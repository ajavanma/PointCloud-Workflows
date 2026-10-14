"""Cross-version checks using outputs produced by the actual pre-rename code."""

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from pointcloud_workflows import ml
from pointcloud_workflows.data_commands import (
    inspect_dataset,
    inspect_prepared_dataset,
    preprocess_dataset,
)
from pointcloud_workflows.datasets import sha256_file


class TestLegacyArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        cls.addClassCleanup(torch.set_num_threads, previous_threads)
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name)
        compatibility = Path(__file__).resolve().parent
        provenance = json.loads((compatibility / "provenance.json").read_text())
        historical_source = os.environ.get("PCW_LEGACY_SOURCE")
        if not historical_source:
            raise RuntimeError(
                "Set PCW_LEGACY_SOURCE to a separate RPTU_AI_Toolkit checkout at "
                + provenance["revision"]
                + "; the compatibility suite does not use PointCloud Workflows history."
            )
        repository = Path(historical_source).expanduser().resolve()

        def git(*arguments):
            result = subprocess.run(
                ["git", "-C", str(repository), *arguments], capture_output=True, check=False,
            )
            if result.returncode:
                raise RuntimeError(
                    "Cannot read the pinned RPTU source from PCW_LEGACY_SOURCE. "
                    + result.stderr.decode(errors="replace")
                )
            return result.stdout

        revision = provenance["revision"]
        package_path = provenance["package_path"]
        if git("rev-parse", "HEAD").decode().strip() != revision:
            raise RuntimeError("PCW_LEGACY_SOURCE must be checked out at the pinned revision")
        tree = git("rev-parse", f"{revision}:{package_path}").decode().strip()
        if tree != provenance["package_tree"]:
            raise RuntimeError("historical package tree differs from the pinned provenance")
        archive = git("archive", "--format=tar", revision, "--", package_path)
        source = cls.root / "historical"
        # Extract regular package files only. Do not apply archive ownership,
        # links, paths outside the package, or executable permissions.
        with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
            for member in contents.getmembers():
                if not member.isfile():
                    continue
                relative = Path(member.name)
                if ".." in relative.parts or not relative.is_relative_to(package_path):
                    raise RuntimeError("unexpected path in historical package archive")
                destination = source / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                with contents.extractfile(member) as stream:
                    destination.write_bytes(stream.read())
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(source / "src")
        environment["OMP_NUM_THREADS"] = "1"
        environment["MKL_NUM_THREADS"] = "1"
        cls.fixtures = cls.root / "legacy-artifacts"
        result = subprocess.run(
            [sys.executable, str(compatibility / "generate_rptu_artifacts.py"),
             str(source / "src"), str(cls.fixtures)],
            cwd=cls.root, env=environment, capture_output=True, text=True, timeout=90,
        )
        if result.returncode:
            raise RuntimeError(f"historical fixture generation failed:\n{result.stdout}\n{result.stderr}")
        cls.prepared = cls.fixtures / "prepared/prepared.json"
        cls.training_report = json.loads((cls.fixtures / "completed/training.json").read_text())

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def file_hashes(self, directory):
        return {
            path.relative_to(directory).as_posix(): sha256_file(path)
            for path in directory.rglob("*") if path.is_file()
        }

    def test_old_raw_and_prepared_datasets_read_and_reprocess_identically(self):
        before = self.file_hashes(self.fixtures)
        self.assertEqual(
            inspect_dataset(self.fixtures / "raw/manifest.json"),
            json.loads((self.fixtures / "raw-report.json").read_text()),
        )
        self.assertEqual(
            inspect_prepared_dataset(self.prepared),
            json.loads((self.fixtures / "prepared-report.json").read_text()),
        )
        regenerated = self.directory / "prepared"
        preprocess_dataset(self.fixtures / "raw/manifest.json", regenerated, 0.5)
        self.assertEqual(self.file_hashes(regenerated), self.file_hashes(self.fixtures / "prepared"))
        self.assertEqual(before, self.file_hashes(self.fixtures))

    def test_old_standalone_bundle_evaluates_and_predicts_identically(self):
        before = self.file_hashes(self.fixtures)
        model = self.fixtures / "inference"
        self.assertEqual({path.name for path in model.iterdir()}, {"bundle.json", "weights.safetensors"})
        evaluation = self.directory / "evaluation"
        prediction = self.directory / "prediction"
        ml.evaluate_model(self.prepared, model, evaluation, device="cpu")
        ml.predict_model(self.prepared, model, prediction, device="cpu")
        self.assertEqual(self.file_hashes(evaluation), self.file_hashes(self.fixtures / "evaluation"))
        self.assertEqual(self.file_hashes(prediction), self.file_hashes(self.fixtures / "prediction"))
        self.assertEqual(before, self.file_hashes(self.fixtures))

    def test_old_completed_run_reuses_report_without_writing(self):
        run = self.directory / "completed"
        shutil.copytree(self.fixtures / "completed", run)
        before = self.file_hashes(run)
        mtimes = {path.relative_to(run): path.stat().st_mtime_ns for path in run.rglob("*")}
        with patch.object(ml, "save_checkpoint", side_effect=AssertionError("must not retrain")):
            result = ml.train_model(self.prepared, run, resume=True)
        self.assertEqual(result, self.training_report)
        self.assertEqual(before, self.file_hashes(run))
        self.assertEqual(mtimes, {path.relative_to(run): path.stat().st_mtime_ns for path in run.rglob("*")})

    def test_old_interrupted_run_resumes_with_identical_adam_history_and_weights(self):
        run = self.directory / "interrupted"
        shutil.copytree(self.fixtures / "interrupted", run)
        immutable_paths = [run / "run.json", *(run / "checkpoints").rglob("*")]
        before = {path: sha256_file(path) for path in immutable_paths if path.is_file()}
        result = ml.train_model(self.prepared, run, resume=True)
        self.assertEqual(result, self.training_report)
        self.assertEqual(sha256_file(run / "weights.safetensors"),
                         sha256_file(self.fixtures / "completed/weights.safetensors"))
        self.assertEqual(before, {path: sha256_file(path) for path in before})
        self.assertTrue((run / "complete.json").is_file())
        self.assertEqual(len(list((run / "attempts").glob("*/attempt.json"))), 2)


if __name__ == "__main__":
    unittest.main()

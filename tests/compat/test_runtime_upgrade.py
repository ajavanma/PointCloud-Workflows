"""Exercise genuine PyTorch 2.10 artifacts with the supported 2.13 runtime.

Run this suite explicitly with PCW_LEGACY_SOURCE and PCW_LEGACY_PYTHON set.
The historical producer runs in its own interpreter; saved metadata is never
rewritten to simulate an older dependency version.
"""

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

from pointcloud_workflows import ml
from pointcloud_workflows.datasets import sha256_file
from pointcloud_workflows.models import MLRuntimeError


class TestRuntimeUpgrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch

        if str(torch.__version__).split("+", 1)[0] != "2.13.0":
            raise RuntimeError("Run the runtime upgrade suite under PyTorch 2.13.0")
        previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        cls.addClassCleanup(torch.set_num_threads, previous_threads)
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name)
        compatibility = Path(__file__).resolve().parent
        provenance = json.loads((compatibility / "provenance.json").read_text())
        historical_source = os.environ.get("PCW_LEGACY_SOURCE")
        historical_python = os.environ.get("PCW_LEGACY_PYTHON")
        if not historical_source or not historical_python:
            raise RuntimeError(
                "Set PCW_LEGACY_SOURCE to the pinned RPTU checkout and "
                "PCW_LEGACY_PYTHON to a PyTorch 2.10.0 interpreter"
            )
        repository = Path(historical_source).expanduser().resolve()
        # Preserve a virtual environment's executable path instead of resolving
        # its symlink to the base interpreter outside that environment.
        python = Path(historical_python).expanduser().absolute()

        def git(*arguments):
            result = subprocess.run(
                ["git", "-C", str(repository), *arguments],
                capture_output=True, check=False,
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
        if git("rev-parse", f"{revision}:{package_path}").decode().strip() != provenance["package_tree"]:
            raise RuntimeError("historical package tree differs from the pinned provenance")
        archive = git("archive", "--format=tar", revision, "--", package_path)
        source = cls.root / "historical"
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
        cls.fixtures = cls.root / "torch-2.10-artifacts"
        result = subprocess.run(
            [str(python), str(compatibility / "generate_rptu_artifacts.py"),
             str(source / "src"), str(cls.fixtures)],
            cwd=cls.root, env=environment, capture_output=True, text=True, timeout=90,
        )
        if result.returncode:
            raise RuntimeError(f"historical fixture generation failed:\n{result.stdout}\n{result.stderr}")
        bundle = json.loads((cls.fixtures / "inference/bundle.json").read_text())
        if bundle["runtime"]["torch_version"].split("+", 1)[0] != "2.10.0":
            raise RuntimeError("PCW_LEGACY_PYTHON did not produce genuine PyTorch 2.10.0 artifacts")
        cls.prepared = cls.fixtures / "prepared/prepared.json"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def file_hashes(self, directory):
        return {
            path.relative_to(directory).as_posix(): sha256_file(path)
            for path in directory.rglob("*") if path.is_file()
        }

    def test_2_10_models_preserve_evaluation_and_point_predictions(self):
        before = self.file_hashes(self.fixtures)
        for source_name in ("inference", "completed"):
            with self.subTest(model=source_name):
                output = self.directory / source_name
                output.mkdir()
                ml.evaluate_model(self.prepared, self.fixtures / source_name,
                                  output / "evaluation", device="cpu")
                ml.predict_model(self.prepared, self.fixtures / source_name,
                                 output / "prediction", device="cpu")
                for name in ("evaluation", "prediction"):
                    self.assertEqual(self.file_hashes(output / name),
                                     self.file_hashes(self.fixtures / name))
        self.assertEqual(before, self.file_hashes(self.fixtures))

    def test_2_10_resume_rejects_new_runtime_without_modifying_run(self):
        for source_name in ("interrupted", "completed"):
            with self.subTest(run=source_name):
                run = self.directory / source_name
                shutil.copytree(self.fixtures / source_name, run)
                before = self.file_hashes(run)
                mtimes = {path.relative_to(run): path.stat().st_mtime_ns
                          for path in run.rglob("*")}
                with self.assertRaisesRegex(MLRuntimeError, r"runtime\.torch_version"):
                    ml.train_model(self.prepared, run, resume=True)
                self.assertEqual(before, self.file_hashes(run))
                self.assertEqual(mtimes, {path.relative_to(run): path.stat().st_mtime_ns
                                          for path in run.rglob("*")})


if __name__ == "__main__":
    unittest.main()

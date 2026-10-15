"""The installed versioned protocol preserves existing payloads and failures."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from pointcloud_workflows import __version__
from pointcloud_workflows.cli import main
from pointcloud_workflows.datasets import DatasetError
from pointcloud_workflows.models import MLRuntimeError
from pointcloud_workflows.runs import TrainingRun


class ProtocolCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="pcw-protocol-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.environment = os.environ.copy()
        self.environment.pop("PYTHONPATH", None)
        self.environment["PYTHONNOUSERSITE"] = "1"

    def run_cli(self, *arguments, guard=False):
        command = [sys.executable, "-m", "pointcloud_workflows"]
        if guard:
            command = [sys.executable, "-c", """
import importlib.abc
import runpy
import sys
class NoML(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'warpconvnet', 'MinkowskiEngine', 'open3d'}:
            raise AssertionError('Unexpected ML import: ' + fullname)
sys.meta_path.insert(0, NoML())
sys.argv = ['pcw', *sys.argv[1:]]
runpy.run_module('pointcloud_workflows', run_name='__main__')
"""]
        return subprocess.run(
            [*command, *map(str, arguments)], cwd=self.directory, env=self.environment,
            capture_output=True, text=True, timeout=30,
        )

    def envelope(self, process, command, *, code=None, status=None):
        self.assertEqual(process.returncode, status if status is not None else (2 if code else 0),
                         process.stdout + process.stderr)
        document = json.loads(process.stdout)
        self.assertEqual(set(document), {"protocol_version", "pcw_version", "command", "ok", "result", "error"})
        self.assertEqual(document["protocol_version"], 1)
        self.assertIs(type(document["protocol_version"]), int)
        self.assertEqual(document["pcw_version"], __version__)
        self.assertEqual(document["command"], command)
        self.assertIs(document["ok"], code is None)
        if code:
            self.assertIsNone(document["result"])
            self.assertEqual(set(document["error"]), {"code", "message"})
            self.assertEqual(document["error"]["code"], code)
            self.assertTrue(document["error"]["message"])
        else:
            self.assertIsNone(document["error"])
            self.assertIsInstance(document["result"], dict)
        return document["result"]

    def call(self, *arguments, **kwargs):
        return self.run_cli("--protocol-version", "1", *arguments, **kwargs)

    def test_doctor_and_config_payloads_match_legacy_json(self):
        config = self.directory / "config.yaml"
        config.write_text("schema_version: 1\npaths: {input_dir: raw, output_dir: output}\n")
        for command, arguments in (("doctor", ("doctor",)),
                                   ("config validate", ("config", "validate", "--config", config))):
            with self.subTest(command=command):
                old = self.run_cli(*arguments, "--json")
                self.assertEqual(old.returncode, 0, old.stderr)
                old_result = json.loads(old.stdout)
                self.assertNotIn("protocol_version", old_result)
                self.assertEqual(self.envelope(self.call(*arguments, guard=True), command), old_result)
                self.assertEqual(self.envelope(self.call(*arguments, "--json"), command), old_result)

    def test_cpu_pipeline_results_preserve_saved_and_legacy_payloads(self):
        generated = self.envelope(self.call("synthetic", "--output", "raw", "--seed", "42"), "synthetic")
        manifest = Path(generated["manifest"])
        self.assertEqual(manifest, self.directory / "raw/manifest.json")
        inspected = self.envelope(self.call("inspect", "--manifest", manifest), "inspect")
        self.assertEqual(inspected, json.loads(self.run_cli("inspect", "--manifest", manifest, "--json").stdout))
        prepared = self.envelope(self.call("preprocess", "--manifest", manifest,
                                           "--output", "prepared", "--voxel-size", "0.25"), "preprocess")
        metadata = self.directory / "prepared/prepared.json"
        self.assertEqual(prepared, json.loads(metadata.read_text()))
        inspected = self.envelope(self.call("inspect", "--prepared", metadata), "inspect")
        self.assertEqual(inspected, json.loads(self.run_cli("inspect", "--prepared", metadata, "--json").stdout))

    def test_parse_errors_are_single_json_responses(self):
        for command, arguments in (
            ("", ()), ("unknown", ("unknown",)), ("synthetic", ("synthetic",)),
            ("synthetic", ("synthetic", "--output", "new", "--seed", "not-an-int")),
            ("config", ("config",)), ("run inspect", ("run", "inspect")),
            ("train", ("train", "--device", "invalid")),
            ("doctor", ("doctor", "--unknown")), ("benchmark", ("benchmark",)),
        ):
            with self.subTest(arguments=arguments):
                self.envelope(self.call(*arguments), command, code="usage_error")
        self.assertFalse((self.directory / "new").exists())

    def test_invalid_protocol_and_help_requests_never_execute(self):
        for arguments in (
            ("--protocol-version", "2"), ("--protocol-version", "01"),
            ("--protocol-version=1", "--protocol-version=1"),
            ("--protocol-version",), ("--protocol-version=1", "--help"),
            ("--protocol-version=1", "--version"),
            ("--protocol-version=1", "-hh"),
        ):
            with self.subTest(arguments=arguments):
                process = self.run_cli(*arguments, "synthetic", "--output", "never")
                self.assertEqual(process.returncode, 2, process.stderr)
                self.assertEqual(json.loads(process.stdout)["error"]["code"], "usage_error")
                self.assertFalse((self.directory / "never").exists())
        misplaced = self.run_cli("synthetic", "--protocol-version", "1", "--output", "never")
        self.envelope(misplaced, "synthetic", code="usage_error")
        self.assertFalse((self.directory / "never").exists())
        self.envelope(self.run_cli("--protocol-version=1", "doctor"), "doctor")
        for arguments in (("doctor", "-hh"), ("config", "validate", "-hh"),
                          ("run", "inspect", "-hh")):
            self.envelope(self.call(*arguments), " ".join(arguments[:-1]), code="usage_error")

    def test_data_errors_preserve_legacy_error_behavior(self):
        for command, arguments in (
            ("inspect", ("inspect", "--manifest", "missing.json")),
            ("config validate", ("config", "validate", "--config", "missing.yaml")),
            ("synthetic", ("synthetic", "--output", "bad", "--seed", "-1")),
            ("run inspect", ("run", "inspect", "--output", "missing")),
        ):
            with self.subTest(command=command):
                self.envelope(self.call(*arguments), command, code="data_error")
                old = self.run_cli(*arguments, "--json")
                self.assertEqual(old.returncode, 2)
                self.assertEqual(old.stdout, "")
                self.assertIn("pcw: error:", old.stderr)

    def test_run_inspection_verifies_artifacts_without_creating_a_lock(self):
        output = self.directory / "model"
        with TrainingRun(output) as run:
            run.bind_spec({"epochs": 2})
            with run.attempt() as attempt:
                staged = run.path / "attempts" / attempt / "model"
                staged.mkdir()
                for name in ("weights.safetensors", "training.json", "bundle.json"):
                    (staged / name).write_bytes(b"test artifact")
                completion = run.publish(staged, {"epochs": 2})
        (output / ".run.lock").unlink()
        before = {p.relative_to(output): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in output.rglob("*") if p.is_file()}
        report = self.envelope(self.call("run", "inspect", "--output", output, guard=True), "run inspect")
        self.assertEqual(report["kind"], "pcw-run-inspection")
        self.assertEqual(report["state"], "completed")
        self.assertEqual(report["completion"], completion)
        self.assertEqual(report["output"], str(output))
        self.assertEqual(report, json.loads(self.run_cli("run", "inspect", "--output", output, "--json").stdout))
        self.assertFalse((output / ".run.lock").exists())
        self.assertEqual(before, {p.relative_to(output): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in output.rglob("*") if p.is_file()})
        (output / "weights.safetensors").write_bytes(b"tampered")
        failed = self.call("run", "inspect", "--output", output)
        self.envelope(failed, "run inspect", code="data_error")
        self.assertIn("checksum mismatch", json.loads(failed.stdout)["error"]["message"])

    def test_unexpected_failures_and_progress_are_isolated_from_stdout(self):
        for exception, code, status in ((OSError("disk error"), "io_error", 2),
                                        (AssertionError("unexpected failure"), "internal_error", 1)):
            stdout, stderr = io.StringIO(), io.StringIO()
            with mock.patch("pointcloud_workflows.cli._doctor", side_effect=exception), \
                    redirect_stdout(stdout), redirect_stderr(stderr):
                actual_status = main(["--protocol-version", "1", "doctor"])
            self.envelope(subprocess.CompletedProcess([], actual_status, stdout.getvalue(), stderr.getvalue()),
                          "doctor", code=code, status=status)

        def noisy_doctor(*args):
            print("third-party progress")
            return {"finite": True}

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("pointcloud_workflows.cli._doctor", side_effect=noisy_doctor), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["--protocol-version", "1", "doctor"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(stdout.getvalue())["result"], {"finite": True})
        self.assertEqual(stderr.getvalue(), "third-party progress\n")

    def test_ml_failures_have_stable_categories(self):
        for exception, code in ((DatasetError("invalid prepared data"), "data_error"),
                                (MLRuntimeError("runtime unavailable"), "runtime_error"),
                                (RuntimeError("device error"), "runtime_error"),
                                (OSError("cannot write output"), "io_error")):
            with self.subTest(code=code, exception=type(exception).__name__):
                stdout, stderr = io.StringIO(), io.StringIO()
                with mock.patch("pointcloud_workflows.ml.train_model", side_effect=exception), \
                        redirect_stdout(stdout), redirect_stderr(stderr):
                    status = main(["--protocol-version", "1", "train", "--prepared", "input.json",
                                   "--output", "run"])
                self.envelope(subprocess.CompletedProcess([], status, stdout.getvalue(), stderr.getvalue()),
                              "train", code=code)

    def test_nonfinite_result_fails_without_a_partial_json_response(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("pointcloud_workflows.cli._doctor", return_value={"value": float("nan")}), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["--protocol-version", "1", "doctor"])
        self.envelope(subprocess.CompletedProcess([], status, stdout.getvalue(), stderr.getvalue()),
                      "doctor", code="internal_error", status=1)


if __name__ == "__main__":
    unittest.main()

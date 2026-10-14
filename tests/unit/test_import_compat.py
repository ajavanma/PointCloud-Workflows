"""Keep historical imports lazy and identical to their canonical modules."""

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest


class ImportCompatibilityTests(unittest.TestCase):
    def run_isolated(self, script, *arguments):
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", textwrap.dedent(script), *arguments],
                cwd=directory, env=environment, capture_output=True, text=True,
                timeout=30, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")

    def test_package_imports_only_load_version_metadata(self):
        self.run_isolated("""\
            import importlib.abc
            import sys

            class NoDependencies(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname.split('.')[0] in {'numpy', 'yaml', 'torch', 'safetensors', 'warpconvnet'}:
                        raise AssertionError('Unexpected dependency import: ' + fullname)

            sys.meta_path.insert(0, NoDependencies())
            import rptu_ai_toolkit
            import pointcloud_workflows
            assert rptu_ai_toolkit.__version__ == pointcloud_workflows.__version__
            assert 'pointcloud_workflows.ml' not in sys.modules
            assert 'rptu_ai_toolkit.ml' not in sys.modules
            """)

    def test_submodules_share_identity_regardless_of_import_order(self):
        script = """\
            import importlib
            import importlib.abc
            import sys
            from unittest.mock import patch

            class NoML(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname.split('.')[0] in {'torch', 'safetensors', 'warpconvnet'}:
                        raise AssertionError('Unexpected ML import: ' + fullname)

            sys.meta_path.insert(0, NoML())
            names = ('_version', 'artifacts', 'checkpoints', 'cli', 'config',
                     'data_commands', 'datasets', 'ml', 'models', 'prepared',
                     'preprocessing', 'runs', 'synthetic')
            prefixes = sys.argv[1:]
            for name in names:
                first = importlib.import_module(prefixes[0] + '.' + name)
                second = importlib.import_module(prefixes[1] + '.' + name)
                assert first is second, name
                assert first.__name__ == 'pointcloud_workflows.' + name

            from rptu_ai_toolkit.datasets import DatasetError as OldError
            from pointcloud_workflows.datasets import DatasetError, load_manifest
            assert OldError is DatasetError
            try:
                load_manifest('missing.json')
            except OldError:
                pass
            else:
                raise AssertionError('Expected a catchable validation failure')

            from pointcloud_workflows import synthetic
            with patch('rptu_ai_toolkit.synthetic.write_npz', side_effect=OSError('test disk failure')):
                try:
                    synthetic.generate_synthetic('raw', 0)
                except DatasetError as error:
                    assert 'test disk failure' in str(error), error
                else:
                    raise AssertionError('Legacy patch did not reach the canonical implementation')
            """
        for prefixes in (
            ("rptu_ai_toolkit", "pointcloud_workflows"),
            ("pointcloud_workflows", "rptu_ai_toolkit"),
        ):
            with self.subTest(import_order=prefixes):
                self.run_isolated(script, *prefixes)


if __name__ == "__main__":
    unittest.main()

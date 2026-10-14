# Tests

Use Python 3.11 or newer, and install the package before running its tests:

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests/unit -v
python -m unittest discover -s tests/cli -v
```

`tests/unit` covers configuration and dataset schemas, NPZ/PLY reading, reversible
label mapping, aligned filtering, voxel aggregation and point mappings, deterministic
synthetic data, and output preservation/cleanup. These tests do not require Open3D, PyTorch, WarpConvNet, a GPU, or the original point-cloud data.

`tests/cli` runs the installed `pcw` command and module entry point, plus the
`rptu` and `python -m rptu_ai_toolkit` compatibility aliases, from temporary
working directories outside the checkout. It checks version/help, diagnostics,
configuration validation, path resolution, and useful errors. The synthetic →
inspect → preprocess workflow verifies output checksums, original point alignment,
label targets, byte reproducibility, and cleanup on failure. An import guard
fails if help, diagnostics, or data commands try to import ML libraries.

CI builds the package and repeats the CLI suite with the wheel installed in a
fresh environment. This catches packaging errors that an editable install can hide.
The clean wheel workflow requires only core dependencies, so PLY remains optional.
The unit test installation includes the `io` extra to exercise the PLY adapter;
PLY-specific tests skip when that extra is absent.

Prepared-data tests cover the generated artifact roundtrip, relocation without
raw inputs, dtype and mapping errors, checksum failures, and the exact voxel-label
majority rule. CLI checks verify that every scene is inspected and malformed
prepared bundles fail with a useful error rather than a traceback.

For the model suite, install `.[ml]` and run:

```sh
python -m unittest discover -s tests/ml -v
```

This suite exercises real CPU training, model bundle save/load, original-point
metrics and predictions, runtime selection, failure paths, and artifact integrity.
Core tests remain separate and do not require ML dependencies. CI also builds a
CPU container and runs the mounted-input/output workflow using
`scripts/container-smoke.sh`. GPU execution is a separate hardware check.

Checkpoint tests compare interrupted-and-resumed CPU training with an uninterrupted
run, including weights and loss history. They exercise optimizer and random-state
recovery, incompatible settings, corruption, and completed retries. Run-output
tests cover process contention, lock release after process death, interrupted
publication, and preservation of completed artifacts.

Cross-version tests live separately in `tests/compat/`. They use a pinned,
external RPTU checkout, not inherited PCW history. The same-runtime suite checks
rename compatibility; a second suite produces artifacts under actual PyTorch
2.10 and exercises them under 2.13. Follow [fixture provenance](compat/README.md)
for explicit environment requirements and commands.

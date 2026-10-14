# Development and tests

Install this checkout and its dependencies before running the unit, CLI, and ML
suites. PointCloud Core currently installs from an immutable, hash-checked source
revision. Additional cross-version suites use a separately pinned RPTU source and
an optional old interpreter. See [fixture provenance](https://github.com/ajavanma/PointCloud-Workflows/blob/main/tests/compat/README.md).

Clone the public [source repository](https://github.com/ajavanma/PointCloud-Workflows) and create
a Python 3.11 or newer virtual environment using the [quickstart](quickstart.md).
Python 3.11 and 3.12 are covered by the CPU test matrix.

## Install and test

From the repository root:

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests/unit -v
python -m unittest discover -s tests/cli -v
```

The test installation includes the optional PLY reader. Unit tests cover strict
configuration and dataset contracts, NPZ/PLY input, class mappings, aligned finite
row filtering, voxel aggregation, deterministic synthetic scenes, and preservation
or cleanup of outputs. Prepared-reader tests check strict metadata, exact array
dtypes and shapes, counts, voxel ordering, point mappings, and label aggregation.
They also exercise corruption, bundle relocation, and labeled/unlabeled scenes.

Core compatibility tests cover the adapter's array and label contracts, numerical
edge cases, original-row lifting, and established PCW validation errors. PCW's
feature means retain their divide-before-sum reduction; direct Core callers use
its scaled mean. See the [integration boundary](../core-integration.md).

CLI tests run the installed command and module entry point from temporary working
directories outside the checkout. They exercise the generate, inspect, and
preprocess sequence followed by prepared-bundle inspection, checksums, original
point alignment, useful failures, and reproducibility. Prepared inspection is also
tested after moving the bundle and removing its raw source directory. Import
guards catch accidental ML dependency imports.

## Locked development environment

If uv is installed:

```sh
uv sync --locked --extra io
uv run --locked --extra io python -m unittest discover -s tests/unit -v
uv run --locked --extra io python -m unittest discover -s tests/cli -v
```

The lockfile includes the optional ML dependencies. To exercise the CPU model:

```sh
uv sync --locked --extra io --extra ml
uv run --locked --extra io --extra ml python -m unittest discover -s tests/ml -v
```

Alternatively install `.[ml]` with pip and run the same `tests/ml` discovery.
The separate `requirements/gpu-cu128.txt` pins the WarpConvNet CUDA wheel and
matching PyTorch build. Keep it separate from the portable CPU dependency set.

## Build and CI

```sh
python -m pip install 'build>=1.2,<2'
python -m build
```

The CPU CI workflow runs the unit and CLI suites, builds a source distribution
and wheel, and repeats the CLI tests with the wheel installed in a separate
environment outside the checkout. The clean wheel check installs core dependencies
only, keeping PLY optional. Current run results are available in
[GitHub Actions](https://github.com/ajavanma/PointCloud-Workflows/actions/workflows/tests.yml).

The installed PCW wheel also runs the Core compatibility tests. A separate clean
environment installs only Core and NumPy and runs
[`examples/core_roundtrip.py`](https://github.com/ajavanma/PointCloud-Workflows/blob/main/examples/core_roundtrip.py)
outside the checkout on Python 3.11 and 3.12. This checks that the array example
does not rely on PCW, its CLI, file formats, or ML dependencies. Follow the
[standalone instructions](../core-integration.md#standalone-array-example) to run it locally.

The CPU model suite runs real training, safetensors save/load, point-level
metrics, and prediction. It exercises corruption and contract-mismatch failures,
ignored and removed rows, deterministic behavior, and output preservation.
A separate CI job builds the CPU container and runs the CLI through mounted
storage. GPU kernels and cluster execution are separate execution environments.

Report defects through [GitHub issues](https://github.com/ajavanma/PointCloud-Workflows/issues),
including the command, toolkit version, Python version, and a small reproducible
input where possible.

Checkpoint tests compare interrupted-and-resumed CPU training with an uninterrupted
run, including weights and loss history. They exercise optimizer and random-state
recovery, incompatible settings, corruption, and completed retries. Run-output
tests cover process contention, lock release after process death, interrupted
publication, and preservation of completed artifacts.

# PointCloud Core integration

PCW uses [PointCloud Core](https://github.com/ajavanma/pointcloud-core) for
in-memory point-cloud operations. Core depends only on NumPy and can be used
without the workflow application.

| Layer | Responsibilities |
| --- | --- |
| PointCloud Core | Aligned-array validation, reversible class encoding, voxel grouping and labels, safe lifting from voxels to source rows |
| PCW compatibility adapter | Preserve PCW validation errors, array contracts, and the existing feature-mean reduction |
| PCW workflow | Dataset manifests and file readers, prepared artifacts, CLI, models, checkpoints, run outputs, and containers |

No artifact migration is required. Dataset, model, checkpoint, and run schemas
retain their existing versions and `rptu-*` identifiers. Existing resume checks
still enforce the saved runtime and prepared-data contract.

## Dependency and release status

The current dependency uses the immutable Core `0.1.0` source revision
[`5c28a700c30aee6186cfe30f6cd74708289f0743`](https://github.com/ajavanma/pointcloud-core/commit/5c28a700c30aee6186cfe30f6cd74708289f0743).
Core's first release is prepared but is not yet on PyPI. Installing PCW from this
checkout fetches that revision automatically; it does not follow Core's `main`
branch. The archive is verified against SHA-256
`060ee954fabda420d57bc22138f6c62d5946f11e7f076c1e69c863139c52c355`.
The base environment contains PyYAML, NumPy, and PointCloud Core.

This source pin is transitional. After Core is published, replace it with a
tested package-index version and regenerate the lockfile. Complete that change
before publishing PCW to PyPI. Updating Core requires running the PCW parity,
artifact, and model compatibility suites, not only checking that imports work.
The package release workflow rejects direct URL dependencies before publication.

## Compatibility boundary

PCW retains its existing error types and messages at its public validation
boundaries. Its manifests still require features and enforce split, path,
checksum, and label rules that the general-purpose Core array API does not own.
Class declaration order, ignored labels, negative-coordinate floor quantization,
voxel ordering, original IDs, and removed-row markers remain unchanged.

The feature-mean implementations have different floating-point reduction orders.
Core scales values by their voxel's maximum absolute value before averaging.
PCW retains its existing divide-each-contribution-before-summing reduction in a
small compatibility adapter. This preserves established PCW prepared features;
it does not change existing artifacts to Core's numerics. Direct Core callers
use Core's documented scaled mean, including its handling of subnormal values.
Neither API promises bitwise equality across arbitrary NumPy/runtime versions.

Compatibility tests cover numerical edge cases, class and point alignment,
error behavior, and existing artifact readers. The standalone example is also
run with an installed package from outside the checkout. See
[development](gitbook/development.md) and the
[test suites](https://github.com/ajavanma/PointCloud-Workflows/blob/main/tests/README.md).

## Standalone array example

[`examples/core_roundtrip.py`](https://github.com/ajavanma/PointCloud-Workflows/blob/main/examples/core_roundtrip.py)
imports only Core, NumPy, and the Python standard library. It creates seven
synthetic points in memory, validates and encodes labels, aggregates three voxels,
and maps example predictions back to all seven original rows. It needs no PCW
imports, manifest, file reader, model, or GPU, and writes no files.

From the PCW checkout, create a separate environment containing only Core and its
NumPy dependency, then run the example from another directory:

```sh
python3 -m venv /tmp/core-example-venv
/tmp/core-example-venv/bin/python -m pip install \
  'pointcloud-core @ https://github.com/ajavanma/pointcloud-core/archive/5c28a700c30aee6186cfe30f6cd74708289f0743.tar.gz#sha256=060ee954fabda420d57bc22138f6c62d5946f11e7f076c1e69c863139c52c355'
cp examples/core_roundtrip.py /tmp/core_roundtrip.py
cd /tmp
/tmp/core-example-venv/bin/python core_roundtrip.py
```

The output includes:

```json
{
  "input_points": 7,
  "retained_points": 5,
  "voxels": 3,
  "point_to_voxel": [0, 0, 1, 1, 2, -1, -1],
  "point_ids": [100, 8, 901, 42, 5000, 77, 1234],
  "predicted_labels": [42, 42, 7, 7, 7, 255, 255]
}
```

One row has an invalid coordinate and another has an invalid feature. Both keep
their row and external ID, with the ignore label `255` after lifting. The first
voxel has a label tie resolved by declared class order; the third contains only
ignored training labels but can still receive a prediction. Prediction lifting
restores row alignment, not information lost during aggregation.

For independent applications, use the documented top-level imports and contracts
in the [Core API reference](https://github.com/ajavanma/pointcloud-core/blob/5c28a700c30aee6186cfe30f6cd74708289f0743/docs/api.md).

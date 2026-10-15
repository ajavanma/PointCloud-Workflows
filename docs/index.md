# PointCloud Workflows

Prepare point-cloud datasets, validate their contracts, and run reproducible
segmentation workflows with a portable CPU model and an optional GPU backend.

Start with the [quickstart](gitbook/quickstart.md), explore the
[commands](gitbook/cli-reference.md), or read the
[dataset specification](datasets.md). The [overview](gitbook/README.md)
describes the supported workflow and model choices.

For maintainers, the [release guide](releasing.md) records the package and
documentation destinations and the checks required before publishing.

PointCloud Workflows and the separate NumPy-only
[PointCloud Core library](https://github.com/ajavanma/pointcloud-core) have public
source repositories. PCW uses Core for array validation, voxelization, and
original-point mappings through a compatibility adapter. The current dependency
pins the prepared Core `0.1.0` source; PyPI publication remains a separate step.
See [Core integration and the standalone example](core-integration.md).

Programs can use the opt-in [JSON execution protocol](protocol.md) for structured
command results and errors, including read-only training-run inspection.

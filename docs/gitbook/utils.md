# Utilities

Use `pcw doctor` for dependency metadata and `pcw COMMAND --help` for command
arguments. Diagnostics and data commands remain usable without loading PyTorch
or WarpConvNet.

`pcw config validate --config PATH` checks application YAML. Dataset and model
commands take explicit arguments; see [configuration](configuration.md) and the
[CLI reference](cli-reference.md).

The Python data API exposes `load_prepared_manifest` and `load_prepared_scene`
from `pointcloud_workflows.prepared`. They return validated metadata and numeric arrays,
independent of the model backend. See the [dataset contract](dataset-contract.md).

For operations on arrays without PCW file formats, use the separate
`pointcloud_core` API. The [integration guide](../core-integration.md) explains
validation, reversible labels, voxelization, and original-row lifting through a
standalone synthetic example.

The model API in `pointcloud_workflows.ml` exposes `train_model`, `evaluate_model`, and
`predict_model`, with the same prepared inputs and new-output-directory rules as
the CLI. ML dependencies load only when a model command executes. `train_model(...,
resume=True)` resumes the same output run. Omitted training options reuse the
recorded values; explicit changes are rejected. Completed retries return the
verified saved report.

Use the repository's
[container guide](https://github.com/ajavanma/PointCloud-Workflows/blob/main/docs/containers.md)
for CPU and NVIDIA execution through Docker. Input datasets are mounted read-only;
outputs and runtime caches use explicit writable mounts.

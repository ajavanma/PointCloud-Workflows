# Roadmap

## Available workflow

- Installable package and CLI with optional ML and PLY dependencies.
- Versioned dataset contracts, reversible class mappings, and preserved point IDs.
- Seeded synthetic scenes, CPU voxel preprocessing, and prepared-bundle inspection.
- WarpConvNet MinkUNet18 for NVIDIA GPUs and a portable PyTorch CPU fallback.
- Training, original-point evaluation, and prediction in original dataset class IDs.
- Model bundles with safetensors weights, normalization, metadata, and checksums.
- Epoch checkpoints with Adam and random state, explicit resume, durable attempt
  records, and verified completed retries.
- Separate CPU and GPU container targets with explicit input, output, and cache mounts.
- The `pointcloud-workflows` distribution, `pointcloud_workflows` imports, and
  `pcw` CLI, with old command/import aliases and preserved artifact formats.
- PointCloud Core integration with compatibility tests and a standalone array
  example, using an immutable source revision until Core's first PyPI release.
- Versioned JSON command results/errors and read-only training-run inspection
  for programmatic execution. See the [protocol](../protocol.md).

Use the [GPU and CPU quickstart](quickstart.md) for a complete run.

## Next stages

The `pcw-go` companion is being developed privately around this protocol. The
first runner executes local PCW processes with typed requests, bounded output,
cancellation, and explicit training resume. Python retains array processing and
model execution. Automatic retries, remote artifact ownership, and container or
Kubernetes runners need separate execution contracts.

1. Complete the first `0.1.0` release of the separate NumPy-only
   [PointCloud Core library](https://github.com/ajavanma/pointcloud-core). Its
   source and release preparation are public; PyPI publication remains a separate
   release step.
2. Replace the transitional Core source dependency with its published package
   version, rerun compatibility tests, and retain existing artifact contracts.
   Add a public-data recipe and spatial chunking for larger scenes.
3. Prepare versioned package and image releases with schema compatibility guidance.
4. Package explicit batch runs as Helm Jobs with preserved dataset and result storage.
5. Add optional Rancher Fleet examples for existing cluster operators.
6. Add repeatable GPU performance benchmarks with fixed inputs and model bundles.

Both source repositories are public. PCW remains `0.2.0.dev0`; package, image, and
documentation publication remain separate release steps. The
[public-release record](../public-readiness.md) describes repository protections;
the [public RPTU guide](https://rptu.gitbook.io/rptu-ai-toolkit/)
continues to describe the shared baseline. See [project lineage](../project-lineage.md)
and [publication status](../gitbook-publication.md).

Training currently resumes at completed epoch boundaries using the original run
settings. Step-level checkpoints, changing settings while resuming, scheduler
state, and distributed storage coordination remain separate future extensions.

Helm and Fleet will package the same CLI. Configuration reconciliation must not
silently launch training runs. A GPU host, cluster provisioner, or experiment server
is not a required dependency of the local package.

BIM export, multi-GPU training, and additional source formats remain follow-up
work. Research history remains in the original RPTU repository.

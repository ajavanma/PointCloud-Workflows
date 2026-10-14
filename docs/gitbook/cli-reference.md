# CLI reference

The installed command is `pcw`. `python -m pointcloud_workflows` provides the same
interface. The obsolete `src/main.py` research wrapper has been removed; use
one of the installed commands or module entry points.

| Command | Behavior |
| --- | --- |
| `pcw --help` | Show commands and availability. |
| `pcw --version` | Show the installed toolkit version. |
| `pcw doctor [--json]` | Report Python, platform, installed package metadata, and capabilities. |
| `pcw config validate --config PATH [--json]` | Validate application YAML and show resolved configuration. |
| `pcw synthetic --output DIR [--seed N] [--json]` | Generate four small seeded scenes and their manifest. |
| `pcw inspect --manifest PATH [--json]` | Validate the raw dataset manifest, checksums, scene arrays, and labels. |
| `pcw inspect --prepared PATH [--json]` | Validate prepared metadata, every scene archive, and point/voxel consistency. |
| `pcw preprocess --manifest PATH --output DIR --voxel-size SIZE [--json]` | Filter invalid rows and voxelize the dataset on the CPU. |
| `pcw train --prepared PATH --output DIR [--resume]` | Start or resume WarpConvNet or PyTorch training. |
| `pcw evaluate --prepared PATH --model DIR --output DIR` | Report original-point metrics for the selected split. |
| `pcw predict --prepared PATH --model DIR --output DIR` | Export original dataset labels and point identities. |
| `pcw benchmark` | Reserved for the benchmark workflow. |

Run `pcw COMMAND --help` for a command's arguments.

`rptu` and `python -m rptu_ai_toolkit` remain compatibility entry points to the
same implementation. Help and diagnostics use PointCloud Workflows branding.
Saved artifact identifiers and schema versions are unchanged; see the
[migration guide](../migration.md).

## Diagnostics and configuration

`doctor` reads distribution metadata without importing ML libraries. It lists the
installed dependencies and available commands. Device selection happens when an
ML command starts, so diagnostics remain usable in a base installation.

`config validate` checks structure and path rules without requiring a dataset,
creating directories, or initializing a GPU. Dataset and ML commands use explicit CLI
arguments and a separate JSON manifest; they currently do not read application
YAML. See [configuration](configuration.md).

## Dataset commands

`synthetic` defaults to seed `0`. A seed must be an integer between `0` and
`4294967295`. Its output directory must not already exist.

`inspect --manifest` checks every raw scene's SHA-256 before parsing it and reports point counts,
nonfinite rows, and class statistics. A manifest can contain unusable rows when a
scene also contains usable points; preprocessing removes those rows consistently
from aligned data. Inspection never silently repairs unknown class IDs or
malformed arrays.

`inspect --prepared` validates a complete prepared bundle without reopening raw
files. It checks metadata, output checksums, exact array dtypes and shapes, sorted
voxel coordinates, point IDs, mapping bounds and coverage, counts, label ranges,
and majority/tie label aggregation. The raw `--manifest` and prepared `--prepared`
options are mutually exclusive. Neither command prints a successful report until
every listed scene has passed validation.

Prepared reports use `kind: "rptu-prepared-dataset"` and include per-scene and total
input, retained, removed, and voxel counts. Point and voxel label count maps use
training IDs; point-label counts include removed rows. Raw reports use
`kind: "rptu-raw-dataset"`, with label counts in original dataset IDs. Recorded
source hashes identify the claimed source bytes; prepared inspection does not
verify publisher identity or recompute voxel coordinates and feature means from
absent raw arrays.

`preprocess` requires a finite positive voxel size in the manifest's coordinate
unit and a new output directory. It preserves original point correspondence and
writes completion metadata last. On failure, it removes the output directory it
created. It does not train a model or reconstruct predictions.

The [dataset contract](dataset-contract.md) defines split rules, class mappings,
feature reductions, numeric limits, and the prepared output format. For a prepared
bundle, pass its `prepared.json` to `inspect --prepared`.

## Model commands

Training accepts `--backend auto|warpconvnet|torch`, `--device auto|cpu|cuda`,
`--epochs` (20), `--learning-rate` (0.001), and `--seed` (0). Automatic selection
uses WarpConvNet/CUDA when available and the PyTorch/CPU fallback otherwise.

Evaluation and prediction take `--model DIR` and use its saved architecture.
Their default splits are `test` and `predict`, respectively; `--split` accepts
`train`, `val`, `test`, or `predict`. Evaluation requires at least one valid,
nonignored labeled point; unlabeled scenes contribute no scored points.

All three commands accept `--max-voxels` (100000 per scene), `--device`, and
`--json`. Outputs require new directories, except `train --resume`, which opens
an existing training run. Resume restores omitted options from that run; explicit
options must match. `--epochs` is the original total, not an additional count.
Completed retries return the saved report after verifying its artifacts. A busy
run, changed dataset, incompatible runtime, or corrupt checkpoint fails clearly. Errors do not silently overwrite prior
models, trim scenes, or switch a saved model's architecture. See [training](train.md)
and [test and evaluation](test.md).

## Exit status and JSON

Successful commands and help return status `0`. Argument errors, configuration or
dataset errors, and unimplemented commands return status `2`, with errors on
stderr. A command's `--json` option emits JSON on stdout on success.

Model quality is measured by evaluation on representative held-out data.

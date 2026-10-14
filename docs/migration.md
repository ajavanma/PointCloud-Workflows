# Moving to PointCloud Workflows

| Surface | Preferred name | Supported compatibility name |
| --- | --- | --- |
| Distribution | `pointcloud-workflows` | No old-distribution redirect |
| Python package | `pointcloud_workflows` | `rptu_ai_toolkit` |
| Command | `pcw` | `rptu` |
| Module command | `python -m pointcloud_workflows` | `python -m rptu_ai_toolkit` |
| Locally built images | `pointcloud-workflows:cpu`, `pointcloud-workflows:gpu` | Old images keep their original contents |

This applies to the independent PointCloud Workflows repository. The original
RPTU repository and its public guide continue to describe the RPTU baseline.

## Install without overlapping distributions

Use a fresh environment from a PointCloud Workflows checkout:

```sh
python3.11 -m venv .venv-pcw
source .venv-pcw/bin/activate
python -m pip install .
pcw doctor --json
python -m pointcloud_workflows --help
```

Use `.[io]` for PLY and `.[ml]` for the default CPU training runtime. For CUDA,
install `requirements/gpu-cu128.txt` followed by the base package (`pip install .`);
do not install the `ml` extra over that GPU profile. Follow the
[quickstart](gitbook/quickstart.md) for the separate CPU and GPU commands.
Source installation does not require a public package registry.

Do not install `rptu-ai-toolkit` and `pointcloud-workflows` together. They both own
the `rptu_ai_toolkit` compatibility files and `rptu` command; uninstalling either
can remove files used by the other. Keep the previous environment available for
older runs. If reusing an environment, uninstall the old distribution first,
then install the successor and run `python -m pip check`.

No `pointcloud-workflows` release has been published to PyPI. The old distribution
name is not a redirect and is not republished by this migration.

## Imports and scripts

Prefer canonical imports in new code:

```python
from pointcloud_workflows.prepared import load_prepared_manifest, load_prepared_scene
```

Old `rptu_ai_toolkit` submodule imports resolve to the same implementation modules
and classes. Exceptions, module state, and monkeypatches are shared. Importing the
base package or running help, diagnostics, and dataset commands does not import
PyTorch or WarpConvNet. The `rptu` alias accepts the same arguments as `pcw`; help
and errors use the new branding. The obsolete `python src/main.py` wrapper has
been removed; use the installed command or module entry point.

These aliases are supported throughout the `0.2` prerelease line. There is no
scheduled removal; a later removal requires a documented release change. Update
new scripts to `pcw` now without changing old artifact files.

## Datasets, models, and resumed runs

Raw and prepared datasets, model bundles, evaluation and prediction exports,
training specifications, checkpoints, attempt records, and completion markers
keep their existing schema versions and `rptu-*` kind strings. New outputs also
use these format identifiers. They describe the file format, not the product name.
No conversion step is required. Do not search-and-replace strings inside bundles:
saved metadata and weights are protected by checksums.

The [PointCloud Core integration](core-integration.md) preserves these schemas,
PCW validation errors, and the established feature-mean reduction. Installation
now fetches an immutable, hash-checked Core `0.1.0` source revision while its PyPI
release is prepared. This does not relax runtime checks for resumed training.

The package is currently `0.2.0.dev0`. The default CPU ML runtime is now PyTorch
2.13.0; the separate GPU binary profile still uses 2.10.0. Existing resume
checks still require the saved toolkit, PyTorch, CUDA and WarpConvNet versions,
device, training settings, and prepared data. Retain the original dependency
versions when moving an interrupted run to the successor. In a dedicated old-run
environment, install its recorded dependencies and the base package (`pip install .`)
instead of the newer `ml` extra. A PyTorch 2.10 checkpoint cannot resume under
2.13; changing metadata to bypass that check is unsupported:

```sh
pcw inspect --prepared runs/demo-prepared/prepared.json
pcw train --prepared runs/demo-prepared/prepared.json --output runs/demo-model --resume
```

A completed retry verifies its saved outputs and returns the original report
without rewriting artifacts. An interrupted run continues from its last complete
epoch. Inference still selects the architecture recorded in the bundle; renaming
does not convert WarpConvNet weights into the CPU fallback architecture.

Compatibility tests generate synthetic artifacts using the immutable pre-rename
public RPTU revision `73319745a0aacb410401df71ec890a1cecc00cf8` in an external temporary checkout, then load, evaluate, predict,
and resume with the new package. This covers the modern RPTU artifact contracts;
it does not introduce a loader for unversioned research-era pickle checkpoints.

The fresh project history removes old source and repository metadata, not the
artifact compatibility readers. See [lineage](project-lineage.md) and the
[runtime advisory review](runtime-advisories.md) for the separate runtime change.

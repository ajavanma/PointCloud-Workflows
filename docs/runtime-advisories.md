# Runtime advisory review

Reviewed on 2026-10-14. PointCloud Workflows keeps data preparation independent
of PyTorch. Model workflows have separate dependency profiles:

| Profile | PyTorch | Sparse backend | Advisory status |
| --- | --- | --- | --- |
| `.[ml]` and CPU container | `2.13.0` | None; built-in voxel MLP | Contains the upstream fix for GHSA-rrmf-rvhw-rf47 |
| `requirements/gpu-cu128.txt` and GPU container | `2.10.0+cu128` | WarpConvNet `1.8.2+torch2.10cu128` | Retains affected PyTorch; sparse runtime upgrade remains open |

The GPU requirements provide both PyTorch and safetensors. Install the base
PCW package after them (`python -m pip install .`), without the `ml` extra;
the two profiles deliberately select different PyTorch versions.

## TorchScript annotation crash

[GHSA-rrmf-rvhw-rf47 / CVE-2025-3000](https://github.com/advisories/GHSA-rrmf-rvhw-rf47)
lists PyTorch versions through `2.12.1` as affected and `2.13.0` as the first
patched version. GitHub rates it low severity with a local attack vector.
The [upstream report](https://github.com/pytorch/pytorch/issues/149623) involves
compiling a scripted class containing a bare `list` annotation. The
[fix](https://github.com/pytorch/pytorch/commit/b90c949) rejects unsupported bare
container annotations instead of reaching the crashing compiler path.

PCW does not invoke `torch.jit` or accept TorchScript programs as model inputs.
Its built-in model definitions receive numeric weights from safetensors.
That source inspection bounds exposure through the supported PCW interfaces;
it does not certify every use of the installed dependency.

## Exported-program loading

PyPI's PyTorch `2.10.0` metadata also lists
[PYSEC-2026-139 / CVE-2026-4538](https://github.com/pypa/advisory-database/blob/main/vulns/torch/PYSEC-2026-139.yaml).
This record describes a high-severity local deserialization issue when loading
an untrusted `.pt2` exported program. Its affected range ends at `2.10.0`, but
it does not identify a fixed release. Its referenced
[PyTorch pull request](https://github.com/pytorch/pytorch/pull/176791) was closed
without merging, so its proposed change is not evidence of a released fix.

PCW uses neither `torch.export.load` nor `torch.load` and does not accept `.pt2`
archives. NPZ readers set `allow_pickle=False`; model and optimizer tensors use
safetensors. The review found no entry point for this loader through PCW's
documented artifact formats. PyPI currently lists no vulnerabilities for
`2.13.0`; this observation alone is not proof of a fix for this separate issue.

## Compatibility across the runtime upgrade

The package remains `0.2.0.dev0`. Dataset schemas, numeric model bundles, and
the old package and command aliases are unchanged. The runtime upgrade tests
generate synthetic models using the pinned pre-rename source in a separate
PyTorch `2.10.0` interpreter. They then exercise evaluation and prediction with
the current `2.13.0` interpreter, comparing the resulting reports and point
predictions without rewriting the original model metadata.

Training resume is stricter than model inference. It compares the saved
PyTorch version, toolkit version, CUDA/WarpConvNet versions, device, and other
training settings. A run created under `2.10.0` is rejected under `2.13.0`
before any attempt or checkpoint is written. This also applies to a completed
run submitted again through `train --resume`. Use its original isolated
runtime to resume it, or load its completed model for inference. Do not edit
the saved version fields to bypass this contract.

## Remaining sparse GPU upgrade

The official [PyTorch install matrix](https://pytorch.org/get-started/previous-versions/#v2130)
and [wheel index](https://download.pytorch.org/whl/cpu/torch/) provide `2.13.0`
CPU wheels for the supported Python 3.11/3.12 platforms. CUDA `2.13.0` wheels
exist for CUDA 12.6 and 13.0, but not the current CUDA 12.8 profile.

[WarpConvNet 1.8.2](https://github.com/NVlabs/WarpConvNet/releases/tag/v1.8.2)
does not currently publish a PyTorch `2.13` wheel. Installing its `torch2.10`
binary alongside `2.13` would combine incompatible extension builds. Keep
the existing profile until a matching upstream wheel is available, or build
WarpConvNet against the selected newer PyTorch and CUDA toolkit.

The source-build candidate is WarpConvNet `1.8.2` at commit
`e3ab140bea3567b930c2e1f1aa85c4299dd088b8` with PyTorch `2.13.0+cu126`.
The [upstream build instructions](https://github.com/NVlabs/WarpConvNet/blob/v1.8.2/README.md#installation)
require a matching CUDA compiler, the CUTLASS submodule, and build dependencies.
An explicit `TORCH_CUDA_ARCH_LIST=8.9` targets the RTX 4070 when building without
a visible GPU. Completing that change requires a successful extension build
and model compatibility checks; no matching binary is supplied by this change.

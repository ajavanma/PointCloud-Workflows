# Security policy

PointCloud Workflows is in development. Security fixes target the current
`main` branch. This repository does not ship the original research source or
its historical dependency environments.

## Reporting a vulnerability

Use **Security → Report a vulnerability** on the
[repository security page](https://github.com/ajavanma/PointCloud-Workflows/security/advisories/new)
to send a private report to the maintainer. Include the affected revision,
the smallest synthetic reproducer, expected and actual behavior, and the impact.
Do not include access tokens, personal data, or a private research dataset.

If GitHub's private reporting form is unavailable, open an issue titled
**Security contact request** containing only a request for a private reporting
channel. Do not put the vulnerability or proof of concept in that issue.

## Runtime boundaries

Dataset and model readers validate their documented contracts. Numeric arrays
are loaded without pickle, and supported weights and checkpoints use
safetensors with JSON metadata. File hashes detect changes relative to recorded
metadata; they do not authenticate an unknown artifact publisher.

Run unfamiliar inputs in an isolated environment with appropriate memory, disk,
and execution limits. Do not treat Python package installation, legacy research
scripts, or arbitrary dataset conversion code as a sandbox. The supported CLI
and artifact contracts are described in the [documentation](docs/gitbook/README.md).

Training run ownership uses local POSIX process locks. Shared network storage
does not turn those locks into a distributed coordination service.

## Known dependency follow-up

The default `ml` extra and CPU container use PyTorch `2.13.0`, the first patched
release for [GHSA-rrmf-rvhw-rf47](https://github.com/advisories/GHSA-rrmf-rvhw-rf47).
The separate WarpConvNet GPU profile retains PyTorch `2.10.0+cu128` because its
compiled extension requires that PyTorch/CUDA combination. That profile remains
affected by the dependency advisory; a CPU upgrade does not resolve its alert.

The reviewed issue concerns `torch.jit.script`. PyPI also reports
[PYSEC-2026-139](https://github.com/pypa/advisory-database/blob/main/vulns/torch/PYSEC-2026-139.yaml)
for PyTorch `2.10.0`, concerning untrusted `.pt2` loading through
`torch.export.load`. PCW does not call these interfaces or `torch.load`; its
supported model readers use safetensors. This limits the affected entry points
in PCW, but does not make arbitrary use of an affected PyTorch runtime safe.

See the [runtime advisory review](docs/runtime-advisories.md) for affected
profiles, evidence, and the sparse GPU upgrade path. No dependency alert is
dismissed by this review. Do not alter saved run metadata or bypass runtime
checks to resume a run under another PyTorch version.

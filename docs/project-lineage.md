# Project origin and clean history

PointCloud Workflows derives from the modernized
[RPTU AI Toolkit](https://github.com/ajavanma/RPTU_AI_Toolkit). The original MIT
copyright and license notice remain in [LICENSE](https://github.com/ajavanma/PointCloud-Workflows/blob/main/LICENSE).
The owner confirmed reuse of the four research illustrations on 2026-10-14;
they remain labelled as historical illustrations, not current benchmark outputs.

The successor now starts with a clean Git history containing only maintained
package code, tests, documentation, and the approved pictures. Research scripts,
old configuration formats, helper modules, generated logs, research branches,
tags, and their commit metadata are not copied into this repository. The original
RPTU repository remains the historical archive. A private rollback archive of the
previous successor is separate from this project and is not a release source.

The source cleanup does not rewrite user datasets or model files. `rptu` and
`rptu_ai_toolkit` remain compatibility aliases, and on-disk formats retain their
existing schema versions and `rptu-*` identifiers. See [migration](migration.md).

Cross-version tests fetch a separately pinned public RPTU revision,
`73319745a0aacb410401df71ec890a1cecc00cf8`, only into a temporary test checkout.
They verify its package tree before generating synthetic fixtures. Neither that
source nor the generated fixtures are shipped in PCW. See
[compatibility tests](https://github.com/ajavanma/PointCloud-Workflows/blob/main/tests/compat/README.md).

[PointCloud Core](https://github.com/ajavanma/pointcloud-core) is a separate,
NumPy-only library for point-cloud validation, deterministic voxelization, label
mapping, and reconstructing original-point outputs. PCW retains file formats,
dataset contracts, training, CLI, containers, and runtime orchestration. A
versioned library integration will follow its first tested release.

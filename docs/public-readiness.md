# Public release preparation

Prepared on 2026-10-14. This repository remains private; package, image, and site
publication are separate release actions.

## Source and history

The maintained project starts with fresh Git history and GitHub records. Old
research branches, tags, commits, generated logs, helper scripts, and obsolete
dependency snapshots are not imported. The original RPTU repository remains the
historical archive. A private rollback archive is separate from the new PCW
project, rather than retaining hidden pull-request refs in the release repository.

The MIT license and attribution remain. Arash confirmed reuse of the four research
pictures; they are kept as labelled illustrations. New commits use the verified
GitHub noreply identity. No historical personal email, home directory, desktop
metadata, research data, or model weights are intentionally carried into the clean
history. Repeat a scoped secret/content scan on the selected release revision.
See [lineage](project-lineage.md) and the [changelog](https://github.com/ajavanma/PointCloud-Workflows/blob/main/CHANGELOG.md).

## Runtime review

The default CPU ML extra and CPU container use PyTorch 2.13.0, which includes the
upstream fix for GHSA-rrmf-rvhw-rf47. The GPU binary profile remains paired with
PyTorch 2.10.0+cu128 and WarpConvNet 1.8.2 because upstream has no matching patched
binary. Its advisory remains open. The separate exported-program advisory is
reviewed without claiming a fix based only on an empty package-index alert list.
See the [runtime advisory review](runtime-advisories.md) for evidence and the next
sparse-GPU upgrade step.

Compatibility tests distinguish inference from training resume: completed 2.10
model bundles remain inference inputs, while a 2.10 training run requires its
recorded runtime. Do not rewrite checkpoint metadata to bypass this rule.

## GitHub controls

- Read-only workflow token; no workflow PR-review approval capability.
- Immutable action commit pins and GitHub-hosted runners for untrusted changes.
- Squash merges, automatic merged-branch cleanup, no merge/rebase merge methods.
- Dependency alerts enabled; vulnerability fixes are reviewed through PRs.
- CODEOWNERS routes review to the maintainer; it does not enforce protection alone.
- Prepared `main` protection requires PRs, current passing checks, linear history,
  resolved conversations, and blocks force pushes/deletions, including admins.
  The solo-maintainer policy requires no second approval; CI is still mandatory.
- Enable secret scanning/push protection, private vulnerability reporting, outside
  contributor workflow approval, and Python CodeQL when repository eligibility
  permits. Verify controls after activation instead of assuming files enable them.

The current account's private-repository plan does not support enforced branch
protection or Pages. A plan upgrade or an explicitly requested public visibility
change is needed for those controls. This preparation does not change visibility
or buy an account plan. GitHub documents the
[branch protection eligibility](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
and [Pages eligibility](https://docs.github.com/en/pages/quickstart).

## Destinations and release boundary

| Artifact | Selected destination | Current state |
| --- | --- | --- |
| Python package | PyPI `pointcloud-workflows` | Prepared, not published; configure Trusted Publisher |
| Documentation | GitHub Pages `https://ajavanma.github.io/PointCloud-Workflows/` | Prepared, not deployed |
| Future container images | `ghcr.io/ajavanma/pointcloud-workflows` | Selected; no image publishing workflow yet |
| Numerical library | Separate `ajavanma/pointcloud-core`, PyPI `pointcloud-core` | Separate private project; no public-index dependency in PCW yet |

Use [release instructions](releasing.md) and the manual workflows. PyPI releases
use short-lived OIDC through a repository/workflow-specific Trusted Publisher and
a protected `pypi` environment. Documentation deploys use a protected `docs`
environment. Neither workflow publishes from an unreviewed PR or private repo.
A source-distribution or wheel build alone does not reserve the package name.

Before publication, select the version, review all release files, configure the
provider-side publisher and protected environments, activate eligible GitHub
controls, and explicitly authorize public visibility and publication. No known
GPU advisory is silently dismissed by this preparation.

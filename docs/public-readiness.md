# Public release status

Updated on 2026-10-14. PointCloud Workflows and PointCloud Core have public source
repositories. Package, image, and site publication are separate release actions.

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

The following controls were enabled and read back from GitHub on 2026-10-14
for both public repositories:

- Read-only workflow token; no workflow PR-review approval capability.
- Immutable action commit pins and GitHub-hosted runners for untrusted changes.
- Squash merges using the PR title and an empty commit body, automatic
  merged-branch cleanup, and no merge/rebase merge methods.
- Dependency alerts, secret scanning with push protection, and private
  vulnerability reporting.
- Protected `main` requires pull requests, current passing checks, linear history,
  and resolved conversations; force pushes and deletions are blocked, including
  for administrators. The solo-maintainer policy requires no second approval;
  CI remains mandatory: five PCW checks and four Core checks, bound to the
  GitHub Actions application and requiring an up-to-date branch. CODEOWNERS
  routes review to the maintainer.
- Approval for all external-contributor workflow runs.
- Required `@ajavanma` review for PCW `pypi`/`docs` and Core `pypi` environments,
  with deployment allowed only from `v*` tags. Self-review remains available
  for the solo maintainer; no branch deployment policy is allowed.
- Active rules prevent updates and deletions of existing `v*` tags, with no
  bypass actors. Immutable releases are enabled, protecting published release
  assets as well.
- CodeQL default setup analyzes Python and GitHub Actions with the default
  query suite and both remote and local threat models. Baseline analyses
  completed for both repositories. Main-branch rules require CodeQL results
  and block error-level findings and security findings rated high or critical,
  with no bypass actors.

The initial Core baseline reported no findings. PCW reported four
`py/path-injection` alerts (#1–#4) in its external compatibility-test harness.
Each was independently reviewed and dismissed as a false positive: the source
checkout and interpreter are explicit operator selections, the pinned source
HEAD and package tree are checked, and generated outputs use temporary paths.
These inputs are not dataset fields or service requests. The individual alert
records retain that rationale; local-threat analysis remains enabled. This
triage does not dismiss the separate known GPU dependency advisory.

The initial private staging phase could not activate several of these controls
under the account's repository eligibility. Those staging errors describe the
previous state; the public-launch verification replaces them. Verify live
settings after any policy change instead of assuming repository files enable
protection. See the [release guide](releasing.md) for the reproducible setup.

## Destinations and release boundary

| Artifact | Selected destination | Current state |
| --- | --- | --- |
| Python package | PyPI `pointcloud-workflows` | Prepared, not published; configure Trusted Publisher |
| Documentation | GitHub Pages `https://ajavanma.github.io/PointCloud-Workflows/` | Prepared, not deployed |
| Future container images | `ghcr.io/ajavanma/pointcloud-workflows` | Selected; no image publishing workflow yet |
| Numerical library | Separate `ajavanma/pointcloud-core`, PyPI `pointcloud-core` | Public source; first `0.1.0` release prepared, not published; no PCW dependency yet |

Use [release instructions](releasing.md) and the manual workflows. PyPI releases
use short-lived OIDC through a repository/workflow-specific Trusted Publisher and
a protected `pypi` environment. Documentation deploys use a protected `docs`
environment. Neither workflow publishes from an unreviewed PR or private repo.
A source-distribution or wheel build alone does not reserve the package name.

PCW remains `0.2.0.dev0`. PointCloud Core release preparation targets `0.1.0`
and keeps its package independent of PyTorch and PCW. Before either package is
published, configure its provider-side Trusted Publisher, review the exact
release files, and complete the protected manual release workflow. Repository
visibility does not reserve a PyPI name or upload a distribution. No known GPU
advisory is dismissed by making the source public.

# Releasing PointCloud Workflows

The prepared destinations are:

| Artifact | Destination | Workflow |
| --- | --- | --- |
| Python wheel and source archive | `pointcloud-workflows` on PyPI | `.github/workflows/release.yml` |
| Documentation | `https://ajavanma.github.io/PointCloud-Workflows/` | `.github/workflows/docs.yml` |

These are configured targets, not a claim that either has been published or
reserved. Container registry publication remains a separate release task.
Both workflows require a manual dispatch, this repository to be public, and an
exact `v<package version>` tag whose commit is on `main`. Development versions
cannot be published. Neither a push nor a pull request triggers publication.

## Repository and publisher setup

1. Review the [public-release status](public-readiness.md). Both source
   repositories are public; publishing a package or documentation site remains
   a separate release action. The scripts and workflows do not change visibility.
2. Inspect `python scripts/apply-public-settings.py`. To apply or recheck the
   repository controls, run `python scripts/apply-public-settings.py --apply` with an
   authenticated administrator's `gh` CLI. It enables and verifies `main`
   protection, secret scanning, push protection, dependency alerts, and private
   vulnerability reporting. It stops on unavailable settings or failed checks;
   earlier successful operations remain applied.
3. The branch policy requires pull requests, the five existing CPU CI checks,
   an up-to-date branch, linear history, and resolved conversations. It blocks
   force pushes/deletions and applies to administrators. Required approvals are
   zero so a solo maintainer can merge their own tested PR. CI checks are bound
   to the GitHub Actions application. Update the payload if job names change.
4. In GitHub Settings → Environments create `pypi` and `docs`. Set `@ajavanma`
   as required reviewer and allow deployment from **tags matching `v*` only**.
   For the solo-maintainer workflow leave prevention of self-review disabled;
   approving the environment remains a deliberate publication step. Verify the
   reviewer and tag restrictions exist before dispatching either workflow.
5. Protect `v*` tags from updating/deletion with a repository ruleset. Keep the
   release-authoring policy narrow enough for the maintainer to create new
   version tags. Do not move a tag or reuse a published version.
6. In PyPI, configure a pending
   [Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
   for project `pointcloud-workflows`, owner `ajavanma`, repository
   `PointCloud-Workflows`, workflow filename `release.yml`, and environment
   `pypi`. An account holder must complete this setup; the local package name
   alone does not reserve the PyPI name. No upload token is required.
7. In GitHub Settings → Pages choose **GitHub Actions** as the build source.
   The workflow deploys through the `docs` environment and publishes only the
   generated `site/` artifact. No private repository deployment is allowed by
   the workflow guard.
8. Require approval for all external contributors' workflow runs, keep the
   default token read-only, and prevent PR workflows from receiving release
   credentials. Keep CPU CI on GitHub-hosted runners.

The [branch protection payload](https://github.com/ajavanma/PointCloud-Workflows/blob/main/scripts/public-branch-protection.json)
is reviewable without executing the settings script. Environments, tag rules,
Pages setup, and PyPI account configuration are separate from that script.

## Prepare a version

Make a release PR updating `src/pointcloud_workflows/_version.py`, the changelog,
and the supported runtime information. Use a real release or prerelease version,
such as `0.2.0` or `0.2.0rc1`. Treat checkpoint runtime compatibility as part of
that version decision; see [migration](migration.md).

Run the supported tests and inspect the wheel, source archive, dependency
alerts, and generated docs. Merge only after all five required checks pass.
Replace the transitional PointCloud Core source pin with a tested PyPI release
and regenerate the lockfile first. The release workflow rejects direct URL
dependencies in package metadata, so source integration alone is not releasable
to PyPI.
Create the matching `v<version>` tag on that reviewed commit without moving
existing tags. Before release, confirm the public repository, environments,
PyPI identity, and source version are the intended ones.

## Publish deliberately

Dispatch **Publish Python package** from the chosen version tag. The build job
checks the tag/version and main ancestry, builds wheel and source archive,
validates package metadata, and runs unit, CLI, and CPU model tests against the
installed wheel outside the checkout. Only the later `pypi` job receives OIDC
permission; it downloads those exact distributions and publishes with
attestations after environment approval. No long-lived package-upload secret
is stored in GitHub.

Dispatch **Publish documentation** from the same version tag. It checks the
version and ancestry, builds the docs with strict internal-link checks, and
waits for approval in `docs` before deploying its artifact. Inspect the
published landing page, navigation, install commands, and release links.
Record the released version and resulting URLs in the release notes.

PyPI does not allow replacing a released file. Fix an incorrect package with a
new version, and evaluate whether the old release needs to be yanked. If a
workflow fails after partially uploading, inspect the index before retrying;
the workflow deliberately does not silently skip files that already exist.

## Build the documentation locally

```sh
python -m pip install -r requirements/docs.txt
python -m mkdocs build --strict --site-dir /tmp/pcw-docs-preview
python -m mkdocs serve
```

The source remains in `docs/`, including the existing `docs/gitbook/` guide.
GitHub Pages is independent of the original RPTU GitBook site.

The workflow follows the official guidance for
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
and [GitHub Pages deployments](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Public launch and PointCloud Core (2026-10-14)

Both source repositories are public. PCW remains `0.2.0.dev0`; its package and
MkDocs site have not been published. The [public-release status](public-readiness.md)
records the verified branch, scanning, reporting, environment, and tag controls.
The `pypi` and `docs` environments require maintainer review and accept only
`v*` tags; release-tag updates and deletions are blocked without bypass actors.
Immutable releases also protect published release assets. CodeQL baselines for
Python and GitHub Actions completed, and required main-branch analysis blocks
error-level and high/critical security findings. The public-release record
documents the four PCW compatibility-harness alerts reviewed and dismissed as
false positives. Earlier private-plan eligibility errors belong to the staging
phase. PyPI Trusted Publisher setup and the first release dispatch remain
outstanding; the documentation site has not been deployed.

The separate NumPy-only [PointCloud Core repository](https://github.com/ajavanma/pointcloud-core)
prepares its first `0.1.0` release. It provides point-cloud validation, label
mapping, deterministic voxelization, and original-point lifting without PCW or
PyTorch dependencies. Its own
[release guide](https://github.com/ajavanma/pointcloud-core/blob/main/docs/releasing.md)
tracks the wheel, source archive, tests, and package-index setup. Release
preparation does not upload to PyPI or reserve the package name.

PCW now depends on Core's prepared `0.1.0` source at immutable commit
`5c28a700c30aee6186cfe30f6cd74708289f0743`, with the archive hash checked during
installation. Compatibility tests preserve PCW's dataset and artifact contracts,
feature reduction, error behavior, and model/runtime checks. The
[integration guide](core-integration.md) includes a standalone Core example.
Once Core is published, replace this transitional source pin with its tested
package-index version before a PCW release.

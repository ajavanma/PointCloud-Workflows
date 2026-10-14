# Contributing to PointCloud Workflows

PointCloud Workflows is an independent project derived from RPTU AI Toolkit.
The source repository is public. See [project lineage](docs/project-lineage.md)
and the [public-release record](docs/public-readiness.md) for provenance,
repository protections, and package-release status.

For a substantial change, describe the problem and proposed behavior in an
issue before implementation. Keep pull requests focused, include a small
reproducer when fixing a bug, and explain how the change was checked. Report
security issues through the [security policy](SECURITY.md).

## Development setup

Use Python 3.11 or 3.12 and a fresh virtual environment. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt 'build>=1.2,<2'
pcw doctor
python -m unittest discover -s tests/unit -v
python -m unittest discover -s tests/cli -v
python -m build
```

The base package does not require a GPU or install ML libraries. For changes to
training, evaluation, prediction, or checkpoint behavior, install the CPU model
dependencies and run the ML suite:

```sh
# Linux: choose the CPU PyTorch wheel before installing the extra.
python -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install '.[ml]'
python -m unittest discover -s tests/ml -v
```

On macOS, installing `.[ml]` directly supplies the PyTorch runtime. See
[development and tests](docs/gitbook/development.md) for the supported suites,
wheel acceptance checks, and optional readers, and
[container execution](docs/containers.md) for the container smoke workflow.
State separately whether validation was local, in CI, or on GPU hardware.
The separate compatibility suites use a pinned external source checkout and,
for the runtime-upgrade checks, a second interpreter. See
[fixture provenance](tests/compat/README.md); ordinary tests do not need either.

## Compatibility and data

The canonical distribution, import, and command names are `pointcloud-workflows`,
`pointcloud_workflows`, and `pcw`. The `rptu` command and `rptu_ai_toolkit` imports
remain compatibility aliases. See the [migration guide](docs/migration.md).

Existing artifact kinds deliberately retain the `rptu-*` prefix. A product name
change is not an artifact schema migration. Preserve schema validation,
immutable run metadata, checksum checks, and exact resume compatibility checks.
When changing a format or runtime requirement, document the compatibility impact
and exercise artifacts created by an earlier implementation.

Use synthetic fixtures in tests. Do not commit private datasets, credentials,
local environment files, trained models, or generated run directories. A recipe
for a public dataset should record its source, license, download procedure,
split policy, and conversion steps rather than silently redistribute the data.
The research images in the README are historical illustrations, not current
benchmark results.

## Pull requests and releases

Use short commit and PR titles. Put detailed context in the PR description;
squash commits use the PR title only.

Run the checks relevant to the behavior being changed and keep documentation
examples aligned with the CLI. CI also checks installed wheels outside the source
checkout and exercises the CPU container workflow. Wait for the checks on the
actual PR head before merging. The protected `main` branch requires pull requests
and passing CPU CI checks, including for the maintainer.

Research history stays in the original RPTU repository. This project has fresh
history and no research branches. Keep the MIT license and existing attribution
notices when reusing code. New contributions are made under
the repository's [MIT license](LICENSE); identify any third-party material and
its applicable terms in the pull request.

Publishing a package, image, or documentation site requires a release decision
separate from making the source public. See the [release guide](docs/releasing.md)
for the manual workflows, protected environments, and registry setup.

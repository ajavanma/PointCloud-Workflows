# Documentation publication

The maintained source remains in `docs/gitbook/` for compatibility with existing
links. New PointCloud Workflows documentation is prepared for GitHub Pages at
`https://ajavanma.github.io/PointCloud-Workflows/`, built from this repository with
MkDocs. No successor site has been deployed. See [release setup](releasing.md).

The existing [public RPTU guide](https://rptu.gitbook.io/rptu-ai-toolkit/) and
[original research site](https://arash.gitbook.io/rptu-ai-toolkit/) remain separate.
They are not automatically synchronized with private successor content.

The manual docs workflow builds the reviewed source and deploys only from an
eligible public repository and selected release tag. Configure GitHub Pages to
use Actions and protect the `docs` environment before the first deployment.
The selected destination requires public visibility or an eligible account plan;
preparation does not enable publication or change repository visibility.

The current documentation uses `pointcloud-workflows`, `pointcloud_workflows`,
and `pcw`. Compatibility aliases and artifact policies are described in the
[migration guide](migration.md). Read the [overview](gitbook/README.md),
[quickstart](gitbook/quickstart.md), and [navigation reference](gitbook/SUMMARY.md).

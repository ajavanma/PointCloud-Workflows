"""Compatibility alias for :mod:`pointcloud_workflows.checkpoints`."""

import sys as _sys

from pointcloud_workflows import checkpoints as _canonical

# Both names share one module, including exceptions and patched attributes.
_sys.modules[__name__] = _canonical

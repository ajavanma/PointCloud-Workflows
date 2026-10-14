"""Compatibility alias for :mod:`pointcloud_workflows.ml`."""

import sys as _sys

from pointcloud_workflows import ml as _canonical

# Both names share one module, including exceptions and patched attributes.
_sys.modules[__name__] = _canonical

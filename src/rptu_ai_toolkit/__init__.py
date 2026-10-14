"""Compatibility imports for the renamed :mod:`pointcloud_workflows` package.

Submodules delegate lazily to the canonical implementation.
"""

from pointcloud_workflows import __version__

__all__ = ["__version__"]

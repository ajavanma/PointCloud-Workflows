"""Deterministic CPU voxelization, independent of a sparse-convolution engine."""

from dataclasses import dataclass
from numbers import Real

import numpy as np
import pointcloud_core as core

from .datasets import DatasetError, DatasetManifest, Sample, validate_sample


@dataclass(frozen=True)
class PreparedSample:
    """Voxel arrays plus a mapping for every original input row.

    ``point_to_voxel[i]`` indexes the voxel for input row ``i``; -1 marks a
    removed, nonfinite row. ``point_indices[i]`` is that row's original point
    identifier, which need not equal ``i``. Labels are contiguous training IDs,
    with -1 reserved for ignored labels.
    """

    voxel_coords: np.ndarray
    features: np.ndarray
    labels: np.ndarray | None
    point_to_voxel: np.ndarray
    point_indices: np.ndarray


def voxelize(
    sample: Sample, manifest: DatasetManifest, voxel_size: float
) -> PreparedSample:
    """Aggregate points into voxels of ``voxel_size`` in manifest units.

    Quantization uses floor, including for negative coordinates; no origin
    offset or boundary epsilon is applied. Voxels are ordered lexicographically
    by integer coordinate. Features use an arithmetic mean, while labels use
    the most frequent nonignored training ID (smallest ID on a tie).

    One shared finite-coordinate/finite-feature mask preserves array alignment.
    Unknown labels are rejected before that mask is applied. This operation
    creates new arrays and does not modify the source sample.
    """
    if isinstance(voxel_size, bool) or not isinstance(voxel_size, Real):
        raise DatasetError("voxel_size: expected a finite positive real number")
    try:
        size = float(voxel_size)
    except (OverflowError, ValueError) as error:
        raise DatasetError("voxel_size: expected a finite positive real number") from error
    if not np.isfinite(size) or size <= 0:
        raise DatasetError("voxel_size: expected a finite positive real number")

    sample = validate_sample(sample, len(manifest.feature_names))
    training_labels = (
        None if sample.labels is None else manifest.encode_labels(sample.labels)
    )
    try:
        cloud = core.voxelize(core.PointCloud(
            sample.coords, sample.features, training_labels, sample.point_indices,
        ), size)
    except core.PointCloudError as error:
        raise DatasetError(str(error)) from error

    features = _schema_v1_features(sample.features, cloud.point_to_voxel, len(cloud.voxel_coords))
    return PreparedSample(
        cloud.voxel_coords, features, cloud.labels, cloud.point_to_voxel, cloud.point_indices
    )


def _schema_v1_features(
    source: np.ndarray, point_to_voxel: np.ndarray, voxel_count: int
) -> np.ndarray:
    """Retain exact schema-v1 means for prepared artifacts and checkpoint resume.

    Core uses a scaled mean that preserves subnormal values, but can round
    differently from PCW's historical divide-before-sum operation. Keep that
    operation until an explicit artifact migration; grouping and the shared
    exclusion mask come exclusively from Core's returned point mapping.
    """
    included = point_to_voxel >= 0
    inverse = point_to_voxel[included]
    counts = np.bincount(inverse, minlength=voxel_count)
    features = np.zeros((voxel_count, source.shape[1]), dtype=np.float64)
    with np.errstate(over="ignore", invalid="ignore"):
        np.add.at(features, inverse, source[included] / counts[inverse, None])
    if not np.isfinite(features).all():
        raise DatasetError("features: voxel feature mean is not finite")
    return features

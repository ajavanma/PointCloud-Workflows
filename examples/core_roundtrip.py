"""Validate, voxelize, and restore rows using only NumPy and PointCloud Core.

Run this file with an installed pointcloud-core package. It creates synthetic
arrays in memory and writes only a JSON summary to stdout.
"""

from __future__ import annotations

import json

import numpy as np
from pointcloud_core import (
    LabelMap,
    PointCloud,
    lift_voxel_values,
    validate_cloud,
    voxelize,
)


def main() -> None:
    # Declared class order controls encoded-label tie breaking: 42 precedes 7.
    classes = LabelMap((42, 7), ignore_label=255)
    original_labels = np.array([42, 7, 255, 7, 255, 42, 7], dtype=np.int64)
    original_ids = np.array([100, 8, 901, 42, 5000, 77, 1234], dtype=np.int64)
    cloud = validate_cloud(
        PointCloud(
            coords=[
                [-0.2, 0, 0],
                [-0.1, 0, 0],
                [0.1, 0, 0],
                [0.2, 0, 0],
                [1.2, 0, 0],
                [np.nan, 0, 0],
                [0.3, 0, 0],
            ],
            features=[[2], [4], [6], [10], [12], [14], [np.inf]],
            # Validate every label before filtering any invalid coordinate/feature row.
            labels=classes.encode(original_labels),
            point_indices=original_ids,
        )
    )
    assert cloud.coords.dtype == np.float64
    assert len(cloud.coords) == 7  # Validation retains rows; voxelization filters them.

    voxels = voxelize(cloud, voxel_size=1.0)
    np.testing.assert_array_equal(voxels.voxel_coords, [[-1, 0, 0], [0, 0, 0], [1, 0, 0]])
    np.testing.assert_array_equal(voxels.features, [[3.0], [8.0], [12.0]])
    np.testing.assert_array_equal(voxels.labels, [0, 1, -1])
    np.testing.assert_array_equal(voxels.point_to_voxel, [0, 0, 1, 1, 2, -1, -1])
    np.testing.assert_array_equal(voxels.point_indices, original_ids)

    # Any algorithm can supply one prediction per voxel; no model is required.
    encoded_predictions = np.array([0, 1, 1], dtype=np.int64)
    point_predictions = classes.decode(
        lift_voxel_values(encoded_predictions, voxels.point_to_voxel, fill_value=-1)
    )
    np.testing.assert_array_equal(point_predictions, [42, 42, 7, 7, 7, 255, 255])
    np.testing.assert_array_equal(classes.decode(cloud.labels), original_labels)

    # Sparse IDs remain identities, never array offsets. Excluded rows stay present.
    print(json.dumps({
        "input_points": len(cloud.coords),
        "retained_points": int(np.count_nonzero(voxels.point_to_voxel >= 0)),
        "voxels": len(voxels.voxel_coords),
        "point_to_voxel": voxels.point_to_voxel.tolist(),
        "point_ids": voxels.point_indices.tolist(),
        "predicted_labels": point_predictions.tolist(),
    }, indent=2))


if __name__ == "__main__":
    main()

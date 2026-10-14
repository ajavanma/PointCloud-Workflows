"""Core-backed workflows retain PCW's row, label and numeric contracts."""

from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pointcloud_core as core

from pointcloud_workflows import ml
from pointcloud_workflows.datasets import DatasetError, DatasetManifest, LabelClass, Sample
from pointcloud_workflows.prepared import PreparedSceneData
from pointcloud_workflows.preprocessing import voxelize


class TestCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.manifest = DatasetManifest(
            source=Path("manifest.json"),
            coordinate_unit="m",
            feature_names=("signal", "height"),
            classes=(LabelClass(42, "roof"), LabelClass(7, "wall"), LabelClass(0, "floor")),
            ignore_label=255,
            scenes=(),
        )
        self.sample = Sample(
            coords=np.array([
                [0.5, 0, 0], [-0.5, 0, 0], [np.nextafter(-0.5, -np.inf), 0, 0],
                [0, 0.5, 0], [0, 0, 0], [0, 0.49, 0], [np.nan, 0, 0],
                [3, 0, 0], [-0.49, 0, 0], [1, 0, 0], [1.1, 0, 0], [1.2, 0, 0],
            ]),
            features=np.array([
                [1, 10], [2, 20], [3, 30], [4, 40], [5, 50], [7, 70],
                [17, 170], [np.inf, 80], [8, 80], [10, 100], [11, 110], [12, 120],
            ]),
            labels=np.array([0, 7, 42, 255, 0, 42, 7, 42, 42, 255, 255, 255]),
            point_indices=np.array([1000, 4, 91, 2, 800, 61, 7, 99, 3, 20, 15, 6]),
        )

    def prepared_scene(self, sample=None):
        sample = self.sample if sample is None else sample
        result = voxelize(sample, self.manifest, 0.5)
        return PreparedSceneData(
            result.voxel_coords, result.features, result.labels,
            None if sample.labels is None else self.manifest.encode_labels(sample.labels),
            result.point_indices, result.point_to_voxel,
        )

    def test_core_delegation_preserves_combined_preprocessing_contract(self):
        original = {
            name: getattr(self.sample, name).copy()
            for name in ("coords", "features", "labels", "point_indices")
        }
        for name in original:
            getattr(self.sample, name).flags.writeable = False
        # Wrap the real functions: these assertions catch a dependency that is
        # installed but never used, without substituting the numerical results.
        with (
            patch.object(core, "validate_cloud", wraps=core.validate_cloud) as validate,
            patch.object(core, "voxelize", wraps=core.voxelize) as aggregate,
        ):
            result = voxelize(self.sample, self.manifest, 0.5)
        self.assertGreaterEqual(validate.call_count, 1)
        aggregate.assert_called_once()
        np.testing.assert_array_equal(result.voxel_coords, [
            [-2, 0, 0], [-1, 0, 0], [0, 0, 0], [0, 1, 0], [1, 0, 0], [2, 0, 0],
        ])
        np.testing.assert_array_equal(result.features, [
            [3, 30], [5, 50], [6, 60], [4, 40], [1, 10], [11, 110],
        ])
        # Ties follow declared class order; ignored-only voxels remain -1.
        np.testing.assert_array_equal(result.labels, [0, 0, 0, -1, 2, -1])
        np.testing.assert_array_equal(result.point_to_voxel, [4, 1, 0, 3, 2, 2, -1, -1, 1, 5, 5, 5])
        np.testing.assert_array_equal(result.point_indices, original["point_indices"])
        self.assertEqual(result.features.dtype, np.dtype("float64"))
        for name in ("voxel_coords", "labels", "point_to_voxel", "point_indices"):
            self.assertEqual(getattr(result, name).dtype, np.dtype("int64"))
        for name, values in original.items():
            np.testing.assert_array_equal(getattr(self.sample, name), values)
            for output in (result.voxel_coords, result.features, result.labels,
                           result.point_to_voxel, result.point_indices):
                self.assertFalse(np.shares_memory(output, getattr(self.sample, name)))

    def test_unknown_label_on_excluded_row_keeps_dataset_error(self):
        labels = self.sample.labels.copy()
        labels[6] = 999  # This row has a NaN coordinate and cannot reach a voxel.
        with self.assertRaisesRegex(DatasetError, "unknown dataset class IDs.*999"):
            voxelize(replace(self.sample, labels=labels), self.manifest, 0.5)

    def test_legacy_feature_mean_bytes_survive_core_rounding_difference(self):
        cases = (
            ([0.1, 0.2, 0.3], "0x1.999999999999ap-3", "0x1.9999999999999p-3"),
            ([1, 2, 4], "0x1.2aaaaaaaaaaaap+1", "0x1.2aaaaaaaaaaabp+1"),
            ([float.fromhex("0x0.0000000000001p-1022")] * 2,
             "0x0.0p+0", "0x0.0000000000001p-1022"),
        )
        manifest = replace(self.manifest, feature_names=("signal",))
        for values, legacy_hex, core_hex in cases:
            with self.subTest(values=values):
                sample = Sample(np.zeros((len(values), 3)), np.array(values)[:, None],
                                None, np.arange(len(values)))
                result = voxelize(sample, manifest, 1)
                plain_core = core.voxelize(core.PointCloud(sample.coords, sample.features), 1)
                expected = np.array([[float.fromhex(legacy_hex)]], dtype=np.float64)
                self.assertEqual(result.features.tobytes(), expected.tobytes())
                self.assertEqual(plain_core.features[0, 0].hex(), core_hex)
                self.assertNotEqual(result.features.tobytes(), plain_core.features.tobytes())

    def test_core_lifting_restores_predictions_and_original_targets(self):
        scene = self.prepared_scene()
        predictions = np.array([2, 1, 0, 2, 1, 0], dtype=np.int64)
        before = predictions.copy()
        with patch.object(core, "lift_voxel_values", wraps=core.lift_voxel_values) as lift:
            arrays, training = ml._point_predictions(scene, predictions, self.manifest)
        lift.assert_called_once()
        self.assertEqual(set(arrays), {"point_rows", "point_indices", "labels", "valid_mask", "target_labels"})
        np.testing.assert_array_equal(training, [1, 1, 2, 2, 0, 0, -1, -1, 1, 0, 0, 0])
        np.testing.assert_array_equal(arrays["labels"], [7, 7, 0, 0, 42, 42, 255, 255, 7, 42, 42, 42])
        np.testing.assert_array_equal(arrays["valid_mask"], [True] * 6 + [False] * 2 + [True] * 4)
        np.testing.assert_array_equal(arrays["point_rows"], np.arange(12))
        np.testing.assert_array_equal(arrays["point_indices"], self.sample.point_indices)
        # Source targets are retained even when invalid coordinates/features
        # exclude their prediction rows; the validity mask controls scoring.
        np.testing.assert_array_equal(arrays["target_labels"], self.sample.labels)
        np.testing.assert_array_equal(predictions, before)

    def test_unlabeled_core_pipeline_does_not_invent_targets(self):
        scene = self.prepared_scene(replace(self.sample, labels=None))
        self.assertIsNone(scene.labels)
        self.assertIsNone(scene.point_labels)
        arrays, training = ml._point_predictions(scene, np.zeros(6, dtype=np.int64), self.manifest)
        self.assertNotIn("target_labels", arrays)
        np.testing.assert_array_equal(arrays["labels"], [42] * 6 + [255] * 2 + [42] * 4)
        np.testing.assert_array_equal(training, [0] * 6 + [-1] * 2 + [0] * 4)

    def test_pcw_mapping_lifts_multichannel_scores_without_using_point_ids(self):
        scene = self.prepared_scene()
        scores = np.array([[0, 1], [2, 3], [4, 5], [6, 7], [8, 9], [10, 11]], dtype=np.float32)
        result = core.lift_voxel_values(scores, scene.point_to_voxel, fill_value=np.nan)
        np.testing.assert_array_equal(result, np.array([
            [8, 9], [2, 3], [0, 1], [6, 7], [4, 5], [4, 5],
            [np.nan, np.nan], [np.nan, np.nan], [2, 3], [10, 11], [10, 11], [10, 11],
        ], dtype=np.float32))
        self.assertEqual(result.dtype, np.dtype("float32"))
        self.assertFalse(np.shares_memory(result, scores))


if __name__ == "__main__":
    unittest.main()

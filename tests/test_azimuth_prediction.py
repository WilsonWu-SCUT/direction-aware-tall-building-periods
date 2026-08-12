"""Tests for floor-plan geometry calculations and database integrity."""

from __future__ import annotations

import math
import sqlite3
import unittest
from pathlib import Path

from analysis.azimuth_prediction.geometry import (
    compute_plan_geometry,
    order_outline_segments,
    polygon_section_properties,
)


DATABASE_PATH = Path("data/azimuth_prediction/building_plan_geometry.sqlite")
PERIOD_DATABASE_PATH = Path("data/period_prediction/tall_building_periods.sqlite")


class GeometryUnitTests(unittest.TestCase):
    def test_orders_shuffled_and_reversed_segments(self) -> None:
        segments = [
            (4.0, 2.0, 4.0, 0.0),
            (0.0, 0.0, 0.0, 2.0),
            (4.0, 0.0, 0.0, 0.0),
            (0.0, 2.0, 4.0, 2.0),
        ]
        vertices = order_outline_segments(segments)
        self.assertEqual(len(vertices), 4)
        self.assertAlmostEqual(polygon_section_properties(vertices).area, 8.0)

    def test_rectangle_section_properties(self) -> None:
        vertices = [(0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (0.0, 2.0)]
        section = polygon_section_properties(vertices)
        self.assertAlmostEqual(section.area, 8.0)
        self.assertAlmostEqual(section.centroid_x, 2.0)
        self.assertAlmostEqual(section.centroid_y, 1.0)
        self.assertAlmostEqual(section.ix_centroid, 4.0 * 2.0**3 / 12.0)
        self.assertAlmostEqual(section.iy_centroid, 2.0 * 4.0**3 / 12.0)
        self.assertAlmostEqual(section.ixy_centroid, 0.0)

    def test_rotated_rectangle_recovers_both_rectangles(self) -> None:
        angle = math.radians(31.0)
        ux = (math.cos(angle), math.sin(angle))
        vx = (-math.sin(angle), math.cos(angle))

        def point(local_x: float, local_y: float) -> tuple[float, float]:
            return (
                10.0 + local_x * ux[0] + local_y * vx[0],
                -4.0 + local_x * ux[1] + local_y * vx[1],
            )

        vertices = [
            point(-2.0, -1.0),
            point(2.0, -1.0),
            point(2.0, 1.0),
            point(-2.0, 1.0),
        ]
        geometry = compute_plan_geometry(vertices)
        self.assertAlmostEqual(geometry.minimum_bounding_rectangle.length, 4.0)
        self.assertAlmostEqual(geometry.minimum_bounding_rectangle.width, 2.0)
        self.assertAlmostEqual(geometry.transverse_effective_width, 2.0)
        self.assertAlmostEqual(geometry.longitudinal_effective_width, 4.0)
        self.assertAlmostEqual(geometry.regularity_ratio, 1.0)

    def test_regularity_threshold_is_point_eight(self) -> None:
        vertices = [(0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (0.0, 1.2)]
        geometry = compute_plan_geometry(vertices)
        expected_class = "regular" if geometry.regularity_ratio >= 0.80 else "irregular"
        self.assertEqual(geometry.plan_class, expected_class)


@unittest.skipUnless(DATABASE_PATH.is_file(), "Plan database has not been built.")
class PlanDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.connection = sqlite3.connect(DATABASE_PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.connection.close()

    def count(self, query: str) -> int:
        return self.connection.execute(query).fetchone()[0]

    def test_model_count(self) -> None:
        self.assertEqual(self.count("SELECT COUNT(*) FROM model_plans"), 482)

    def test_all_models_have_geometry_and_source_data(self) -> None:
        self.assertEqual(self.count("SELECT COUNT(*) FROM geometry_metrics"), 482)
        self.assertEqual(self.count("SELECT COUNT(*) FROM source_file_summary"), 482)
        self.assertGreater(self.count("SELECT COUNT(*) FROM plan_segments"), 140_000)
        self.assertGreater(self.count("SELECT COUNT(*) FROM outline_vertices"), 30_000)

    def test_model_ids_match_the_period_database(self) -> None:
        plan_ids = {
            row[0] for row in self.connection.execute("SELECT model_id FROM model_plans")
        }
        period_connection = sqlite3.connect(PERIOD_DATABASE_PATH)
        period_ids = {
            row[0]
            for row in period_connection.execute("SELECT model_id FROM period_records")
        }
        period_connection.close()
        self.assertEqual(len(plan_ids), 482)
        self.assertTrue(plan_ids.issubset(period_ids))

    def test_privacy_sensitive_identifiers_are_not_in_schema(self) -> None:
        schema = " ".join(
            row[0] or ""
            for row in self.connection.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
            )
        ).lower()
        for token in (
            "phone",
            "time_series",
            "project_name",
            "source_path",
            "public_model_id",
            "period_model_id",
            "pairing_status",
        ):
            self.assertNotIn(token, schema)

    def test_reported_and_derived_widths_are_consistent_after_rounding(self) -> None:
        maximum_difference = self.connection.execute(
            """
            SELECT MAX(
                MAX(
                    ABS(plans.transverse_effective_width_m -
                        metrics.transverse_effective_width_m),
                    ABS(plans.longitudinal_effective_width_m -
                        metrics.longitudinal_effective_width_m)
                )
            )
            FROM model_plans AS plans
            JOIN geometry_metrics AS metrics USING (model_pk)
            """
        ).fetchone()[0]
        self.assertLessEqual(maximum_difference, 1.0)


if __name__ == "__main__":
    unittest.main()

"""Regression tests for the Section 4.2 reproduction code."""

from __future__ import annotations

import unittest
from pathlib import Path

from analysis.section_4_2.regression import (
    CATEGORY_ORDER,
    CONSTRAINTS,
    fit_constrained,
    fit_unconstrained,
    group_observations,
    load_directional_observations,
    relative_dispersion_increase,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "tall_building_periods.csv"


class Section42RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.observations = load_directional_observations(DATA)
        cls.groups = group_observations(cls.observations)

    def test_directional_observation_count(self) -> None:
        self.assertEqual(len(self.observations), 2666)

    def test_category_counts(self) -> None:
        expected = {
            ("Non-Framed Tube", "Low-Intensity"): 1852,
            ("Non-Framed Tube", "High-Intensity"): 146,
            ("Framed Tube", "Low-Intensity"): 552,
            ("Framed Tube", "High-Intensity"): 116,
        }
        self.assertEqual({key: len(self.groups[key]) for key in CATEGORY_ORDER}, expected)

    def test_unconstrained_table_3_reproduction(self) -> None:
        expected = {
            ("Non-Framed Tube", "Low-Intensity"): (9.65, 0.19, 0.84, 0.650),
            ("Non-Framed Tube", "High-Intensity"): (2.22, 0.15, 1.09, 0.711),
            ("Framed Tube", "Low-Intensity"): (3.84, 0.23, 1.06, 0.688),
            ("Framed Tube", "High-Intensity"): (3.08, 0.12, 0.98, 0.824),
        }
        for key in CATEGORY_ORDER:
            result = fit_unconstrained(self.groups[key])
            observed = (
                round(100.0 * result.alpha_0, 2),
                round(result.alpha_b, 2),
                round(result.alpha_h, 2),
                round(result.metrics.r_squared, 3),
            )
            self.assertEqual(observed, expected[key])

    def test_constrained_table_4_coefficients(self) -> None:
        expected_alpha_0 = {
            ("Non-Framed Tube", "Low-Intensity"): 4.65,
            ("Non-Framed Tube", "High-Intensity"): 4.04,
            ("Framed Tube", "Low-Intensity"): 3.02,
            ("Framed Tube", "High-Intensity"): 2.47,
        }
        for key in CATEGORY_ORDER:
            result = fit_constrained(self.groups[key], *CONSTRAINTS[key[0]])
            self.assertEqual(round(100.0 * result.alpha_0, 2), expected_alpha_0[key])

    def test_dispersion_increase_is_within_five_percent(self) -> None:
        for key in CATEGORY_ORDER:
            unconstrained = fit_unconstrained(self.groups[key])
            constrained = fit_constrained(self.groups[key], *CONSTRAINTS[key[0]])
            increase = relative_dispersion_increase(
                unconstrained.sigma_ln_t, constrained.sigma_ln_t
            )
            self.assertLessEqual(increase, 5.0)

    def test_no_width_log_r_squared_matches_table_5(self) -> None:
        expected = {
            ("transverse", "Non-Framed Tube", "Low-Intensity"): 0.610,
            ("transverse", "Non-Framed Tube", "High-Intensity"): 0.706,
            ("transverse", "Framed Tube", "Low-Intensity"): 0.791,
            ("transverse", "Framed Tube", "High-Intensity"): 0.829,
            ("longitudinal", "Non-Framed Tube", "Low-Intensity"): 0.633,
            ("longitudinal", "Non-Framed Tube", "High-Intensity"): 0.765,
            ("longitudinal", "Framed Tube", "Low-Intensity"): 0.706,
            ("longitudinal", "Framed Tube", "High-Intensity"): 0.839,
        }
        for (direction, system, intensity), expected_r_squared in expected.items():
            subset = [
                item
                for item in self.observations
                if item.direction == direction
                and item.system_group == system
                and item.intensity_group == intensity
            ]
            result = fit_constrained(subset, 0.0, CONSTRAINTS[system][1])
            self.assertEqual(round(result.r_squared_log, 3), expected_r_squared)


if __name__ == "__main__":
    unittest.main()

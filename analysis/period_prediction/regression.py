"""Regression primitives for direction-aware period prediction."""

from __future__ import annotations

import csv
import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


NON_FT = "Non-Framed Tube"
FT = "Framed Tube"
LOW_INTENSITY = "Low-Intensity"
HIGH_INTENSITY = "High-Intensity"

CATEGORY_ORDER = (
    (NON_FT, LOW_INTENSITY),
    (NON_FT, HIGH_INTENSITY),
    (FT, LOW_INTENSITY),
    (FT, HIGH_INTENSITY),
)

CONSTRAINTS = {
    NON_FT: (0.2, 1.0),
    FT: (0.2, 1.1),
}


@dataclass(frozen=True)
class Observation:
    """One directional period observation from an anonymized building model."""

    model_id: str
    direction: str
    structural_system_code: str
    system_group: str
    intensity_group: str
    building_height_m: float
    effective_width_m: float
    numerical_period_s: float


@dataclass(frozen=True)
class FitMetrics:
    """Goodness-of-fit metrics evaluated in the original period scale."""

    r_squared: float
    rmse_s: float
    mre_percent: float


@dataclass(frozen=True)
class UnconstrainedResult:
    """Three-parameter unconstrained power-law regression result."""

    alpha_0: float
    alpha_b: float
    alpha_h: float
    n_buildings: int
    n_observations: int
    sigma_ln_t: float
    sigma_ln_t_eq23: float
    r_squared_log: float
    metrics: FitMetrics


@dataclass(frozen=True)
class ConstrainedResult:
    """One-parameter constrained power-law regression result."""

    alpha_0: float
    alpha_b: float
    alpha_h: float
    n_buildings: int
    n_observations: int
    sigma_ln_t: float
    sigma_ln_t_eq23: float
    r_squared_log: float
    metrics: FitMetrics


def _system_group(code: str) -> str:
    if code in {"SW", "FSW"}:
        return NON_FT
    if code == "FT":
        return FT
    raise ValueError(f"Unsupported structural-system code: {code!r}")


def _intensity_group(degree: int) -> str:
    if degree in {6, 7}:
        return LOW_INTENSITY
    if degree == 8:
        return HIGH_INTENSITY
    raise ValueError(f"Unsupported seismic intensity degree: {degree}")


def _period_rows(data_path: Path) -> list[dict[str, object]]:
    """Read canonical period rows from SQLite (preferred) or CSV."""

    if data_path.suffix.lower() in {".sqlite", ".sqlite3", ".db"}:
        connection = sqlite3.connect(data_path)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                """
                SELECT model_id, structural_system_code, building_height_m,
                       transverse_effective_width_m,
                       longitudinal_effective_width_m,
                       seismic_intensity_degree, transverse_period_s,
                       longitudinal_period_s
                FROM period_records
                ORDER BY CASE structural_system_code
                    WHEN 'SW' THEN 1
                    WHEN 'FSW' THEN 2
                    WHEN 'FT' THEN 3
                    ELSE 4
                END, source_row
                """
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    with data_path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_directional_observations(data_path: Path) -> list[Observation]:
    """Expand each database row into paired transverse and longitudinal records."""

    observations: list[Observation] = []
    for row in _period_rows(data_path):
        code = str(row["structural_system_code"])
        degree = int(row["seismic_intensity_degree"])
        common = {
            "model_id": str(row["model_id"]),
            "structural_system_code": code,
            "system_group": _system_group(code),
            "intensity_group": _intensity_group(degree),
            "building_height_m": float(row["building_height_m"]),
        }
        for direction in ("transverse", "longitudinal"):
            observation = Observation(
                **common,
                direction=direction,
                effective_width_m=float(row[f"{direction}_effective_width_m"]),
                numerical_period_s=float(row[f"{direction}_period_s"]),
            )
            if min(
                observation.building_height_m,
                observation.effective_width_m,
                observation.numerical_period_s,
            ) <= 0:
                raise ValueError(
                    f"Non-positive regression value for {observation.model_id}."
                )
            observations.append(observation)

    if len(observations) != 2666:
        raise ValueError(
            f"Expected 2,666 directional observations, found {len(observations)}."
        )
    return observations


def group_observations(
    observations: Iterable[Observation],
) -> dict[tuple[str, str], list[Observation]]:
    """Group observations by lateral system and seismic intensity category."""
    groups: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    for observation in observations:
        key = (observation.system_group, observation.intensity_group)
        groups[key].append(observation)
    missing = set(CATEGORY_ORDER) - set(groups)
    if missing:
        raise ValueError(f"Missing regression categories: {sorted(missing)!r}")
    return dict(groups)


def _arrays(
    observations: Sequence[Observation],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    height = np.asarray(
        [item.building_height_m for item in observations], dtype=float
    )
    width = np.asarray(
        [item.effective_width_m for item in observations], dtype=float
    )
    period = np.asarray(
        [item.numerical_period_s for item in observations], dtype=float
    )
    return height, width, period


def original_scale_metrics(
    actual_period_s: np.ndarray, predicted_period_s: np.ndarray
) -> FitMetrics:
    """Calculate R-squared, RMSE, and mean relative error in period space."""
    residual = actual_period_s - predicted_period_s
    sse = float(residual @ residual)
    centered = actual_period_s - float(actual_period_s.mean())
    sst = float(centered @ centered)
    if sst <= 0:
        raise ValueError("R-squared is undefined for a constant response.")
    relative_error = (predicted_period_s - actual_period_s) / actual_period_s
    return FitMetrics(
        r_squared=1.0 - sse / sst,
        rmse_s=math.sqrt(float(np.mean(residual**2))),
        mre_percent=100.0 * float(np.mean(relative_error)),
    )


def _log_dispersion(residual_log: np.ndarray, parameter_count: int) -> tuple[float, float]:
    """Return the reported RMS dispersion and the Eq. (23) DOF correction."""
    sse = float(residual_log @ residual_log)
    n = len(residual_log)
    if n <= parameter_count:
        raise ValueError("Insufficient observations for dispersion estimation.")
    sigma_reported = math.sqrt(sse / n)
    sigma_eq23 = math.sqrt(sse / (n - parameter_count))
    return sigma_reported, sigma_eq23


def _log_r_squared(actual_log: np.ndarray, predicted_log: np.ndarray) -> float:
    residual = actual_log - predicted_log
    centered = actual_log - float(actual_log.mean())
    return 1.0 - float(residual @ residual) / float(centered @ centered)


def fit_unconstrained(
    observations: Sequence[Observation],
) -> UnconstrainedResult:
    """Fit ln(T) = ln(alpha_0) + alpha_H ln(H) - alpha_B ln(B)."""
    height, width, period = _arrays(observations)
    log_period = np.log(period)
    design = np.column_stack(
        [np.ones(len(period)), np.log(height), -np.log(width)]
    )
    coefficients, _, rank, _ = np.linalg.lstsq(design, log_period, rcond=None)
    if rank != 3:
        raise ValueError("The unconstrained design matrix is rank deficient.")

    log_alpha_0, alpha_h, alpha_b = (float(value) for value in coefficients)
    predicted_log = design @ coefficients
    predicted_period = np.exp(predicted_log)
    residual_log = log_period - predicted_log
    sigma_reported, sigma_eq23 = _log_dispersion(residual_log, 3)
    return UnconstrainedResult(
        alpha_0=math.exp(log_alpha_0),
        alpha_b=alpha_b,
        alpha_h=alpha_h,
        n_buildings=len({item.model_id for item in observations}),
        n_observations=len(observations),
        sigma_ln_t=sigma_reported,
        sigma_ln_t_eq23=sigma_eq23,
        r_squared_log=_log_r_squared(log_period, predicted_log),
        metrics=original_scale_metrics(period, predicted_period),
    )


def constrained_prediction(
    observations: Sequence[Observation],
    alpha_0: float,
    alpha_b: float,
    alpha_h: float,
) -> np.ndarray:
    """Predict periods using T = alpha_0 (H / B^alpha_B)^alpha_H."""
    height, width, _ = _arrays(observations)
    return alpha_0 * (height / np.power(width, alpha_b)) ** alpha_h


def fit_constrained(
    observations: Sequence[Observation],
    alpha_b: float,
    alpha_h: float,
) -> ConstrainedResult:
    """Fit alpha_0 with fixed geometry exponents in the manuscript model."""
    height, width, period = _arrays(observations)
    log_period = np.log(period)
    offset = alpha_h * (np.log(height) - alpha_b * np.log(width))
    log_alpha_0 = float(np.mean(log_period - offset))
    predicted_log = log_alpha_0 + offset
    predicted_period = np.exp(predicted_log)
    residual_log = log_period - predicted_log
    sigma_reported, sigma_eq23 = _log_dispersion(residual_log, 1)
    return ConstrainedResult(
        alpha_0=math.exp(log_alpha_0),
        alpha_b=alpha_b,
        alpha_h=alpha_h,
        n_buildings=len({item.model_id for item in observations}),
        n_observations=len(observations),
        sigma_ln_t=sigma_reported,
        sigma_ln_t_eq23=sigma_eq23,
        r_squared_log=_log_r_squared(log_period, predicted_log),
        metrics=original_scale_metrics(period, predicted_period),
    )


def relative_dispersion_increase(
    unconstrained_sigma: float, constrained_sigma: float
) -> float:
    """Return Eq. (24) as a percentage using constrained sigma as denominator."""
    return 100.0 * (constrained_sigma - unconstrained_sigma) / constrained_sigma


def contour_sigma_surface(
    observations: Sequence[Observation],
    alpha_b_grid: np.ndarray,
    alpha_h_grid: np.ndarray,
) -> np.ndarray:
    """Profile alpha_0 and calculate log-dispersion over an exponent grid."""
    height, width, period = _arrays(observations)
    log_height = np.log(height)
    log_width = np.log(width)
    log_period = np.log(period)
    surface = np.empty((len(alpha_h_grid), len(alpha_b_grid)), dtype=float)

    for row_index, alpha_h in enumerate(alpha_h_grid):
        offset = alpha_h * (
            log_height[None, :] - alpha_b_grid[:, None] * log_width[None, :]
        )
        log_alpha_0 = np.mean(log_period[None, :] - offset, axis=1)
        residual = log_period[None, :] - (log_alpha_0[:, None] + offset)
        surface[row_index, :] = np.sqrt(np.mean(residual**2, axis=1))
    return surface

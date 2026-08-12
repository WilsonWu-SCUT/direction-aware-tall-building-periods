#!/usr/bin/env python3
"""Select and render representative azimuth examples from the public database."""

from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.azimuth_prediction.database import load_plan  # noqa: E402
from analysis.azimuth_prediction.geometry import compute_plan_geometry  # noqa: E402
from analysis.azimuth_prediction.plotting import (  # noqa: E402
    configure_paper_style,
    draw_plan,
    figure_legend_handles,
)


DEFAULT_DATABASE = ROOT / "data" / "azimuth_prediction" / "building_plan_geometry.sqlite"
DEFAULT_OUTPUT = ROOT / "results" / "azimuth_prediction" / "figures"
DEFAULT_MARKDOWN = ROOT / "results" / "azimuth_prediction" / "regularity_examples.md"
TARGET_RATIOS = tuple(round(0.95 - 0.05 * index, 2) for index in range(11))
HALF_INTERVAL = 0.025
MIN_EQUIVALENT_ASPECT_RATIO = 1.20


@dataclass(frozen=True)
class Candidate:
    model_id: str
    ratio: float
    equivalent_angle: float
    bounding_angle: float
    target_ratio: float
    axis_deviation: float
    rectangle_deviation: float
    equivalent_aspect_ratio: float
    score: float

    @property
    def plan_class(self) -> str:
        return "regular" if self.ratio >= 0.80 else "irregular"


def angular_distance_mod90(first: float, second: float = 0.0) -> float:
    difference = abs((first - second) % 90.0)
    return min(difference, 90.0 - difference)


def select_examples(database: Path) -> list[Candidate]:
    connection = sqlite3.connect(database)
    try:
        rows = connection.execute(
            """
            SELECT model_id, regularity_ratio,
                   equivalent_rectangle_long_axis_deg, mbr_long_axis_deg,
                   major_principal_moment_m4, minor_principal_moment_m4
            FROM plan_geometry_readable
            """
        ).fetchall()
    finally:
        connection.close()

    selected: list[Candidate] = []
    for target in TARGET_RATIOS:
        candidates: list[Candidate] = []
        for (
            model_id,
            ratio,
            equivalent_angle,
            bounding_angle,
            major_moment,
            minor_moment,
        ) in rows:
            if not (
                target - HALF_INTERVAL <= ratio < target + HALF_INTERVAL
                and ratio < 0.975
            ):
                continue
            equivalent_aspect_ratio = math.sqrt(major_moment / minor_moment)
            if equivalent_aspect_ratio < MIN_EQUIVALENT_ASPECT_RATIO:
                continue
            axis_deviation = angular_distance_mod90(equivalent_angle)
            rectangle_deviation = angular_distance_mod90(
                equivalent_angle, bounding_angle
            )
            smaller_deviation = min(axis_deviation, rectangle_deviation)
            larger_deviation = max(axis_deviation, rectangle_deviation)
            score = 0.65 * smaller_deviation + 0.35 * larger_deviation
            candidates.append(
                Candidate(
                    model_id=model_id,
                    ratio=ratio,
                    equivalent_angle=equivalent_angle,
                    bounding_angle=bounding_angle,
                    target_ratio=target,
                    axis_deviation=axis_deviation,
                    rectangle_deviation=rectangle_deviation,
                    equivalent_aspect_ratio=equivalent_aspect_ratio,
                    score=score,
                )
            )
        if not candidates:
            raise ValueError(f"No candidate found for target ratio {target:.2f}.")
        selected.append(
            max(
                candidates,
                key=lambda item: (
                    item.score,
                    item.axis_deviation,
                    item.rectangle_deviation,
                ),
            )
        )
    return selected


def draw_candidate(axis, database: Path, candidate: Candidate) -> None:
    _, segments, vertices = load_plan(database, candidate.model_id)
    geometry = compute_plan_geometry(vertices)
    draw_plan(axis, segments, vertices, geometry)
    axis.set_title(
        f"A≈{candidate.target_ratio:.2f}  {candidate.model_id}  "
        f"A={candidate.ratio:.3f}\n"
        f"Δaxis={candidate.axis_deviation:.1f}°  "
        f"ΔMBR={candidate.rectangle_deviation:.1f}°  "
        f"{candidate.plan_class.title()}",
        fontsize=8.5,
        fontweight="bold",
        pad=3,
    )


def write_markdown(path: Path, selected: list[Candidate]) -> None:
    lines = [
        "# Representative plan-regularity examples",
        "",
        "These examples are selected directly from "
        "`data/azimuth_prediction/building_plan_geometry.sqlite` at target "
        "regularity ratios from 0.95 to 0.45 in steps of 0.05. Exact and "
        "near-exact rectangles above 0.975 are excluded. To avoid numerically "
        "ambiguous principal directions, the inertia-equivalent rectangle must "
        "have a long-to-short aspect ratio of at least 1.20. The classification "
        "threshold is `eta_A = 0.80`: values below 0.80 are irregular.",
        "",
        "![Representative examples](figures/plan_geometry_area_ratio_examples.png)",
        "",
        "| Target `eta_A` | Model ID | Actual `eta_A` | Class | "
        "Equivalent aspect ratio | Equivalent angle | Axis deviation | "
        "MBR deviation | Figure |",
        "|---:|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for item in selected:
        code = int(round(item.target_ratio * 100))
        lines.append(
            f"| {item.target_ratio:.2f} | {item.model_id} | {item.ratio:.6f} | "
            f"{item.plan_class.title()} | {item.equivalent_aspect_ratio:.3f} | "
            f"{item.equivalent_angle:.2f}° | "
            f"{item.axis_deviation:.2f}° | {item.rectangle_deviation:.2f}° | "
            f"[PNG](figures/plan_geometry_A{code:03d}.png) |"
        )
    lines.extend(
        [
            "",
            "Regenerate all figures and this table with:",
            "",
            "```bash",
            "python scripts/generate_azimuth_examples.py",
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    configure_paper_style()
    selected = select_examples(args.database)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for candidate in selected:
        figure, axis = plt.subplots(figsize=(5.2, 5.4))
        draw_candidate(axis, args.database, candidate)
        figure.legend(
            handles=figure_legend_handles(),
            loc="lower center",
            ncol=3,
            frameon=False,
            fontsize=7.2,
        )
        figure.subplots_adjust(left=0.03, right=0.97, top=0.88, bottom=0.16)
        code = int(round(candidate.target_ratio * 100))
        figure.savefig(args.output_dir / f"plan_geometry_A{code:03d}.png", dpi=args.dpi)
        plt.close(figure)

    rows = math.ceil(len(selected) / 3)
    figure, axes = plt.subplots(rows, 3, figsize=(12.0, rows * 3.8))
    for axis, candidate in zip(axes.flat, selected):
        draw_candidate(axis, args.database, candidate)
    for axis in axes.flat[len(selected):]:
        axis.set_visible(False)
    figure.suptitle(
        "Representative footprints at 0.05 regularity-ratio intervals",
        fontsize=15,
        fontweight="bold",
        y=0.995,
    )
    figure.legend(
        handles=figure_legend_handles(),
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    figure.subplots_adjust(left=0.02, right=0.98, top=0.965, bottom=0.05, hspace=0.24)
    figure.savefig(
        args.output_dir / "plan_geometry_area_ratio_examples.png",
        dpi=args.dpi,
    )
    plt.close(figure)
    write_markdown(args.markdown, selected)
    print(f"Generated {len(selected)} examples in {args.output_dir}")


if __name__ == "__main__":
    main()

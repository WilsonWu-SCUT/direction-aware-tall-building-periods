"""Plot one public building plan with manuscript-style geometry overlays."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from analysis.azimuth_prediction.database import list_models, load_plan
from analysis.azimuth_prediction.geometry import compute_plan_geometry
from analysis.azimuth_prediction.plotting import (
    configure_paper_style,
    draw_plan,
    figure_legend_handles,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--model-id", help="Period-database identifier such as SW-701.")
    group.add_argument(
        "--all",
        action="store_true",
        help="Generate one PNG for every model in the plan database.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/azimuth_prediction/building_plan_geometry.sqlite"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/azimuth_prediction/figures/plans"),
    )
    parser.add_argument("--centroid", action="store_true")
    return parser.parse_args()


def plot_model(
    database: Path,
    model_id: str,
    output: Path,
    show_centroid: bool = False,
) -> Path:
    """Generate one self-contained plan figure for one period model identifier."""

    record, segments, vertices = load_plan(
        database,
        model_id,
    )
    geometry = compute_plan_geometry(vertices)
    output.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(4.8, 4.8))
    figure.subplots_adjust(left=0.04, right=0.96, bottom=0.19, top=0.86)
    draw_plan(
        axis,
        segments,
        vertices,
        geometry,
        show_centroid=show_centroid,
    )
    axis.set_title(
        f"{record.model_id}\n"
        rf"$\eta_A={geometry.regularity_ratio:.2f}$, "
        f"Plan-{geometry.plan_class.title()}",
        fontsize=9,
        fontweight="bold",
        pad=3,
    )
    figure.legend(
        handles=figure_legend_handles(),
        loc="lower center",
        bbox_to_anchor=(0.5, 0.015),
        ncol=3,
        frameon=False,
        fontsize=7.5,
    )
    figure.savefig(output, dpi=400)
    plt.close(figure)
    return output.resolve()


def main() -> None:
    args = parse_args()
    if args.all and args.output is not None:
        raise SystemExit("--output is only valid with --model-id; use --output-dir with --all.")
    configure_paper_style()

    if args.model_id:
        output = args.output or args.output_dir / f"{args.model_id.lower()}_plan.png"
        print(plot_model(args.database, args.model_id, output, args.centroid))
        return

    records = list_models(args.database)
    for record in records:
        output = args.output_dir / f"{record.model_id.lower()}_plan.png"
        plot_model(args.database, record.model_id, output, args.centroid)
    print(f"Generated {len(records)} plan figures in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run every Section 4.2 analysis except fold cross-validation."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.section_4_2.regression import (  # noqa: E402
    CATEGORY_ORDER,
    CONSTRAINTS,
    FT,
    HIGH_INTENSITY,
    LOW_INTENSITY,
    NON_FT,
    ConstrainedResult,
    Observation,
    UnconstrainedResult,
    constrained_prediction,
    contour_sigma_surface,
    fit_constrained,
    fit_unconstrained,
    group_observations,
    load_directional_observations,
    original_scale_metrics,
    relative_dispersion_increase,
)


DEFAULT_DATA = ROOT / "data" / "tall_building_periods.csv"
DEFAULT_OUTPUT = ROOT / "results" / "section_4_2"


def write_csv(path: Path, rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows supplied for {path}.")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def write_markdown_table(path: Path, rows: Sequence[dict[str, object]]) -> None:
    headers = list(rows[0])
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(markdown_value(row[key]) for key in headers) + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _category_rows(
    unconstrained: dict[tuple[str, str], UnconstrainedResult],
    constrained: dict[tuple[str, str], ConstrainedResult],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    table_3: list[dict[str, object]] = []
    table_4: list[dict[str, object]] = []
    for key in CATEGORY_ORDER:
        system, intensity = key
        unconstrained_result = unconstrained[key]
        constrained_result = constrained[key]
        table_3.append(
            {
                "lateral_force_resisting_system": system,
                "seismic_design_intensity": intensity,
                "n_buildings": unconstrained_result.n_buildings,
                "n_directional_observations": unconstrained_result.n_observations,
                "alpha_0_times_100": 100.0 * unconstrained_result.alpha_0,
                "alpha_b": unconstrained_result.alpha_b,
                "alpha_h": unconstrained_result.alpha_h,
                "r_squared": unconstrained_result.metrics.r_squared,
                "r_squared_log": unconstrained_result.r_squared_log,
                "sigma_ln_t": unconstrained_result.sigma_ln_t,
                "sigma_ln_t_eq23": unconstrained_result.sigma_ln_t_eq23,
            }
        )
        table_4.append(
            {
                "lateral_force_resisting_system": system,
                "seismic_design_intensity": intensity,
                "n_buildings": constrained_result.n_buildings,
                "n_directional_observations": constrained_result.n_observations,
                "alpha_0_times_100": 100.0 * constrained_result.alpha_0,
                "alpha_b": constrained_result.alpha_b,
                "alpha_h": constrained_result.alpha_h,
                "r_squared": constrained_result.metrics.r_squared,
                "r_squared_log": constrained_result.r_squared_log,
                "sigma_ln_t": constrained_result.sigma_ln_t,
                "sigma_ln_t_eq23": constrained_result.sigma_ln_t_eq23,
                "e_sigma_percent": relative_dispersion_increase(
                    unconstrained_result.sigma_ln_t,
                    constrained_result.sigma_ln_t,
                ),
            }
        )
    return table_3, table_4


def _no_width_rows(
    observations: Sequence[Observation],
) -> tuple[list[dict[str, object]], dict[tuple[str, str, str], ConstrainedResult]]:
    rows: list[dict[str, object]] = []
    results: dict[tuple[str, str, str], ConstrainedResult] = {}
    for direction in ("transverse", "longitudinal"):
        for system, intensity in CATEGORY_ORDER:
            subset = [
                item
                for item in observations
                if item.direction == direction
                and item.system_group == system
                and item.intensity_group == intensity
            ]
            _, alpha_h = CONSTRAINTS[system]
            result = fit_constrained(subset, alpha_b=0.0, alpha_h=alpha_h)
            results[(direction, system, intensity)] = result
            rows.append(
                {
                    "translational_period": "T_S" if direction == "transverse" else "T_L",
                    "lateral_force_resisting_system": system,
                    "seismic_design_intensity": intensity,
                    "n_buildings": result.n_buildings,
                    "alpha_0_times_100": 100.0 * result.alpha_0,
                    "alpha_b": result.alpha_b,
                    "alpha_h": result.alpha_h,
                    "r_squared": result.r_squared_log,
                    "r_squared_period": result.metrics.r_squared,
                    "sigma_ln_t": result.sigma_ln_t,
                    "sigma_ln_t_eq23": result.sigma_ln_t_eq23,
                }
            )
    return rows, results


def _tex_number(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}"


def write_latex_tables(
    directory: Path,
    table_3: Sequence[dict[str, object]],
    table_4: Sequence[dict[str, object]],
    table_5: Sequence[dict[str, object]],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)

    lines_3 = [
        "% Requires booktabs and multirow.",
        "\\begin{tabular}{llrrrrr}",
        "\\toprule",
        "Lateral force-resisting system & Seismic design intensity & $\\alpha_0$ ($10^{-2}$) & $\\alpha_B$ & $\\alpha_H$ & $R^2$ & $\\sigma_{\\ln T}$ \\\\",
        "\\midrule",
    ]
    for index, row in enumerate(table_3):
        system = row["lateral_force_resisting_system"] if index % 2 == 0 else ""
        lines_3.append(
            f"{system} & {row['seismic_design_intensity']} & "
            f"{_tex_number(float(row['alpha_0_times_100']), 2)} & "
            f"{_tex_number(float(row['alpha_b']), 2)} & "
            f"{_tex_number(float(row['alpha_h']), 2)} & "
            f"{_tex_number(float(row['r_squared']), 3)} & "
            f"{_tex_number(float(row['sigma_ln_t']), 3)} \\\\")
    lines_3.extend(["\\bottomrule", "\\end{tabular}", ""])
    (directory / "table_3_unconstrained.tex").write_text(
        "\n".join(lines_3), encoding="utf-8"
    )

    lines_4 = [
        "% Requires booktabs and multirow.",
        "\\begin{tabular}{llrrrrrr}",
        "\\toprule",
        "Lateral force-resisting system & Seismic design intensity & $\\alpha_0$ ($10^{-2}$) & $\\alpha_B$ & $\\alpha_H$ & $R^2$ & $\\sigma_{\\ln T}$ & $e_{\\sigma}$ \\\\",
        "\\midrule",
    ]
    for index, row in enumerate(table_4):
        system = row["lateral_force_resisting_system"] if index % 2 == 0 else ""
        lines_4.append(
            f"{system} & {row['seismic_design_intensity']} & "
            f"{_tex_number(float(row['alpha_0_times_100']), 2)} & "
            f"{_tex_number(float(row['alpha_b']), 1)} & "
            f"{_tex_number(float(row['alpha_h']), 1)} & "
            f"{_tex_number(float(row['r_squared']), 3)} & "
            f"{_tex_number(float(row['sigma_ln_t']), 3)} & "
            f"{_tex_number(float(row['e_sigma_percent']), 2)}\\% \\\\")
    lines_4.extend(["\\bottomrule", "\\end{tabular}", ""])
    (directory / "table_4_constrained.tex").write_text(
        "\n".join(lines_4), encoding="utf-8"
    )

    lines_5 = [
        "% Requires booktabs and multirow.",
        "\\begin{tabular}{lllrrrrr}",
        "\\toprule",
        "Translational period & Lateral force-resisting system & Seismic design intensity & $\\alpha_0$ ($10^{-2}$) & $\\alpha_B$ & $\\alpha_H$ & $R^2$ & $\\sigma_{\\ln T}$ \\\\",
        "\\midrule",
    ]
    for index, row in enumerate(table_5):
        direction = row["translational_period"] if index % 4 == 0 else ""
        system = row["lateral_force_resisting_system"] if index % 2 == 0 else ""
        lines_5.append(
            f"{direction} & {system} & {row['seismic_design_intensity']} & "
            f"{_tex_number(float(row['alpha_0_times_100']), 2)} & "
            f"{_tex_number(float(row['alpha_b']), 0)} & "
            f"{_tex_number(float(row['alpha_h']), 1)} & "
            f"{_tex_number(float(row['r_squared']), 3)} & "
            f"{_tex_number(float(row['sigma_ln_t']), 3)} \\\\")
    lines_5.extend(["\\bottomrule", "\\end{tabular}", ""])
    (directory / "table_5_no_width.tex").write_text(
        "\n".join(lines_5), encoding="utf-8"
    )


def _configure_matplotlib() -> None:
    import matplotlib as mpl

    mpl.use("Agg")
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 10,
            "axes.linewidth": 0.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": False,
            "ytick.right": False,
            "savefig.facecolor": "white",
        }
    )


def plot_figure_11(
    output_directory: Path,
    groups: dict[tuple[str, str], list[Observation]],
    unconstrained: dict[tuple[str, str], UnconstrainedResult],
    dpi: int,
) -> None:
    _configure_matplotlib()
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    alpha_b_grid = np.linspace(-0.4, 1.2, 241)
    alpha_h_grid = np.linspace(0.0, 2.0, 241)
    mesh_b, mesh_h = np.meshgrid(alpha_b_grid, alpha_h_grid)
    levels = np.linspace(0.10, 0.70, 13)

    figure, axes = plt.subplots(2, 2, figsize=(8.0, 7.2), constrained_layout=True)
    contour_sets = []
    for row_index, system in enumerate((NON_FT, FT)):
        for column_index, intensity in enumerate((LOW_INTENSITY, HIGH_INTENSITY)):
            key = (system, intensity)
            axis = axes[row_index, column_index]
            surface = contour_sigma_surface(
                groups[key], alpha_b_grid, alpha_h_grid
            )
            contour_set = axis.contourf(
                mesh_b,
                mesh_h,
                surface,
                levels=levels,
                cmap="jet",
                extend="both",
            )
            contour_sets.append(contour_set)

            unconstrained_result = unconstrained[key]
            threshold = unconstrained_result.sigma_ln_t / 0.95
            axis.contour(
                mesh_b,
                mesh_h,
                surface,
                levels=[threshold],
                colors=["#38e8e8"],
                linestyles="--",
                linewidths=1.8,
            )
            axis.plot(
                unconstrained_result.alpha_b,
                unconstrained_result.alpha_h,
                marker="*",
                color="red",
                markersize=11,
                markeredgewidth=0.7,
                markeredgecolor="red",
            )
            selected_alpha_b, selected_alpha_h = CONSTRAINTS[system]
            axis.axvline(selected_alpha_b, color="red", linestyle=(0, (5, 4)), linewidth=1.2)
            axis.axhline(selected_alpha_h, color="red", linestyle=(0, (5, 4)), linewidth=1.2)

            axis.set_xlim(-0.4, 1.2)
            axis.set_ylim(0.0, 2.0)
            axis.set_xticks([-0.4, 0.0, 0.4, 0.8, 1.2])
            axis.set_yticks([0.0, 0.5, 1.0, 1.5, 2.0])
            axis.set_xlabel(r"$\alpha_B$")
            axis.set_ylabel(r"$\alpha_H$")
            axis.set_title(intensity, pad=4)

        axes[row_index, 0].text(
            -0.33,
            1.08,
            f"({'a' if row_index == 0 else 'b'}) {system}",
            transform=axes[row_index, 0].transAxes,
            fontweight="bold",
        )

    colorbar = figure.colorbar(
        contour_sets[0], ax=axes, fraction=0.025, pad=0.02, ticks=[0.14, 0.70]
    )
    colorbar.set_label(r"$\sigma_{\ln T}$")
    legend_handles = [
        Line2D([], [], marker="*", color="red", linestyle="None", markersize=11,
               label="Unconstrained regression solution"),
        Line2D([], [], color="#38e8e8", linestyle="--", linewidth=1.8,
               label="Admissible adjustment boundary"),
    ]
    figure.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_directory / "fig_11_constrained_contours.png", dpi=dpi, bbox_inches="tight")
    figure.savefig(output_directory / "fig_11_constrained_contours.pdf", bbox_inches="tight")
    plt.close(figure)


def build_full_data_predictions(
    observations: Sequence[Observation],
    constrained: dict[tuple[str, str], ConstrainedResult],
) -> list[dict[str, object]]:
    prediction_rows: list[dict[str, object]] = []
    for observation in observations:
        key = (observation.system_group, observation.intensity_group)
        result = constrained[key]
        predicted = float(
            constrained_prediction(
                [observation], result.alpha_0, result.alpha_b, result.alpha_h
            )[0]
        )
        actual = observation.numerical_period_s
        prediction_rows.append(
            {
                "model_id": observation.model_id,
                "direction": observation.direction,
                "lateral_force_resisting_system": observation.system_group,
                "seismic_design_intensity": observation.intensity_group,
                "numerical_period_s": actual,
                "predicted_period_s": predicted,
                "residual_s": actual - predicted,
                "relative_error_percent": 100.0 * (predicted - actual) / actual,
            }
        )
    return prediction_rows


def prediction_metric_rows(
    prediction_rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for label, direction in (
        ("Transverse", "transverse"),
        ("Longitudinal", "longitudinal"),
        ("Combined", None),
    ):
        subset = [
            row
            for row in prediction_rows
            if direction is None or row["direction"] == direction
        ]
        actual = np.asarray([row["numerical_period_s"] for row in subset], dtype=float)
        predicted = np.asarray([row["predicted_period_s"] for row in subset], dtype=float)
        metrics = original_scale_metrics(actual, predicted)
        output.append(
            {
                "dataset": label,
                "n_observations": len(subset),
                "r_squared": metrics.r_squared,
                "rmse_s": metrics.rmse_s,
                "mre_percent": metrics.mre_percent,
            }
        )
    return output


def plot_figure_13(
    output_directory: Path,
    prediction_rows: Sequence[dict[str, object]],
    metric_rows: Sequence[dict[str, object]],
    dpi: int,
) -> None:
    _configure_matplotlib()
    import matplotlib.pyplot as plt

    metric_map = {row["dataset"]: row for row in metric_rows}
    figure, axes = plt.subplots(1, 3, figsize=(10.2, 3.5), sharex=True, sharey=True)
    panels = [
        ("Transverse", {"transverse"}, [("transverse", r"$T_S$", "#1717ff", "s")]),
        ("Longitudinal", {"longitudinal"}, [("longitudinal", r"$T_L$", "#20dfea", "o")]),
        (
            "Combined",
            {"transverse", "longitudinal"},
            [
                ("transverse", r"$T_S$", "#1717ff", "s"),
                ("longitudinal", r"$T_L$", "#20dfea", "o"),
            ],
        ),
    ]

    for panel_index, (label, _, series) in enumerate(panels):
        axis = axes[panel_index]
        for direction, legend_label, color, marker in series:
            subset = [row for row in prediction_rows if row["direction"] == direction]
            axis.scatter(
                [row["numerical_period_s"] for row in subset],
                [row["predicted_period_s"] for row in subset],
                s=14,
                marker=marker,
                facecolors="none",
                edgecolors=color,
                linewidths=0.65,
                alpha=0.75,
                label=legend_label,
            )
        axis.plot([0, 6], [0, 6], color="#ff4444", linewidth=1.0)
        axis.set_xlim(0, 6)
        axis.set_ylim(0, 6)
        axis.set_xticks([0, 2, 4, 6])
        axis.set_yticks([0, 2, 4, 6])
        axis.grid(True, linestyle=":", color="0.82", linewidth=0.6)
        axis.set_xlabel("Numerical period (s)")
        axis.text(-0.10, 1.02, f"({chr(97 + panel_index)})", transform=axis.transAxes,
                  fontweight="bold")
        metric = metric_map[label]
        axis.text(
            0.95,
            0.06,
            f"$R^2$ = {float(metric['r_squared']):.2f}\n"
            f"RMSE = {float(metric['rmse_s']):.2f} s\n"
            f"MRE = {float(metric['mre_percent']):.1f}%",
            transform=axis.transAxes,
            ha="right",
            va="bottom",
        )
        axis.legend(loc="upper left", frameon=False, handletextpad=0.3)
    axes[0].set_ylabel("Predicted period (s)")
    figure.subplots_adjust(wspace=0.28, bottom=0.18)

    output_directory.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_directory / "fig_13_full_data_predictions.png", dpi=dpi, bbox_inches="tight")
    figure.savefig(output_directory / "fig_13_full_data_predictions.pdf", bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dpi", type=int, default=600)
    parser.add_argument("--skip-figures", action="store_true")
    args = parser.parse_args()

    observations = load_directional_observations(args.data)
    groups = group_observations(observations)
    unconstrained = {
        key: fit_unconstrained(groups[key]) for key in CATEGORY_ORDER
    }
    constrained = {
        key: fit_constrained(groups[key], *CONSTRAINTS[key[0]])
        for key in CATEGORY_ORDER
    }

    table_3, table_4 = _category_rows(unconstrained, constrained)
    table_5, _ = _no_width_rows(observations)
    table_directory = args.output / "tables"
    for stem, rows in (
        ("table_3_unconstrained", table_3),
        ("table_4_constrained", table_4),
        ("table_5_no_width", table_5),
    ):
        write_csv(table_directory / f"{stem}.csv", rows)
        write_markdown_table(table_directory / f"{stem}.md", rows)
    write_latex_tables(table_directory, table_3, table_4, table_5)

    predictions = build_full_data_predictions(observations, constrained)
    metrics = prediction_metric_rows(predictions)
    write_csv(args.output / "data" / "full_data_predictions.csv", predictions)
    write_csv(args.output / "tables" / "fig_13_full_data_metrics.csv", metrics)
    write_markdown_table(
        args.output / "tables" / "fig_13_full_data_metrics.md", metrics
    )

    if not args.skip_figures:
        plot_figure_11(args.output / "figures", groups, unconstrained, args.dpi)
        plot_figure_13(args.output / "figures", predictions, metrics, args.dpi)

    print(f"Completed Section 4.2 analysis using {len(observations):,} observations.")
    print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()

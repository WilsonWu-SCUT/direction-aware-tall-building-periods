"""Matplotlib presentation helpers for floor-plan geometry results."""

from __future__ import annotations

from collections.abc import Sequence

from .geometry import PlanGeometry, Point, Segment, close_ring


PLAN_COLOR = "#A7B4FF"
OUTLINE_COLOR = "#F01818"
BOUNDING_COLOR = "#003BFF"
EQUIVALENT_COLOR = "#FF00D4"


def configure_paper_style() -> None:
    """Apply a compact journal-style Matplotlib configuration."""

    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 9.0,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def _plot_ring(ax, points: Sequence[Point], **kwargs) -> None:
    ring = close_ring(points)
    ax.plot([point[0] for point in ring], [point[1] for point in ring], **kwargs)


def draw_plan(
    ax,
    plan_segments: Sequence[Segment],
    outline_vertices: Sequence[Point],
    geometry: PlanGeometry,
    *,
    show_plan: bool = True,
    show_outline: bool = True,
    show_minimum_bounding_rectangle: bool = True,
    show_inertia_equivalent_rectangle: bool = True,
    show_centroid: bool = False,
) -> None:
    """Draw one plan with independently selectable manuscript-style layers."""

    if show_plan:
        for x1, y1, x2, y2 in plan_segments:
            ax.plot(
                (x1, x2),
                (y1, y2),
                color=PLAN_COLOR,
                linewidth=0.55,
                alpha=0.72,
                solid_capstyle="round",
                zorder=1,
            )
    if show_outline:
        _plot_ring(
            ax,
            outline_vertices,
            color=OUTLINE_COLOR,
            linewidth=1.45,
            solid_capstyle="round",
            zorder=4,
        )
    if show_minimum_bounding_rectangle:
        _plot_ring(
            ax,
            geometry.minimum_bounding_rectangle.corners,
            color=BOUNDING_COLOR,
            linewidth=1.35,
            linestyle="--",
            dash_capstyle="butt",
            zorder=5,
        )
    if show_inertia_equivalent_rectangle:
        _plot_ring(
            ax,
            geometry.inertia_equivalent_rectangle.corners,
            color=EQUIVALENT_COLOR,
            linewidth=1.15,
            linestyle="--",
            dash_capstyle="butt",
            zorder=6,
        )
    if show_centroid:
        ax.scatter(
            [geometry.section.centroid_x],
            [geometry.section.centroid_y],
            s=12,
            facecolor="white",
            edgecolor="black",
            linewidth=0.7,
            zorder=7,
        )

    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(0.08)
    ax.set_axis_off()


def figure_legend_handles():
    """Return line handles matching the manuscript-style geometry layers."""

    from matplotlib.lines import Line2D

    return [
        Line2D([0], [0], color=OUTLINE_COLOR, linewidth=1.6, label="Building outline"),
        Line2D(
            [0],
            [0],
            color=BOUNDING_COLOR,
            linewidth=1.4,
            linestyle="--",
            label="Minimum\nbounding rectangle",
        ),
        Line2D(
            [0],
            [0],
            color=EQUIVALENT_COLOR,
            linewidth=1.2,
            linestyle="--",
            label="Inertia-equivalent\nrectangle",
        ),
    ]

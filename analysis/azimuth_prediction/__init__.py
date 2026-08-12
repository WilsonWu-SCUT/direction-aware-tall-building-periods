"""Floor-plan geometry analysis for the public building database."""

from .geometry import (
    OrientedRectangle,
    PlanGeometry,
    SectionProperties,
    compute_plan_geometry,
    order_outline_segments,
    polygon_section_properties,
)

__all__ = [
    "OrientedRectangle",
    "PlanGeometry",
    "SectionProperties",
    "compute_plan_geometry",
    "order_outline_segments",
    "polygon_section_properties",
]

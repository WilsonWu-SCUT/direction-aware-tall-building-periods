"""Geometry calculations that do not depend on plotting or database code."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, isclose, radians, sin
from typing import Iterable, Sequence


Point = tuple[float, float]
Segment = tuple[float, float, float, float]


@dataclass(frozen=True)
class SectionProperties:
    """Area properties of a closed polygon about its centroidal axes."""

    area: float
    centroid_x: float
    centroid_y: float
    ix_centroid: float
    iy_centroid: float
    ixy_centroid: float


@dataclass(frozen=True)
class OrientedRectangle:
    """An oriented rectangle represented in the source coordinate system."""

    corners: tuple[Point, Point, Point, Point]
    length: float
    width: float
    area: float
    long_axis_deg: float


@dataclass(frozen=True)
class PlanGeometry:
    """Complete derived geometry for one building plan outline."""

    section: SectionProperties
    major_principal_moment: float
    minor_principal_moment: float
    transverse_azimuth_deg: float
    longitudinal_azimuth_deg: float
    transverse_effective_width: float
    longitudinal_effective_width: float
    minimum_bounding_rectangle: OrientedRectangle
    inertia_equivalent_rectangle: OrientedRectangle
    regularity_ratio: float
    plan_class: str


def _same_point(first: Point, second: Point, tolerance: float) -> bool:
    return (
        abs(first[0] - second[0]) <= tolerance
        and abs(first[1] - second[1]) <= tolerance
    )


def _point_key(point: Point, tolerance: float) -> tuple[int, int]:
    return (round(point[0] / tolerance), round(point[1] / tolerance))


def order_outline_segments(
    segments: Iterable[Segment], tolerance: float = 1.0e-6
) -> list[Point]:
    """Recover one ordered, closed polygon ring from unordered line segments.

    The returned vertex sequence does not repeat the first vertex at the end.
    Segment direction may be mixed. Disconnected rings and branched outlines are
    rejected because the source format is expected to contain one exterior ring.
    """

    cleaned: list[tuple[Point, Point]] = []
    for x1, y1, x2, y2 in segments:
        first = (float(x1), float(y1))
        second = (float(x2), float(y2))
        if not _same_point(first, second, tolerance):
            cleaned.append((first, second))
    if len(cleaned) < 3:
        raise ValueError("At least three nonzero outline segments are required.")

    adjacency: dict[tuple[int, int], list[tuple[int, Point]]] = defaultdict(list)
    for index, (first, second) in enumerate(cleaned):
        adjacency[_point_key(first, tolerance)].append((index, second))
        adjacency[_point_key(second, tolerance)].append((index, first))

    start = cleaned[0][0]
    current = start
    vertices = [start]
    unused = set(range(len(cleaned)))

    while unused:
        candidates = [
            candidate
            for candidate in adjacency.get(_point_key(current, tolerance), [])
            if candidate[0] in unused
        ]
        if not candidates:
            for index in sorted(unused):
                first, second = cleaned[index]
                if _same_point(current, first, tolerance):
                    candidates = [(index, second)]
                    break
                if _same_point(current, second, tolerance):
                    candidates = [(index, first)]
                    break
        if not candidates:
            raise ValueError("Outline segments do not form a connected ring.")

        index, next_point = min(candidates, key=lambda item: item[0])
        unused.remove(index)
        current = next_point

        if _same_point(current, start, tolerance):
            if unused:
                raise ValueError("Outline contains a disconnected ring or branch.")
            break
        vertices.append(current)

    if not _same_point(current, start, tolerance):
        raise ValueError("Outline segments do not form a closed ring.")
    if len(vertices) < 3:
        raise ValueError("The recovered outline has fewer than three vertices.")
    return vertices


def polygon_section_properties(vertices: Sequence[Point]) -> SectionProperties:
    """Compute polygon area, centroid, and centroidal second moments.

    The formulas are the closed-polygon expressions used in Section 4.1 of the
    manuscript. Clockwise and counterclockwise vertex orders are both accepted.
    """

    if len(vertices) < 3:
        raise ValueError("At least three polygon vertices are required.")

    area_twice = 0.0
    centroid_x_sum = 0.0
    centroid_y_sum = 0.0
    ix_origin_sum = 0.0
    iy_origin_sum = 0.0
    ixy_origin_sum = 0.0

    for index, (x1, y1) in enumerate(vertices):
        x2, y2 = vertices[(index + 1) % len(vertices)]
        cross = x1 * y2 - x2 * y1
        area_twice += cross
        centroid_x_sum += (x1 + x2) * cross
        centroid_y_sum += (y1 + y2) * cross
        ix_origin_sum += (y1 * y1 + y1 * y2 + y2 * y2) * cross
        iy_origin_sum += (x1 * x1 + x1 * x2 + x2 * x2) * cross
        ixy_origin_sum += (
            2.0 * x1 * y1
            + x1 * y2
            + x2 * y1
            + 2.0 * x2 * y2
        ) * cross

    if isclose(area_twice, 0.0, abs_tol=1.0e-14):
        raise ValueError("Polygon area is zero.")

    signed_area = 0.5 * area_twice
    area = abs(signed_area)
    centroid_x = centroid_x_sum / (3.0 * area_twice)
    centroid_y = centroid_y_sum / (3.0 * area_twice)

    orientation = 1.0 if signed_area > 0.0 else -1.0
    ix_origin = orientation * ix_origin_sum / 12.0
    iy_origin = orientation * iy_origin_sum / 12.0
    ixy_origin = orientation * ixy_origin_sum / 24.0

    ix_centroid = ix_origin - area * centroid_y * centroid_y
    iy_centroid = iy_origin - area * centroid_x * centroid_x
    ixy_centroid = ixy_origin - area * centroid_x * centroid_y

    scale = max(ix_origin, iy_origin, 1.0)
    if ix_centroid < 0.0 and abs(ix_centroid) <= 1.0e-12 * scale:
        ix_centroid = 0.0
    if iy_centroid < 0.0 and abs(iy_centroid) <= 1.0e-12 * scale:
        iy_centroid = 0.0
    if ix_centroid <= 0.0 or iy_centroid <= 0.0:
        raise ValueError("Polygon centroidal moments must be positive.")

    return SectionProperties(
        area=area,
        centroid_x=centroid_x,
        centroid_y=centroid_y,
        ix_centroid=ix_centroid,
        iy_centroid=iy_centroid,
        ixy_centroid=ixy_centroid,
    )


def convex_hull(points: Sequence[Point]) -> list[Point]:
    """Return the counterclockwise convex hull using the monotone-chain method."""

    unique = sorted(set((float(x), float(y)) for x, y in points))
    if len(unique) < 3:
        raise ValueError("At least three unique points are required for a hull.")

    def cross(origin: Point, first: Point, second: Point) -> float:
        return (first[0] - origin[0]) * (second[1] - origin[1]) - (
            first[1] - origin[1]
        ) * (second[0] - origin[0])

    lower: list[Point] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)

    upper: list[Point] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def minimum_area_bounding_rectangle(vertices: Sequence[Point]) -> OrientedRectangle:
    """Compute the minimum-area rectangle by scanning convex-hull edges."""

    hull = convex_hull(vertices)
    best: tuple[float, float, float, float, float, float] | None = None

    for index, first in enumerate(hull):
        second = hull[(index + 1) % len(hull)]
        dx = second[0] - first[0]
        dy = second[1] - first[1]
        edge_length = hypot(dx, dy)
        if edge_length == 0.0:
            continue
        ux, uy = dx / edge_length, dy / edge_length
        vx, vy = -uy, ux
        projected_u = [x * ux + y * uy for x, y in hull]
        projected_v = [x * vx + y * vy for x, y in hull]
        min_u, max_u = min(projected_u), max(projected_u)
        min_v, max_v = min(projected_v), max(projected_v)
        area = (max_u - min_u) * (max_v - min_v)
        angle = atan2(uy, ux)
        candidate = (area, angle, min_u, max_u, min_v, max_v)
        if best is None or area < best[0]:
            best = candidate

    if best is None:
        raise ValueError("Unable to compute a bounding rectangle.")

    area, angle, min_u, max_u, min_v, max_v = best
    ux, uy = cos(angle), sin(angle)
    vx, vy = -uy, ux

    def global_point(local_u: float, local_v: float) -> Point:
        return (
            local_u * ux + local_v * vx,
            local_u * uy + local_v * vy,
        )

    corners = (
        global_point(min_u, min_v),
        global_point(max_u, min_v),
        global_point(max_u, max_v),
        global_point(min_u, max_v),
    )
    side_u = max_u - min_u
    side_v = max_v - min_v
    if side_u >= side_v:
        length, width = side_u, side_v
        long_axis_deg = degrees(angle) % 180.0
    else:
        length, width = side_v, side_u
        long_axis_deg = (degrees(angle) + 90.0) % 180.0

    return OrientedRectangle(
        corners=corners,
        length=length,
        width=width,
        area=area,
        long_axis_deg=long_axis_deg,
    )


def _rectangle_from_axes(
    center: Point,
    transverse_width: float,
    longitudinal_width: float,
    transverse_azimuth_deg: float,
) -> OrientedRectangle:
    theta = radians(transverse_azimuth_deg)
    ux, uy = cos(theta), sin(theta)
    vx, vy = -uy, ux
    half_transverse = 0.5 * transverse_width
    half_longitudinal = 0.5 * longitudinal_width

    def transform(local_u: float, local_v: float) -> Point:
        return (
            center[0] + local_u * ux + local_v * vx,
            center[1] + local_u * uy + local_v * vy,
        )

    corners = (
        transform(-half_transverse, -half_longitudinal),
        transform(half_transverse, -half_longitudinal),
        transform(half_transverse, half_longitudinal),
        transform(-half_transverse, half_longitudinal),
    )
    if longitudinal_width >= transverse_width:
        length, width = longitudinal_width, transverse_width
        long_axis_deg = (transverse_azimuth_deg + 90.0) % 180.0
    else:
        length, width = transverse_width, longitudinal_width
        long_axis_deg = transverse_azimuth_deg % 180.0
    return OrientedRectangle(
        corners=corners,
        length=length,
        width=width,
        area=transverse_width * longitudinal_width,
        long_axis_deg=long_axis_deg,
    )


def compute_plan_geometry(
    vertices: Sequence[Point], regularity_threshold: float = 0.80
) -> PlanGeometry:
    """Compute Section 4.1 metrics and both rectangles for one plan."""

    section = polygon_section_properties(vertices)
    average = 0.5 * (section.ix_centroid + section.iy_centroid)
    radius = hypot(
        0.5 * (section.ix_centroid - section.iy_centroid),
        section.ixy_centroid,
    )
    major = average + radius
    minor = average - radius
    if minor <= 0.0:
        raise ValueError("The minor principal moment must be positive.")

    if abs(section.ixy_centroid) <= 1.0e-14 * max(major, 1.0):
        transverse_azimuth = 0.0 if section.ix_centroid >= section.iy_centroid else 90.0
    else:
        transverse_azimuth = degrees(
            atan2(
                section.ix_centroid - major,
                section.ixy_centroid,
            )
        ) % 180.0
    longitudinal_azimuth = (transverse_azimuth + 90.0) % 180.0

    transverse_width = (144.0 * minor**3 / major) ** 0.125
    longitudinal_width = (144.0 * major**3 / minor) ** 0.125
    equivalent = _rectangle_from_axes(
        (section.centroid_x, section.centroid_y),
        transverse_width,
        longitudinal_width,
        transverse_azimuth,
    )
    bounding = minimum_area_bounding_rectangle(vertices)
    regularity_ratio = section.area / bounding.area
    plan_class = "regular" if regularity_ratio >= regularity_threshold else "irregular"

    return PlanGeometry(
        section=section,
        major_principal_moment=major,
        minor_principal_moment=minor,
        transverse_azimuth_deg=transverse_azimuth,
        longitudinal_azimuth_deg=longitudinal_azimuth,
        transverse_effective_width=transverse_width,
        longitudinal_effective_width=longitudinal_width,
        minimum_bounding_rectangle=bounding,
        inertia_equivalent_rectangle=equivalent,
        regularity_ratio=regularity_ratio,
        plan_class=plan_class,
    )


def close_ring(points: Sequence[Point]) -> list[Point]:
    """Return a copy of a point sequence with its first point appended."""

    if not points:
        return []
    return [*points, points[0]]

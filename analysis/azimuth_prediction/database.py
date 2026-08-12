"""Read-only access helpers for the public floor-plan geometry database."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .geometry import Point, Segment


@dataclass(frozen=True)
class PlanRecord:
    model_id: str
    building_function: str | None
    structural_system_code: str | None
    building_height_m: float
    transverse_effective_width_m: float
    longitudinal_effective_width_m: float
    transverse_period_s: float
    longitudinal_period_s: float
    regularity_ratio: float
    plan_class: str
    plan_segment_count: int
    outline_vertex_count: int


@contextmanager
def connect_readonly(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open a SQLite database in read-only mode with named-column rows."""

    path = Path(database_path).resolve()
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def list_models(database_path: str | Path) -> list[PlanRecord]:
    """Return all models ordered by the identifiers used in the period database."""

    with connect_readonly(database_path) as connection:
        rows = connection.execute(
            """
            SELECT model_id, building_function, structural_system_code,
                   building_height_m, transverse_effective_width_m,
                   longitudinal_effective_width_m, transverse_period_s,
                   longitudinal_period_s, regularity_ratio, plan_class,
                   plan_segment_count, outline_vertex_count
            FROM plan_geometry_readable
            ORDER BY structural_system_code, model_id
            """
        ).fetchall()
    return [PlanRecord(**dict(row)) for row in rows]


def resolve_model_id(
    connection: sqlite3.Connection,
    model_id: str,
) -> tuple[int, PlanRecord]:
    """Resolve a period-database model identifier to one plan record."""

    row = connection.execute(
        """
        SELECT model_pk, model_id, building_function, structural_system_code,
               building_height_m,
               transverse_effective_width_m, longitudinal_effective_width_m,
               transverse_period_s, longitudinal_period_s, regularity_ratio,
               plan_class, plan_segment_count, outline_vertex_count
        FROM plan_geometry_readable
        WHERE model_id = ?
        """,
        (model_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"Unknown model identifier: {model_id}")
    values = dict(row)
    model_pk = values.pop("model_pk")
    return model_pk, PlanRecord(**values)


def load_plan(
    database_path: str | Path,
    model_id: str,
) -> tuple[PlanRecord, list[Segment], list[Point]]:
    """Load model metadata, structural plan segments, and ordered outline vertices."""

    with connect_readonly(database_path) as connection:
        model_pk, record = resolve_model_id(connection, model_id)
        segment_rows = connection.execute(
            """
            SELECT x1_m, y1_m, x2_m, y2_m
            FROM plan_segments
            WHERE model_pk = ?
            ORDER BY segment_index
            """,
            (model_pk,),
        ).fetchall()
        vertex_rows = connection.execute(
            """
            SELECT x_m, y_m
            FROM outline_vertices
            WHERE model_pk = ?
            ORDER BY vertex_index
            """,
            (model_pk,),
        ).fetchall()
    segments = [tuple(row) for row in segment_rows]
    vertices = [tuple(row) for row in vertex_rows]
    return record, segments, vertices

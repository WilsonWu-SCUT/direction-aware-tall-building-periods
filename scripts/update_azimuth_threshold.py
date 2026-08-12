#!/usr/bin/env python3
"""Apply the documented plan-regularity threshold to the azimuth database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DEFAULT_DATABASE = Path("data/azimuth_prediction/building_plan_geometry.sqlite")
REGULARITY_THRESHOLD = 0.80


def update_threshold(database_path: Path) -> tuple[int, int]:
    connection = sqlite3.connect(database_path)
    try:
        with connection:
            connection.execute(
                """
                UPDATE geometry_metrics
                SET plan_class = CASE
                    WHEN regularity_ratio >= ? THEN 'regular'
                    ELSE 'irregular'
                END
                """,
                (REGULARITY_THRESHOLD,),
            )
            connection.execute(
                """
                UPDATE dataset_metadata
                SET metadata_value = ?
                WHERE metadata_key = 'regularity_threshold'
                """,
                (f"{REGULARITY_THRESHOLD:.2f}",),
            )
            connection.execute(
                """
                UPDATE dataset_metadata
                SET metadata_value = '3'
                WHERE metadata_key = 'schema_version'
                """
            )
            connection.execute("PRAGMA user_version = 3")
        counts = dict(
            connection.execute(
                "SELECT plan_class, COUNT(*) FROM geometry_metrics GROUP BY plan_class"
            )
        )
        return int(counts.get("regular", 0)), int(counts.get("irregular", 0))
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", nargs="?", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    regular, irregular = update_threshold(args.database)
    print(
        f"Updated {args.database}: threshold={REGULARITY_THRESHOLD:.2f}, "
        f"regular={regular}, irregular={irregular}"
    )


if __name__ == "__main__":
    main()

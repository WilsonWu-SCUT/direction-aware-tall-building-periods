"""Validate the public floor-plan geometry SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


EXPECTED_MODELS = 482
REGULARITY_THRESHOLD = 0.80
SENSITIVE_TOKENS = (
    "phone",
    "time_series",
    "project_name",
    "source_path",
    "public_model_id",
    "period_model_id",
    "pairing_status",
)


def scalar(connection: sqlite3.Connection, query: str) -> int | float | str:
    return connection.execute(query).fetchone()[0]


def validate(database_path: Path, period_database_path: Path) -> dict[str, int | float]:
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    integrity = scalar(connection, "PRAGMA integrity_check")
    if integrity != "ok":
        raise AssertionError(f"SQLite integrity check failed: {integrity}")
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise AssertionError(f"Foreign-key violations: {foreign_key_errors[:5]}")

    counts = {
        "models": scalar(connection, "SELECT COUNT(*) FROM model_plans"),
        "plan_segments": scalar(connection, "SELECT COUNT(*) FROM plan_segments"),
        "outline_vertices": scalar(connection, "SELECT COUNT(*) FROM outline_vertices"),
        "geometry_metrics": scalar(connection, "SELECT COUNT(*) FROM geometry_metrics"),
        "rectangle_vertices": scalar(
            connection, "SELECT COUNT(*) FROM derived_rectangle_vertices"
        ),
        "source_summaries": scalar(
            connection, "SELECT COUNT(*) FROM source_file_summary"
        ),
        "regular": scalar(
            connection,
            "SELECT COUNT(*) FROM geometry_metrics WHERE plan_class = 'regular'",
        ),
        "irregular": scalar(
            connection,
            "SELECT COUNT(*) FROM geometry_metrics WHERE plan_class = 'irregular'",
        ),
    }
    if counts["models"] != EXPECTED_MODELS:
        raise AssertionError(f"Expected {EXPECTED_MODELS} models, found {counts['models']}.")
    if counts["geometry_metrics"] != EXPECTED_MODELS:
        raise AssertionError("Every model must have one geometry-metrics record.")
    if counts["source_summaries"] != EXPECTED_MODELS:
        raise AssertionError("Every model must have one source-file summary.")
    if counts["rectangle_vertices"] != EXPECTED_MODELS * 2 * 4:
        raise AssertionError("Every model must have four vertices for both rectangles.")
    if counts["regular"] + counts["irregular"] != EXPECTED_MODELS:
        raise AssertionError("Plan classifications do not cover all models.")

    classification_errors = scalar(
        connection,
        f"""
        SELECT COUNT(*)
        FROM geometry_metrics
        WHERE plan_class != CASE
            WHEN regularity_ratio >= {REGULARITY_THRESHOLD} THEN 'regular'
            ELSE 'irregular'
        END
        """,
    )
    if classification_errors:
        raise AssertionError(
            f"Found {classification_errors} classifications inconsistent with "
            f"the {REGULARITY_THRESHOLD:.2f} threshold."
        )

    stored_threshold = float(
        connection.execute(
            "SELECT metadata_value FROM dataset_metadata WHERE metadata_key = 'regularity_threshold'"
        ).fetchone()[0]
    )
    if stored_threshold != REGULARITY_THRESHOLD:
        raise AssertionError(
            f"Database metadata threshold is {stored_threshold}, expected {REGULARITY_THRESHOLD}."
        )

    invalid_geometry = scalar(
        connection,
        """
        SELECT COUNT(*)
        FROM geometry_metrics
        WHERE area_m2 <= 0
           OR minor_principal_moment_m4 <= 0
           OR major_principal_moment_m4 < minor_principal_moment_m4
           OR regularity_ratio <= 0
           OR regularity_ratio > 1.000001
           OR ABS(longitudinal_azimuth_deg -
                  CASE
                      WHEN transverse_azimuth_deg >= 90.0
                      THEN transverse_azimuth_deg - 90.0
                      ELSE transverse_azimuth_deg + 90.0
                  END) > 1.0e-8
        """,
    )
    if invalid_geometry:
        raise AssertionError(f"Found {invalid_geometry} invalid geometry records.")

    schema_text = " ".join(
        row[0] or ""
        for row in connection.execute(
            "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
        )
    ).lower()
    leaked_tokens = [token for token in SENSITIVE_TOKENS if token in schema_text]
    if leaked_tokens:
        raise AssertionError(f"Sensitive schema tokens found: {leaked_tokens}")

    plan_ids = {
        row[0] for row in connection.execute("SELECT model_id FROM model_plans")
    }
    period_connection = sqlite3.connect(period_database_path)
    period_ids = {
        row[0] for row in period_connection.execute("SELECT model_id FROM period_records")
    }
    period_connection.close()
    missing_period_ids = sorted(plan_ids - period_ids)
    if missing_period_ids:
        raise AssertionError(
            f"Plan identifiers missing from period database: {missing_period_ids[:10]}"
        )
    counts["period_labels_verified"] = len(plan_ids)

    counts["minimum_regularity_ratio"] = scalar(
        connection, "SELECT MIN(regularity_ratio) FROM geometry_metrics"
    )
    counts["maximum_regularity_ratio"] = scalar(
        connection, "SELECT MAX(regularity_ratio) FROM geometry_metrics"
    )
    connection.close()
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "database",
        type=Path,
        nargs="?",
        default=Path("data/azimuth_prediction/building_plan_geometry.sqlite"),
    )
    parser.add_argument(
        "--period-database",
        type=Path,
        default=Path("data/period_prediction/tall_building_periods.sqlite"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = validate(args.database, args.period_database)
    details = ", ".join(f"{key}={value}" for key, value in results.items())
    print(f"Plan database validation passed: {details}")


if __name__ == "__main__":
    main()

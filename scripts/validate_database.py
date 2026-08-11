#!/usr/bin/env python3
"""Validate the tall-building period database and repository text policy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "tall_building_periods.csv"
DEFAULT_DATABASE = ROOT / "data" / "tall_building_periods.sqlite"

EXPECTED_SYSTEM_COUNTS = {"SW": 818, "FSW": 181, "FT": 334}
EXPECTED_FUNCTION_COUNTS = {"Residential": 695, "Office": 422, "Hotel": 216}
EXPECTED_INTENSITY_COUNTS = {6: 391, 7: 811, 8: 131}
EXPECTED_RANGES = {
    "building_height_m": (80.0, 200.0),
    "transverse_effective_width_m": (10.0, 53.0),
    "longitudinal_effective_width_m": (22.0, 88.0),
    "transverse_period_s": (1.32, 5.94),
    "longitudinal_period_s": (1.23, 5.22),
}
TEXT_EXTENSIONS = {".md", ".py", ".sql", ".csv", ".txt", ".tex", ".yml", ".yaml", ".json", ".cff"}
CJK_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_records(path: Path) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            rows.append(
                (
                    row["model_id"],
                    row["structural_system_code"],
                    int(row["source_row"]),
                    float(row["building_height_m"]),
                    float(row["transverse_effective_width_m"]),
                    float(row["longitudinal_effective_width_m"]),
                    row["building_function"],
                    int(row["seismic_intensity_degree"]),
                    float(row["transverse_period_s"]),
                    float(row["longitudinal_period_s"]),
                )
            )
    return rows


def validate_english_only(root: Path) -> None:
    violations: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8")
        match = CJK_PATTERN.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            violations.append(f"{path.relative_to(root)}:{line}")
    if violations:
        raise AssertionError(
            "CJK characters are not allowed in repository text files: "
            + ", ".join(violations)
        )


def validate_database(database_path: Path, csv_path: Path) -> None:
    source_rows = csv_records(csv_path)
    if len(source_rows) != 1333:
        raise AssertionError(f"CSV record count is {len(source_rows)}, not 1,333.")

    connection = sqlite3.connect(database_path)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise AssertionError(f"SQLite integrity check failed: {integrity}")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise AssertionError("SQLite foreign-key check failed.")

        database_rows = connection.execute(
            """
            SELECT
                model_id,
                structural_system_code,
                source_row,
                building_height_m,
                transverse_effective_width_m,
                longitudinal_effective_width_m,
                building_function,
                seismic_intensity_degree,
                transverse_period_s,
                longitudinal_period_s
            FROM period_records
            ORDER BY model_id
            """
        ).fetchall()
        if sorted(source_rows) != database_rows:
            raise AssertionError("CSV and SQLite records are not identical.")

        system_counts = dict(
            connection.execute(
                """
                SELECT structural_system_code, COUNT(*)
                FROM period_records
                GROUP BY structural_system_code
                """
            )
        )
        if system_counts != EXPECTED_SYSTEM_COUNTS:
            raise AssertionError(f"Unexpected system counts: {system_counts}")

        function_counts = Counter(row[6] for row in database_rows)
        if dict(function_counts) != EXPECTED_FUNCTION_COUNTS:
            raise AssertionError(f"Unexpected function counts: {function_counts}")

        intensity_counts = Counter(row[7] for row in database_rows)
        if dict(intensity_counts) != EXPECTED_INTENSITY_COUNTS:
            raise AssertionError(f"Unexpected intensity counts: {intensity_counts}")

        range_columns = {
            "building_height_m": 3,
            "transverse_effective_width_m": 4,
            "longitudinal_effective_width_m": 5,
            "transverse_period_s": 8,
            "longitudinal_period_s": 9,
        }
        for column_name, tuple_index in range_columns.items():
            values = [row[tuple_index] for row in database_rows]
            observed = (min(values), max(values))
            if observed != EXPECTED_RANGES[column_name]:
                raise AssertionError(
                    f"Unexpected range for {column_name}: {observed}"
                )

        metadata = dict(connection.execute("SELECT * FROM dataset_metadata"))
        if metadata.get("record_count") != "1333":
            raise AssertionError("Metadata record count is incorrect.")
        if metadata.get("source_csv_sha256") != sha256_file(csv_path):
            raise AssertionError("CSV checksum does not match database metadata.")
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args()

    validate_database(args.database, args.csv)
    validate_english_only(args.project_root)
    print("Validation passed: 1,333 records, schema, checksum, and language policy.")


if __name__ == "__main__":
    main()

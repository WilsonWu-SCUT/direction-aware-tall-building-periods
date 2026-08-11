#!/usr/bin/env python3
"""Build the SQLite period database from the canonical CSV file."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "tall_building_periods.csv"
DEFAULT_SCHEMA = ROOT / "schema" / "schema.sql"
DEFAULT_DATABASE = ROOT / "data" / "tall_building_periods.sqlite"

SYSTEMS = {
    "SW": ("Shear wall", "Table S1"),
    "FSW": ("Frame-shear wall", "Table S2"),
    "FT": ("Frame-tube", "Table S3"),
}

EXPECTED_FIELDS = [
    "model_id",
    "structural_system_code",
    "structural_system",
    "source_table",
    "source_row",
    "building_height_m",
    "transverse_effective_width_m",
    "longitudinal_effective_width_m",
    "building_function",
    "seismic_intensity_degree",
    "transverse_period_s",
    "longitudinal_period_s",
]

DATA_DICTIONARY = [
    ("period_records", "model_id", "TEXT", None, "Anonymized model identifier."),
    ("period_records", "structural_system_code", "TEXT", None, "Structural-system code."),
    ("period_records", "source_row", "INTEGER", None, "One-based data-row number in the source table."),
    ("period_records", "building_height_m", "REAL", "m", "Total building height."),
    ("period_records", "transverse_effective_width_m", "REAL", "m", "Effective width in the transverse direction."),
    ("period_records", "longitudinal_effective_width_m", "REAL", "m", "Effective width in the longitudinal direction."),
    ("period_records", "building_function", "TEXT", None, "Primary building-use category."),
    ("period_records", "seismic_intensity_degree", "INTEGER", "degree", "Chinese seismic design intensity category."),
    ("period_records", "transverse_period_s", "REAL", "s", "Translational period in the transverse direction."),
    ("period_records", "longitudinal_period_s", "REAL", "s", "Translational period in the longitudinal direction."),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_csv(path: Path) -> list[tuple[object, ...]]:
    """Load and validate canonical CSV records for SQLite insertion."""
    records: list[tuple[object, ...]] = []
    seen_ids: set[str] = set()
    seen_source_rows: set[tuple[str, int]] = set()

    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_FIELDS:
            raise ValueError(
                f"Unexpected CSV fields. Expected {EXPECTED_FIELDS!r}, "
                f"found {reader.fieldnames!r}."
            )

        for line_number, row in enumerate(reader, start=2):
            model_id = row["model_id"]
            code = row["structural_system_code"]
            if code not in SYSTEMS:
                raise ValueError(f"Unknown structural system on line {line_number}: {code}")
            expected_name, expected_table = SYSTEMS[code]
            if row["structural_system"] != expected_name:
                raise ValueError(f"Structural-system name mismatch on line {line_number}.")
            if row["source_table"] != expected_table:
                raise ValueError(f"Source-table mismatch on line {line_number}.")
            if not model_id.startswith(f"{code}-"):
                raise ValueError(f"Model identifier prefix mismatch on line {line_number}.")
            if model_id in seen_ids:
                raise ValueError(f"Duplicate model identifier on line {line_number}: {model_id}")

            source_row = int(row["source_row"])
            source_key = (code, source_row)
            if source_key in seen_source_rows:
                raise ValueError(f"Duplicate source row on line {line_number}: {source_key}")

            building_function = row["building_function"]
            if building_function not in {"Residential", "Office", "Hotel"}:
                raise ValueError(f"Unknown building function on line {line_number}.")
            intensity = int(row["seismic_intensity_degree"])
            if intensity not in {6, 7, 8}:
                raise ValueError(f"Invalid seismic intensity on line {line_number}.")

            numeric_values = [
                float(row["building_height_m"]),
                float(row["transverse_effective_width_m"]),
                float(row["longitudinal_effective_width_m"]),
                float(row["transverse_period_s"]),
                float(row["longitudinal_period_s"]),
            ]
            if any(value <= 0 for value in numeric_values):
                raise ValueError(f"Non-positive numeric value on line {line_number}.")

            seen_ids.add(model_id)
            seen_source_rows.add(source_key)
            records.append(
                (
                    model_id,
                    code,
                    source_row,
                    numeric_values[0],
                    numeric_values[1],
                    numeric_values[2],
                    building_function,
                    intensity,
                    numeric_values[3],
                    numeric_values[4],
                )
            )

    if len(records) != 1333:
        raise ValueError(f"Expected 1,333 records, found {len(records)}.")
    return records


def build_database(csv_path: Path, schema_path: Path, output_path: Path) -> None:
    records = load_csv(csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    if temporary_path.exists():
        temporary_path.unlink()

    connection = sqlite3.connect(temporary_path)
    try:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        connection.executemany(
            """
            INSERT INTO structural_systems (
                structural_system_code, structural_system, source_table
            ) VALUES (?, ?, ?)
            """,
            [(code, name, table) for code, (name, table) in SYSTEMS.items()],
        )
        connection.executemany(
            """
            INSERT INTO period_records (
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )

        metadata = {
            "dataset_title": "Direction-Aware Tall-Building Period Database",
            "dataset_version": "0.1.0",
            "schema_version": "1",
            "record_count": str(len(records)),
            "source_document": "Supplementary.docx",
            "source_tables": "Table S1; Table S2; Table S3",
            "source_csv": csv_path.name,
            "source_csv_sha256": sha256_file(csv_path),
            "paper_title": "Direction-Aware Period Prediction for Seismic Risk Assessment and Application to an Urban Tall Building Portfolio in China",
            "code_license": "MIT",
            "data_license": "CC BY 4.0",
        }
        connection.executemany(
            "INSERT INTO dataset_metadata (metadata_key, metadata_value) VALUES (?, ?)",
            sorted(metadata.items()),
        )
        connection.executemany(
            """
            INSERT INTO data_dictionary (
                table_name, column_name, sqlite_type, unit, description
            ) VALUES (?, ?, ?, ?, ?)
            """,
            DATA_DICTIONARY,
        )
        connection.commit()

        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("SQLite foreign-key validation failed.")
        connection.execute("VACUUM")
    finally:
        connection.close()

    os.replace(temporary_path, output_path)
    print(f"Built {output_path} with {len(records):,} records.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    build_database(args.csv, args.schema, args.output)


if __name__ == "__main__":
    main()


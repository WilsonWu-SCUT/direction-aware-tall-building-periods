# Period-prediction database

## Files

| File | Purpose |
|---|---|
| `tall_building_periods.sqlite` | Canonical analysis database used by default |
| `tall_building_periods.csv` | Human-readable source used to rebuild SQLite |
| `../../schema/period_prediction_schema.sql` | Portable SQLite schema |

The database contains 1,333 anonymized models: 818 shear-wall (`SW`), 181
frame-shear-wall (`FSW`), and 334 frame-tube (`FT`) buildings.

## Tables and views

| Object | Description |
|---|---|
| `period_records` | One row per building, keyed by `model_id` |
| `structural_systems` | System codes, full names, and source tables |
| `data_dictionary` | Machine-readable field definitions and units |
| `dataset_metadata` | Version, provenance, count, and checksum metadata |
| `period_records_readable` | Joined view with readable system names |

## Main fields

| Field | Unit | Meaning |
|---|---|---|
| `model_id` | - | Stable anonymized identifier |
| `structural_system_code` | - | `SW`, `FSW`, or `FT` |
| `building_height_m` | m | Building height |
| `transverse_effective_width_m` | m | Transverse effective width |
| `longitudinal_effective_width_m` | m | Longitudinal effective width |
| `building_function` | - | Residential, Office, or Hotel |
| `seismic_intensity_degree` | degree | 6, 7, or 8 |
| `transverse_period_s` | s | Transverse translational period |
| `longitudinal_period_s` | s | Longitudinal translational period |

## Query example

```python
import sqlite3

connection = sqlite3.connect(
    "data/period_prediction/tall_building_periods.sqlite"
)
rows = connection.execute(
    """
    SELECT model_id, structural_system, building_height_m,
           transverse_period_s, longitudinal_period_s
    FROM period_records_readable
    WHERE seismic_intensity_degree = 8
    ORDER BY building_height_m
    LIMIT 10
    """
).fetchall()
```

## Build and validate

```bash
python scripts/build_period_database.py
python scripts/validate_period_database.py
```

The builder uses the CSV and SQL schema to create the SQLite file atomically.
The validator checks counts, ranges, category values, checksums, schema
integrity, and CSV/SQLite agreement.

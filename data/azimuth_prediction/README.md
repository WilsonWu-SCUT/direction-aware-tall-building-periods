# Azimuth-prediction database

## File and scope

`building_plan_geometry.sqlite` contains normalized structural plans, ordered
exterior outlines, and derived geometry linked by `model_id` to the period
database. The schema is
[`../../schema/azimuth_prediction_schema.sql`](../../schema/azimuth_prediction_schema.sql).

Coordinates are stored in metres, areas in square metres, and second moments
in fourth-power metres. Private project names, phone numbers, time-series keys,
directory names, and source paths are excluded.

## Tables and views

| Object | Description |
|---|---|
| `model_plans` | Linked model metadata and reported widths/periods |
| `plan_segments` | Standard-story structural line segments |
| `outline_vertices` | Ordered exterior polygon vertices |
| `geometry_metrics` | Area, inertias, azimuths, rectangles, and regularity |
| `derived_rectangle_vertices` | Corners of bounding and equivalent rectangles |
| `source_file_summary` | Counts, mesh summaries, and checksums |
| `dataset_metadata` | Units, version, threshold, privacy, and model count |
| `plan_geometry_readable` | Joined model and geometry view |

## Regularity classification

```text
eta_A = area_m2 / mbr_area_m2
```

The database uses the corrected threshold `eta_A = 0.80`:

- regular: `eta_A >= 0.80`;
- irregular: `eta_A < 0.80`.

## Query example

```python
import sqlite3

connection = sqlite3.connect(
    "data/azimuth_prediction/building_plan_geometry.sqlite"
)
rows = connection.execute(
    """
    SELECT model_id, regularity_ratio, plan_class,
           transverse_azimuth_deg, longitudinal_azimuth_deg
    FROM plan_geometry_readable
    ORDER BY regularity_ratio
    LIMIT 10
    """
).fetchall()
```

## Consume and validate

```bash
python scripts/plot_azimuth_prediction.py --model-id SW-701
python scripts/generate_azimuth_examples.py
python scripts/validate_azimuth_database.py
```

The Python geometry implementation can recompute the reported azimuths,
effective rectangles, and regularity metrics from the stored outline vertices.
The public database therefore contains everything needed by the included
azimuth analysis and plotting workflows.

# Data Dictionary

## Primary dataset

The canonical CSV contains one row per anonymized building model. The SQLite table `period_records` stores the normalized version of the same records. The view `period_records_readable` adds the full structural-system name and source-table label.

| Field | SQLite type | Unit | Description | Constraint |
|---|---|---|---|---|
| `model_id` | TEXT | - | Anonymized model identifier from the supplementary table. | Primary key; prefix must match the structural-system code. |
| `structural_system_code` | TEXT | - | Abbreviated lateral force-resisting system. | One of `SW`, `FSW`, or `FT`. |
| `structural_system` | TEXT | - | Full structural-system name. | Available in the CSV and readable SQLite view. |
| `source_table` | TEXT | - | Supplementary table from which the record was extracted. | One of `Table S1`, `Table S2`, or `Table S3`. |
| `source_row` | INTEGER | - | One-based data-row number within the supplementary table, excluding the header. | Positive integer; unique within each structural system. |
| `building_height_m` | REAL | m | Total building height. | Positive; observed range is 80-200 m. |
| `transverse_effective_width_m` | REAL | m | Effective building width in the transverse direction. | Positive; observed range is 10-53 m. |
| `longitudinal_effective_width_m` | REAL | m | Effective building width in the longitudinal direction. | Positive; observed range is 22-88 m. |
| `building_function` | TEXT | - | Primary building-use category. | One of `Residential`, `Office`, or `Hotel`. |
| `seismic_intensity_degree` | INTEGER | degree | Chinese seismic design intensity category reported in the source tables. | One of 6, 7, or 8. |
| `transverse_period_s` | REAL | s | Translational period in the transverse direction. | Positive; observed range is 1.32-5.94 s. |
| `longitudinal_period_s` | REAL | s | Translational period in the longitudinal direction. | Positive; observed range is 1.23-5.22 s. |

## Structural-system codes

| Code | Structural system | Source table | Records |
|---|---|---|---:|
| `SW` | Shear wall | Table S1 | 818 |
| `FSW` | Frame-shear wall | Table S2 | 181 |
| `FT` | Frame-tube | Table S3 | 334 |

## Direction convention

The terms `transverse` and `longitudinal` follow the direction labels used in the supplementary tables. Effective width and translational period must be paired within the same direction.

## Missing values

The source tables contain no missing values in the published fields. SQLite columns are therefore declared `NOT NULL`.

## Precision

The CSV preserves the numeric precision shown in the supplementary tables. SQLite stores measurements using the `REAL` type. The CSV remains the canonical text representation when display precision matters.


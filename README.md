# Direction-Aware Tall-Building Period Database

This repository accompanies the study *Direction-Aware Period Prediction for Seismic Risk Assessment and Application to an Urban Tall Building Portfolio in China*.

The current release contains the translational-period database for 1,333 anonymized tall-building models derived from real engineering projects in China. The records cover building heights from 80 m to 200 m and three structural-system categories.

## Repository status

This is the initial database release. Regression and translational-azimuth identification code will be added in subsequent repository updates.

## Contents

```text
data/
  tall_building_periods.csv       Canonical, human-readable source data
  tall_building_periods.sqlite    Portable SQLite database
docs/
  data_dictionary.md              Field definitions, units, and constraints
schema/
  schema.sql                      SQLite schema
scripts/
  build_database.py               Rebuild the SQLite database from CSV
  extract_supplementary.py        Recreate the CSV from the Word supplement
  validate_database.py            Validate data, schema, and language policy
analysis/section_4_2/
  regression.py                   Regression definitions and fit functions
  run_analysis.py                 Tables and publication-style figures
results/section_4_2/
  figures/                        Fig. 11 and full-data Fig. 13 in PNG/PDF
  tables/                         CSV, Markdown, and LaTeX statistical tables
  data/                           Full-data directional predictions
DATA_LICENSE.md                   CC BY 4.0 notice for database content
LICENSE                           MIT License for repository code
requirements.txt                  Analysis and plotting dependencies
requirements-dev.txt              Optional DOCX-extraction dependency
```

## Dataset summary

| Structural system | Code | Source table | Records |
|---|---:|---:|---:|
| Shear wall | SW | Table S1 | 818 |
| Frame-shear wall | FSW | Table S2 | 181 |
| Frame-tube | FT | Table S3 | 334 |
| **Total** |  |  | **1,333** |

Each record provides:

- building height;
- transverse and longitudinal effective widths;
- building function;
- seismic design intensity degree; and
- transverse and longitudinal translational periods.

The model identifiers are anonymized and preserve the identifiers used in the supplementary tables.

## Quick start

SQLite is serverless and is included with Python. The database can be queried directly:

```python
import sqlite3

connection = sqlite3.connect("data/tall_building_periods.sqlite")
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

for row in rows:
    print(row)
```

Example command-line query:

```bash
sqlite3 data/tall_building_periods.sqlite \
  "SELECT structural_system, COUNT(*) FROM period_records_readable GROUP BY structural_system;"
```

## Rebuild the database

The database build uses only the Python standard library:

```bash
python scripts/build_database.py
```

To regenerate the canonical CSV from the supplementary Word document:

```bash
python -m pip install -r requirements-dev.txt
python scripts/extract_supplementary.py path/to/Supplementary.docx
python scripts/build_database.py
```

## Validation

Run the complete validation suite:

```bash
python scripts/validate_database.py
```

The validation checks record counts, categories, numeric ranges, foreign keys, SQLite integrity, CSV-to-database equality, the source checksum, and the repository's English-only text policy.

## Section 4.2 regression analysis

Install the analysis dependencies and run all Section 4.2 analyses except fold cross-validation:

```bash
python -m pip install -r requirements.txt
python -m analysis.section_4_2.run_analysis
python -m unittest tests.test_section_4_2
```

The workflow creates:

- the unconstrained regression table corresponding to Table 3;
- the constrained full-database regression table corresponding to Table 4;
- constrained models without effective width corresponding to Table 5;
- a coefficient-contour figure corresponding to Fig. 11; and
- a predicted-versus-numerical period figure adapted from Fig. 13 using direct full-database fits instead of out-of-fold predictions.

Method definitions and reproduction notes are provided in `docs/section_4_2_regression.md`.

## Data provenance

The canonical CSV was transcribed programmatically from Tables S1-S3 of the paper's supplementary document. No project names, addresses, coordinates, owner names, or other direct project identifiers are included.

## Citation

Please cite the associated paper and the archived data release. Formal journal and DOI metadata will be added after publication and repository archiving.

## Licenses

- Repository code is released under the MIT License in `LICENSE`.
- Database content and the canonical CSV are released under CC BY 4.0 as described in `DATA_LICENSE.md`.

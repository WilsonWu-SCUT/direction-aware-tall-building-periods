# Period-prediction analysis

## Purpose

This workflow fits direction-aware translational-period models to the 1,333
building records in
[`data/period_prediction/tall_building_periods.sqlite`](../../data/period_prediction/README.md).
Each building contributes one transverse and one longitudinal observation, for
2,666 directional observations in total.

The default entry point reads SQLite directly. CSV input remains supported for
auditing and database rebuilding.

## Main results

![Constrained coefficient contours](../../results/period_prediction/figures/fig_11_constrained_contours.png)

![Full-data period predictions](../../results/period_prediction/figures/fig_13_full_data_predictions.png)

Generated tables:

- [Unconstrained regression](../../results/period_prediction/tables/table_3_unconstrained.md)
- [Constrained regression](../../results/period_prediction/tables/table_4_constrained.md)
- [Models without effective width](../../results/period_prediction/tables/table_5_no_width.md)
- [Full-data prediction metrics](../../results/period_prediction/tables/fig_13_full_data_metrics.md)

## Run

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m analysis.period_prediction.run_analysis
```

The command reads
`data/period_prediction/tall_building_periods.sqlite` and writes figures,
tables, and predictions to `results/period_prediction/`.

Useful options:

```bash
python -m analysis.period_prediction.run_analysis --skip-figures
python -m analysis.period_prediction.run_analysis --dpi 300
python -m analysis.period_prediction.run_analysis --data path/to/database.sqlite
python -m analysis.period_prediction.run_analysis --data path/to/data.csv
python -m analysis.period_prediction.run_analysis --output path/to/results
```

## Model definition

The unconstrained model is fitted after logarithmic linearization:

```text
ln(T) = ln(alpha_0) + alpha_H ln(H) - alpha_B ln(B)
```

The constrained form is:

```text
T = alpha_0 (H / B^alpha_B)^alpha_H
```

The fixed exponents are:

| Structural-system group | `alpha_B` | `alpha_H` |
|---|---:|---:|
| Non-Framed Tube (`SW`, `FSW`) | 0.2 | 1.0 |
| Framed Tube (`FT`) | 0.2 | 1.1 |

Seismic intensities 6 and 7 form the Low-Intensity group; intensity 8 forms
the High-Intensity group.

## Metrics and outputs

The workflow reports original-scale `R_squared`, RMSE in seconds, mean relative
error, RMS log-residual dispersion, and the degree-of-freedom-adjusted Eq. (23)
dispersion. `full_data_predictions.csv` retains model identifiers and both
directions for auditing.

The included Fig. 13 is a complete-database fit, not pooled out-of-fold
prediction. Cross-validation outputs are intentionally excluded from this
public workflow.

## Verify

```bash
python scripts/validate_period_database.py
python -m unittest tests.test_period_prediction
```

The tests verify that SQLite and CSV produce identical observations, reproduce
the published regression coefficients within the released precision, and
preserve all category counts.

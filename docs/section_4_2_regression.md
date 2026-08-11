# Section 4.2 Regression Reproduction

## Scope

The analysis reproduces every Section 4.2 calculation that does not require fold cross-validation:

1. unconstrained power-law regression (Table 3);
2. constrained coefficient-contour analysis (Fig. 11);
3. full-database constrained regression (Table 4);
4. full-database predicted-versus-numerical period comparison (adapted Fig. 13); and
5. constrained models without plan-width information (Table 5).

Fig. 12 and pooled out-of-fold predictions are intentionally excluded.

## Data expansion

Each of the 1,333 building records contributes two directional observations:

- transverse effective width and transverse period; and
- longitudinal effective width and longitudinal period.

The regression therefore uses 2,666 directional observations. The two directions remain linked by `model_id` in the generated prediction file.

## Categories

The four manuscript categories are constructed as follows:

| Manuscript category | Database mapping |
|---|---|
| Non-Framed Tube | `SW` and `FSW` |
| Framed Tube | `FT` |
| Low-Intensity | seismic intensity degree 6 or 7 |
| High-Intensity | seismic intensity degree 8 |

## Unconstrained regression

Table 3 is reproduced with the linearized model

```text
ln(T) = ln(alpha_0) + alpha_H ln(H) - alpha_B ln(B).
```

All three coefficients are estimated by ordinary least squares. `R_squared` is evaluated in the original period scale, consistent with the manuscript table.

## Constrained regression

For the constrained models, the implementation follows the manuscript power-law form

```text
T = alpha_0 (H / B^alpha_B)^alpha_H.
```

The fixed coefficients are:

| Category | `alpha_B` | `alpha_H` |
|---|---:|---:|
| Non-Framed Tube | 0.2 | 1.0 |
| Framed Tube | 0.2 | 1.1 |

Only `alpha_0` is fitted, using the closed-form mean log residual solution.

## Dispersion definitions

The manuscript tables are most closely reproduced from the released, rounded supplementary data by using the root mean square log residual:

```text
sigma_lnT = sqrt(SSE_lnT / n).
```

For auditability, every CSV table also reports `sigma_ln_t_eq23`, calculated with the degrees-of-freedom denominator in Eq. (23):

```text
sigma_lnT_eq23 = sqrt(SSE_lnT / (n - n_p)).
```

The relative dispersion change follows Eq. (24):

```text
e_sigma = (sigma_constrained - sigma_unconstrained) / sigma_constrained.
```

## R-squared reporting

The published Table 3 and Table 4 values correspond to `R_squared` in the original period scale. The published Table 5 values correspond to `R_squared` in logarithmic space. The generated CSV files preserve both definitions as `r_squared` or `r_squared_period` and `r_squared_log`, while each paper-style LaTeX table displays the definition used in the corresponding manuscript table.

Most Table 5 values are closely reproduced after accounting for the two-decimal precision of the released supplementary periods. The largest difference is the transverse High-Intensity Non-Framed Tube model: the released data give a log-space `R_squared` of approximately 0.706, whereas the manuscript table reports 0.741. The repository reports the value calculated from the released data and does not replace it with the manuscript reference value.

## Reproduction note for Table 4

The published Table 4 displays the same rounded `sigma_lnT` values as Table 3, while its reported `e_sigma` values imply the larger constrained dispersions obtained by direct calculation. The generated Table 4 reports the recalculated constrained dispersions, which are internally consistent with `e_sigma`. Both RMS and Eq. (23) dispersions are retained in the CSV output.

## Adapted Fig. 13

The manuscript Fig. 13 uses pooled out-of-fold predictions. The repository version requested for this release uses the final constrained models fitted to the complete database. Its annotation and filename explicitly identify it as a full-data fit so that it cannot be mistaken for cross-validation performance.

Metrics are calculated as:

- `R_squared`: coefficient of determination in the original period scale;
- `RMSE`: root mean square prediction error in seconds; and
- `MRE`: mean of `(predicted - numerical) / numerical`, expressed as a percentage.

## Run the analysis

```bash
python -m pip install -r requirements.txt
python -m analysis.section_4_2.run_analysis
python -m unittest tests.test_section_4_2
```

All generated tables and figures are written to `results/section_4_2/`.

# Representative plan-regularity examples

These examples are selected directly from `data/azimuth_prediction/building_plan_geometry.sqlite` at target regularity ratios from 0.95 to 0.45 in steps of 0.05. Exact and near-exact rectangles above 0.975 are excluded. To avoid numerically ambiguous principal directions, the inertia-equivalent rectangle must have a long-to-short aspect ratio of at least 1.20. The classification threshold is `eta_A = 0.80`: values below 0.80 are irregular.

![Representative examples](figures/plan_geometry_area_ratio_examples.png)

| Target `eta_A` | Model ID | Actual `eta_A` | Class | Equivalent aspect ratio | Equivalent angle | Axis deviation | MBR deviation | Figure |
|---:|---|---:|---|---:|---:|---:|---:|---|
| 0.95 | FSW-140 | 0.927194 | Regular | 1.778 | 173.04° | 6.96° | 6.96° | [PNG](figures/plan_geometry_A095.png) |
| 0.90 | FT-134 | 0.882908 | Regular | 1.222 | 140.73° | 39.27° | 39.27° | [PNG](figures/plan_geometry_A090.png) |
| 0.85 | FT-175 | 0.850462 | Regular | 1.267 | 154.42° | 25.58° | 25.58° | [PNG](figures/plan_geometry_A085.png) |
| 0.80 | SW-761 | 0.786043 | Irregular | 1.307 | 145.48° | 34.52° | 34.52° | [PNG](figures/plan_geometry_A080.png) |
| 0.75 | FSW-50 | 0.754717 | Irregular | 1.579 | 114.90° | 24.90° | 24.90° | [PNG](figures/plan_geometry_A075.png) |
| 0.70 | SW-362 | 0.676346 | Irregular | 1.300 | 36.14° | 36.14° | 36.82° | [PNG](figures/plan_geometry_A070.png) |
| 0.65 | SW-383 | 0.631934 | Irregular | 1.434 | 134.18° | 44.18° | 44.18° | [PNG](figures/plan_geometry_A065.png) |
| 0.60 | FSW-25 | 0.582254 | Irregular | 1.784 | 137.53° | 42.47° | 42.47° | [PNG](figures/plan_geometry_A060.png) |
| 0.55 | FSW-11 | 0.569826 | Irregular | 1.259 | 44.70° | 44.70° | 43.40° | [PNG](figures/plan_geometry_A055.png) |
| 0.50 | SW-717 | 0.475916 | Irregular | 1.897 | 157.80° | 22.20° | 22.20° | [PNG](figures/plan_geometry_A050.png) |
| 0.45 | SW-326 | 0.444190 | Irregular | 1.215 | 20.51° | 20.51° | 34.54° | [PNG](figures/plan_geometry_A045.png) |

Regenerate all figures and this table with:

```bash
python scripts/generate_azimuth_examples.py
```

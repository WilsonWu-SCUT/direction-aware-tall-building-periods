# Representative plan-regularity examples

These examples are selected directly from `data/azimuth_prediction/building_plan_geometry.sqlite` at target regularity ratios from 0.95 to 0.45 in steps of 0.05. Exact and near-exact rectangles above 0.975 are excluded. The classification threshold is `eta_A = 0.80`: values below 0.80 are irregular.

![Representative examples](figures/plan_geometry_area_ratio_examples.png)

| Target `eta_A` | Model ID | Actual `eta_A` | Class | Equivalent angle | Axis deviation | MBR deviation | Figure |
|---:|---|---:|---|---:|---:|---:|---|
| 0.95 | FT-284 | 0.951670 | Regular | 44.58° | 44.58° | 44.58° | [PNG](figures/plan_geometry_A095.png) |
| 0.90 | FT-134 | 0.882908 | Regular | 140.73° | 39.27° | 39.27° | [PNG](figures/plan_geometry_A090.png) |
| 0.85 | FT-175 | 0.850462 | Regular | 154.42° | 25.58° | 25.58° | [PNG](figures/plan_geometry_A085.png) |
| 0.80 | SW-761 | 0.786043 | Irregular | 145.48° | 34.52° | 34.52° | [PNG](figures/plan_geometry_A080.png) |
| 0.75 | SW-247 | 0.750755 | Irregular | 125.36° | 35.36° | 35.36° | [PNG](figures/plan_geometry_A075.png) |
| 0.70 | SW-362 | 0.676346 | Irregular | 36.14° | 36.14° | 36.82° | [PNG](figures/plan_geometry_A070.png) |
| 0.65 | SW-383 | 0.631934 | Irregular | 134.18° | 44.18° | 44.18° | [PNG](figures/plan_geometry_A065.png) |
| 0.60 | SW-294 | 0.575037 | Irregular | 136.39° | 43.61° | 43.61° | [PNG](figures/plan_geometry_A060.png) |
| 0.55 | FSW-11 | 0.569826 | Irregular | 44.70° | 44.70° | 43.40° | [PNG](figures/plan_geometry_A055.png) |
| 0.50 | SW-542 | 0.482140 | Irregular | 121.51° | 31.51° | 39.94° | [PNG](figures/plan_geometry_A050.png) |
| 0.45 | SW-472 | 0.459804 | Irregular | 127.81° | 37.81° | 34.68° | [PNG](figures/plan_geometry_A045.png) |

Regenerate all figures and this table with:

```bash
python scripts/generate_azimuth_examples.py
```

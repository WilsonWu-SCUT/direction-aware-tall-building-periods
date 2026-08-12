# Plan Geometry Intelligence Lab

The [Plan Geometry Intelligence Lab](http://geo.wwstruct.com) is an interactive
companion to the repository. It obtains a building plan from the research
database, a custom drawing, or a public map footprint, then calculates the
minimum bounding rectangle, inertia-equivalent rectangle, principal directions,
plan regularity, and direction-aware translational periods.

Use a current version of Edge, Chrome, Firefox, or Safari. Internet Explorer 11
is not supported. Geometry and prediction results appear in the **Analysis
Output** panel on the right.

## 1. Database Mode: stored building plans

1. Keep **DATABASE MODE** selected.
2. Choose a record under **MODEL ID**, or enter an identifier under
   **FIND MODEL ID** and select **FIND**.
3. Review the plan overlay and the record information, effective widths,
   regularity, azimuths, and predicted periods.
4. Use the legend controls to show or hide the minimum bounding rectangle,
   equivalent rectangle, and principal axes.

![Database Mode showing a stored plan and analysis output](assets/figure-1-database-mode.png)

Database Mode exposes the anonymized research plans in the public geometry
database. Each selected identifier is shared with the period database, allowing
the interface to show both geometry-derived quantities and the corresponding
directional period inputs and predictions.

## 2. Draw a custom plan

1. Select **DRAW CUSTOM PLAN** to clear the database outline.
2. Click the metric grid to add vertices in sequence. Live analysis starts when
   three valid, non-collinear vertices are available.
3. Drag a vertex to refine the shape. Use **UNDO** to remove the latest point or
   **CLEAR** to remove all points.
4. Select **CLOSE PLAN** when the outline is valid.

![Custom drawing with live geometry analysis](assets/figure-2-custom-plan.png)

If the points are nearly collinear or enclose negligible area, the analysis is
withheld until the geometry becomes valid. This mode is useful for testing an
early design or a simplified footprint before a formal model exists.

## 3. Map Mode: select a CBD building

1. Select **MAP MODE**, then choose a city under **CBD LOCATION**.
2. Pan and zoom in **MAP NAVIGATION** until the target area is visible.
3. Select **SELECT BUILDINGS** and wait for the public building footprints to
   load.
4. Hover to highlight a footprint, then click it to generate the plan and run
   the analysis. Continue selecting other buildings as needed.
5. Review or enter the building height when the mapped feature does not provide
   a reliable value.
6. Select **EXIT SELECTION** to restore map navigation.

![Selected building with mapped attributes and period prediction](assets/figure-4-map-selection.png)

Map Mode uses public OpenStreetMap footprints and available tags. Some features
do not contain usable height or storey information, so a defensible height may
need to be entered before period prediction can be completed.

## 4. Interface and output reference

| Interface item | Meaning |
|---|---|
| **PLAN OUTLINE** | Imported, stored, drawn, or selected building footprint. |
| **MIN. BOUNDING RECT.** | Minimum-area rectangle enclosing the plan. |
| **EQUIVALENT RECT.** | Rectangle derived from the plan's two principal inertial properties. |
| **PRINCIPAL AXES** | Orthogonal transverse and longitudinal principal directions. |
| **PLAN REGULARITY** | Plan area divided by minimum bounding-rectangle area. The classification threshold is 0.80. |
| **PERIOD PREDICTION** | Direction-aware estimates using height, effective width, structural class, seismic intensity, and the paper's Table 4 parameters. |

The equivalent rectangle preserves the two principal second moments; it is not
required to have the same area as the original footprint. Plan regularity is
`eta_A = A / A_MBR`, with `eta_A >= 0.80` classified as regular.

## 5. Troubleshooting

- **Blank page:** confirm that a supported browser is being used, then
  force-refresh the page.
- **The map loads but buildings cannot be selected:** exit selection, pan or
  zoom to another view, and select **SELECT BUILDINGS** again. Public building
  data can take several seconds to respond.
- **No result appears while drawing:** add at least three non-collinear points,
  or drag an existing vertex until the polygon has a non-negligible area.
- **Building height is unavailable:** enter a defensible value manually when
  the mapped feature has no usable height or storey metadata.

## 6. Related repository documentation

- [Azimuth-prediction methods and Python usage](../analysis/azimuth_prediction/README.md)
- [Azimuth database structure](../data/azimuth_prediction/README.md)
- [Period-prediction methods](../analysis/period_prediction/README.md)

The screenshots in `assets/` were extracted from the English quick user guide.
Figure 3 is intentionally omitted; Figures 1, 2, and 4 are retained here.

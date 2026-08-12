PRAGMA foreign_keys = ON;
PRAGMA user_version = 3;

CREATE TABLE dataset_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE model_plans (
    model_pk INTEGER PRIMARY KEY,
    model_id TEXT NOT NULL UNIQUE,
    building_function TEXT NOT NULL CHECK (building_function IN ('Residential', 'Office', 'Hotel')),
    structural_system_code TEXT NOT NULL CHECK (structural_system_code IN ('SW', 'FSW', 'FT')),
    building_height_m REAL NOT NULL CHECK (building_height_m > 0),
    transverse_effective_width_m REAL NOT NULL CHECK (transverse_effective_width_m > 0),
    longitudinal_effective_width_m REAL NOT NULL CHECK (longitudinal_effective_width_m > 0),
    raw_t1_s REAL NOT NULL CHECK (raw_t1_s > 0),
    raw_t2_s REAL NOT NULL CHECK (raw_t2_s > 0),
    transverse_period_s REAL NOT NULL CHECK (transverse_period_s > 0),
    longitudinal_period_s REAL NOT NULL CHECK (longitudinal_period_s > 0)
);

CREATE TABLE plan_segments (
    model_pk INTEGER NOT NULL,
    segment_index INTEGER NOT NULL CHECK (segment_index >= 0),
    x1_m REAL NOT NULL,
    y1_m REAL NOT NULL,
    x2_m REAL NOT NULL,
    y2_m REAL NOT NULL,
    PRIMARY KEY (model_pk, segment_index),
    FOREIGN KEY (model_pk) REFERENCES model_plans (model_pk) ON DELETE CASCADE
) WITHOUT ROWID;

CREATE TABLE outline_vertices (
    model_pk INTEGER NOT NULL,
    vertex_index INTEGER NOT NULL CHECK (vertex_index >= 0),
    x_m REAL NOT NULL,
    y_m REAL NOT NULL,
    PRIMARY KEY (model_pk, vertex_index),
    FOREIGN KEY (model_pk) REFERENCES model_plans (model_pk) ON DELETE CASCADE
) WITHOUT ROWID;

CREATE TABLE geometry_metrics (
    model_pk INTEGER PRIMARY KEY,
    area_m2 REAL NOT NULL CHECK (area_m2 > 0),
    centroid_x_m REAL NOT NULL,
    centroid_y_m REAL NOT NULL,
    ix_centroid_m4 REAL NOT NULL CHECK (ix_centroid_m4 > 0),
    iy_centroid_m4 REAL NOT NULL CHECK (iy_centroid_m4 > 0),
    ixy_centroid_m4 REAL NOT NULL,
    major_principal_moment_m4 REAL NOT NULL CHECK (major_principal_moment_m4 > 0),
    minor_principal_moment_m4 REAL NOT NULL CHECK (minor_principal_moment_m4 > 0),
    transverse_azimuth_deg REAL NOT NULL CHECK (
        transverse_azimuth_deg >= 0 AND transverse_azimuth_deg < 180
    ),
    longitudinal_azimuth_deg REAL NOT NULL CHECK (
        longitudinal_azimuth_deg >= 0 AND longitudinal_azimuth_deg < 180
    ),
    transverse_effective_width_m REAL NOT NULL CHECK (transverse_effective_width_m > 0),
    longitudinal_effective_width_m REAL NOT NULL CHECK (longitudinal_effective_width_m > 0),
    mbr_length_m REAL NOT NULL CHECK (mbr_length_m > 0),
    mbr_width_m REAL NOT NULL CHECK (mbr_width_m > 0),
    mbr_area_m2 REAL NOT NULL CHECK (mbr_area_m2 > 0),
    mbr_long_axis_deg REAL NOT NULL CHECK (mbr_long_axis_deg >= 0 AND mbr_long_axis_deg < 180),
    equivalent_rectangle_area_m2 REAL NOT NULL CHECK (equivalent_rectangle_area_m2 > 0),
    equivalent_rectangle_long_axis_deg REAL NOT NULL CHECK (
        equivalent_rectangle_long_axis_deg >= 0 AND equivalent_rectangle_long_axis_deg < 180
    ),
    regularity_ratio REAL NOT NULL CHECK (regularity_ratio > 0 AND regularity_ratio <= 1.000001),
    plan_class TEXT NOT NULL CHECK (plan_class IN ('regular', 'irregular')),
    FOREIGN KEY (model_pk) REFERENCES model_plans (model_pk) ON DELETE CASCADE
);

CREATE TABLE derived_rectangle_vertices (
    model_pk INTEGER NOT NULL,
    rectangle_type TEXT NOT NULL CHECK (
        rectangle_type IN ('minimum_bounding', 'inertia_equivalent')
    ),
    vertex_index INTEGER NOT NULL CHECK (vertex_index BETWEEN 0 AND 3),
    x_m REAL NOT NULL,
    y_m REAL NOT NULL,
    PRIMARY KEY (model_pk, rectangle_type, vertex_index),
    FOREIGN KEY (model_pk) REFERENCES model_plans (model_pk) ON DELETE CASCADE
) WITHOUT ROWID;

CREATE TABLE source_file_summary (
    model_pk INTEGER PRIMARY KEY,
    std_boundary_sha256 TEXT NOT NULL CHECK (length(std_boundary_sha256) = 64),
    std_boundary_out_sha256 TEXT NOT NULL CHECK (length(std_boundary_out_sha256) = 64),
    plan_segment_count INTEGER NOT NULL CHECK (plan_segment_count > 0),
    outline_segment_count INTEGER NOT NULL CHECK (outline_segment_count > 0),
    outline_vertex_count INTEGER NOT NULL CHECK (outline_vertex_count > 2),
    mesh_region_count INTEGER NOT NULL CHECK (mesh_region_count > 0),
    mesh_triangle_count INTEGER NOT NULL CHECK (mesh_triangle_count > 0),
    mesh_area_m2 REAL NOT NULL CHECK (mesh_area_m2 > 0),
    FOREIGN KEY (model_pk) REFERENCES model_plans (model_pk) ON DELETE CASCADE
);

CREATE INDEX idx_model_plans_structural_system ON model_plans (structural_system_code);
CREATE INDEX idx_geometry_metrics_regularity ON geometry_metrics (plan_class, regularity_ratio);

CREATE VIEW plan_geometry_readable AS
SELECT
    plans.model_pk,
    plans.model_id,
    plans.building_function,
    plans.structural_system_code,
    plans.building_height_m,
    plans.transverse_effective_width_m,
    plans.longitudinal_effective_width_m,
    plans.transverse_period_s,
    plans.longitudinal_period_s,
    metrics.area_m2,
    metrics.centroid_x_m,
    metrics.centroid_y_m,
    metrics.ix_centroid_m4,
    metrics.iy_centroid_m4,
    metrics.ixy_centroid_m4,
    metrics.major_principal_moment_m4,
    metrics.minor_principal_moment_m4,
    metrics.transverse_azimuth_deg,
    metrics.longitudinal_azimuth_deg,
    metrics.transverse_effective_width_m AS derived_transverse_effective_width_m,
    metrics.longitudinal_effective_width_m AS derived_longitudinal_effective_width_m,
    metrics.mbr_length_m,
    metrics.mbr_width_m,
    metrics.mbr_area_m2,
    metrics.mbr_long_axis_deg,
    metrics.equivalent_rectangle_area_m2,
    metrics.equivalent_rectangle_long_axis_deg,
    metrics.regularity_ratio,
    metrics.plan_class,
    source.plan_segment_count,
    source.outline_vertex_count,
    source.mesh_triangle_count,
    source.mesh_area_m2
FROM model_plans AS plans
JOIN geometry_metrics AS metrics USING (model_pk)
JOIN source_file_summary AS source USING (model_pk);

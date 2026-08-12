PRAGMA foreign_keys = ON;
PRAGMA user_version = 1;

CREATE TABLE dataset_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE structural_systems (
    structural_system_code TEXT PRIMARY KEY,
    structural_system TEXT NOT NULL UNIQUE,
    source_table TEXT NOT NULL UNIQUE,
    CHECK (structural_system_code IN ('SW', 'FSW', 'FT'))
) WITHOUT ROWID;

CREATE TABLE period_records (
    model_id TEXT PRIMARY KEY,
    structural_system_code TEXT NOT NULL,
    source_row INTEGER NOT NULL CHECK (source_row > 0),
    building_height_m REAL NOT NULL CHECK (building_height_m > 0),
    transverse_effective_width_m REAL NOT NULL CHECK (transverse_effective_width_m > 0),
    longitudinal_effective_width_m REAL NOT NULL CHECK (longitudinal_effective_width_m > 0),
    building_function TEXT NOT NULL CHECK (building_function IN ('Residential', 'Office', 'Hotel')),
    seismic_intensity_degree INTEGER NOT NULL CHECK (seismic_intensity_degree IN (6, 7, 8)),
    transverse_period_s REAL NOT NULL CHECK (transverse_period_s > 0),
    longitudinal_period_s REAL NOT NULL CHECK (longitudinal_period_s > 0),
    FOREIGN KEY (structural_system_code)
        REFERENCES structural_systems (structural_system_code),
    UNIQUE (structural_system_code, source_row)
) WITHOUT ROWID;

CREATE TABLE data_dictionary (
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    sqlite_type TEXT NOT NULL,
    unit TEXT,
    description TEXT NOT NULL,
    PRIMARY KEY (table_name, column_name)
) WITHOUT ROWID;

CREATE INDEX idx_period_records_structural_system
    ON period_records (structural_system_code);

CREATE INDEX idx_period_records_height
    ON period_records (building_height_m);

CREATE INDEX idx_period_records_function
    ON period_records (building_function);

CREATE INDEX idx_period_records_intensity
    ON period_records (seismic_intensity_degree);

CREATE VIEW period_records_readable AS
SELECT
    records.model_id,
    records.structural_system_code,
    systems.structural_system,
    systems.source_table,
    records.source_row,
    records.building_height_m,
    records.transverse_effective_width_m,
    records.longitudinal_effective_width_m,
    records.building_function,
    records.seismic_intensity_degree,
    records.transverse_period_s,
    records.longitudinal_period_s
FROM period_records AS records
JOIN structural_systems AS systems
  ON systems.structural_system_code = records.structural_system_code;


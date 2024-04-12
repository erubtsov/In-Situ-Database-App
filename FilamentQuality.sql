-- Check if the schema exists and create it if it doesn't
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.schemata
        WHERE schema_name = 'filamentquality'
    ) THEN
        CREATE SCHEMA filamentquality;
    END IF;
END$$;

-- Drop all existing tables only if there are tables to drop
DO $$
DECLARE
    _drop_sql TEXT;
BEGIN
    SELECT string_agg('DROP TABLE IF EXISTS ' || quote_ident(schemaname) || '.' || quote_ident(tablename) || ' CASCADE;', ' ')
    INTO _drop_sql
    FROM pg_tables
    WHERE schemaname = 'filamentquality';

    IF _drop_sql IS NOT NULL THEN
        EXECUTE _drop_sql;
    END IF;
END$$;

-- Create materials table with vendor
CREATE TABLE filamentquality.materials (
    material_id VARCHAR(50) NOT NULL,
    vendor VARCHAR(50) NOT NULL,
    PRIMARY KEY (material_id)
);

-- Create parts table with part type
CREATE TABLE filamentquality.parts (
    part_id VARCHAR(50) NOT NULL,
    material_id VARCHAR(50) NOT NULL,
    part_type VARCHAR(50) NOT NULL,
    PRIMARY KEY (part_id),
    FOREIGN KEY (material_id) REFERENCES filamentquality.materials(material_id)
);

-- Create BenchTop Filament Diameter table
CREATE TABLE filamentquality.BenchTop_Filament_Diameter (
    part_id VARCHAR(50) NOT NULL,
    position REAL NOT NULL,
    characteristic_name VARCHAR(100) NOT NULL,
    characteristic_value REAL NOT NULL,
    FOREIGN KEY (part_id) REFERENCES filamentquality.parts(part_id)
);

-- Create Live Print Data table
CREATE TABLE filamentquality.Live_Print_Data (
    part_id VARCHAR(50) NOT NULL,
    time_stamp REAL NOT NULL,
    characteristic_name VARCHAR(100) NOT NULL,
    characteristic_value REAL NOT NULL,
    FOREIGN KEY (part_id) REFERENCES filamentquality.parts(part_id)
);

-- Create part characteristics table
CREATE TABLE filamentquality.part_characteristics (
    part_id VARCHAR(50) NOT NULL,
    time_elapsed REAL NOT NULL,
    characteristic_name VARCHAR(100) NOT NULL,
    characteristic_value REAL NOT NULL,
    FOREIGN KEY (part_id) REFERENCES filamentquality.parts(part_id)
);

-- Create material thermal characteristics table with an auto-incrementing primary key
CREATE TABLE filamentquality.material_thermal_characteristics (
    id SERIAL PRIMARY KEY,
    material_id VARCHAR(50) NOT NULL,
    dsc_ramp TEXT NOT NULL,
    time_min REAL NOT NULL,
    temperature REAL NOT NULL,
    heat_flow REAL NOT NULL,
    FOREIGN KEY (material_id) REFERENCES filamentquality.materials(material_id)
);

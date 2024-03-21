-- Check if the schema exists and create it if it doesn't
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.schemata
        WHERE schema_name = 'FilamentQuality'
    ) THEN
        CREATE SCHEMA "FilamentQuality";
    END IF;
END$$;

-- Drop all existing tables
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'FilamentQuality'
    ) THEN
        DROP TABLE IF EXISTS "FilamentQuality"."Part_Quality";
        DROP TABLE IF EXISTS "FilamentQuality"."Characterization";
        DROP TABLE IF EXISTS "FilamentQuality"."BenchTop_Filament_Diameter";
        DROP TABLE IF EXISTS "FilamentQuality"."Live_Print_Data";
        DROP TABLE IF EXISTS "FilamentQuality"."parts";
    END IF;
END$$;

-- Create the tables
CREATE TABLE IF NOT EXISTS "FilamentQuality"."parts" (
    "part_ID" VARCHAR(50) NOT NULL,
    "material_ID" VARCHAR(50),
    CONSTRAINT "pk_parts" PRIMARY KEY ("part_ID")
);

CREATE TABLE IF NOT EXISTS "FilamentQuality"."Live_Print_Data" (
    "time_stamp" REAL NOT NULL,
    "part_ID" VARCHAR(50) NOT NULL,
    "characteristic_name" VARCHAR(100) NOT NULL,
    "characteristic_value" REAL NOT NULL,
    CONSTRAINT "fk_Live_Print_Data_part_ID" FOREIGN KEY ("part_ID") REFERENCES "FilamentQuality"."parts" ("part_ID")
);

CREATE TABLE IF NOT EXISTS "FilamentQuality"."BenchTop_Filament_Diameter" (
    "part_ID" VARCHAR(50) NOT NULL,
    "position" REAL NOT NULL,
    "characteristic_name" VARCHAR(100) NOT NULL,
    "characteristic_value" REAL NOT NULL,
    CONSTRAINT "fk_BenchTop_Filament_Diameter_part_ID" FOREIGN KEY ("part_ID") REFERENCES "FilamentQuality"."parts" ("part_ID")
);

CREATE TABLE IF NOT EXISTS "FilamentQuality"."characteristics" (
    "material_ID" VARCHAR(50) NOT NULL,
    "time_elapsed" REAL NOT NULL,
    "characteristic_name" VARCHAR(100) NOT NULL,
    "characteristic_value" REAL NOT NULL,
    CONSTRAINT "pk_characteristics" PRIMARY KEY ("material_ID")
);

CREATE TABLE IF NOT EXISTS "FilamentQuality"."Part_Quality" (
    "time_elapsed" REAL NOT NULL,
    "part_ID" VARCHAR(50) NOT NULL,
    "characteristic_name" VARCHAR(100) NOT NULL,
    "characteristic_value" REAL NOT NULL,
    CONSTRAINT "fk_Part_Quality_part_ID" FOREIGN KEY ("part_ID") REFERENCES "FilamentQuality"."parts" ("part_ID")
);

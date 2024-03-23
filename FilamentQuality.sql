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
	 	DROP TABLE IF EXISTS "FilamentQuality"."characteristics" CASCADE;
        DROP TABLE IF EXISTS "FilamentQuality"."part_characteristics" CASCADE; -- Cascade to drop dependent objects
        DROP TABLE IF EXISTS "FilamentQuality"."material_characteristics" CASCADE; -- Cascade to drop dependent objects
        DROP TABLE IF EXISTS "FilamentQuality"."materials" CASCADE; -- Cascade to drop dependent objects
        DROP TABLE IF EXISTS "FilamentQuality"."BenchTop_Filament_Diameter" CASCADE; -- Cascade to drop dependent objects
        DROP TABLE IF EXISTS "FilamentQuality"."Live_Print_Data" CASCADE; -- Cascade to drop dependent objects
        DROP TABLE IF EXISTS "FilamentQuality"."parts" CASCADE; -- Cascade to drop dependent objects
    END IF;
END$$;

-- Exported from QuickDBD: https://www.quickdatabasediagrams.com/
-- Link to schema: https://app.quickdatabasediagrams.com/#/d/KSlYlm

CREATE TABLE "FilamentQuality"."Live_Print_Data" (
    "part_ID" varchar(50)   NOT NULL,
    "time_stamp" real   NOT NULL,
    "characteristic_name" varchar(100)   NOT NULL,
    "characteristic_value" real   NOT NULL
);

CREATE TABLE "FilamentQuality"."BenchTop_Filament_Diameter" (
    "part_ID" varchar(50)   NOT NULL,
    "position" real   NOT NULL,
    "characteristic_name" varchar(100)   NOT NULL,
    "characteristic_value" real   NOT NULL
);

CREATE TABLE "FilamentQuality"."parts" (
    "part_ID" varchar(50)   NOT NULL,
    "material_ID" varchar(50)   NOT NULL,
    "part_type" varchar(50) NOT NULL,
    CONSTRAINT "pk_parts" PRIMARY KEY ("part_ID") -- Adding primary key constraint
);

CREATE TABLE "FilamentQuality"."part_characteristics" (
    "part_ID" varchar(50)   NOT NULL,
    "time_elapsed" real   NOT NULL,
    "characteristic_name" varchar(100)   NOT NULL,
    "characteristic_value" real   NOT NULL
);

CREATE TABLE "FilamentQuality"."material_characteristics" (
    "material_ID" varchar(50)   NOT NULL,
    "time_elapsed" real   NOT NULL,
    "characteristic_name" varchar(100)   NOT NULL,
    "characteristic_value" real   NOT NULL
);

CREATE TABLE "FilamentQuality"."materials" (
    "material_id" varchar(50)   NOT NULL,
    CONSTRAINT "pk_materials" PRIMARY KEY (
        "material_id"
     )
);

ALTER TABLE "FilamentQuality"."Live_Print_Data" ADD CONSTRAINT "fk_Live_Print_Data_part_ID" FOREIGN KEY("part_ID")
REFERENCES "FilamentQuality"."parts" ("part_ID");

ALTER TABLE "FilamentQuality"."BenchTop_Filament_Diameter" ADD CONSTRAINT "fk_BenchTop_Filament_Diameter_part_ID" FOREIGN KEY("part_ID")
REFERENCES "FilamentQuality"."parts" ("part_ID");

ALTER TABLE "FilamentQuality"."parts" ADD CONSTRAINT "fk_parts_material_ID" FOREIGN KEY("material_ID")
REFERENCES "FilamentQuality"."materials" ("material_id");

ALTER TABLE "FilamentQuality"."part_characteristics" ADD CONSTRAINT "fk_Part_characteristics_part_ID" FOREIGN KEY("part_ID")
REFERENCES "FilamentQuality"."parts" ("part_ID");

ALTER TABLE "FilamentQuality"."material_characteristics" ADD CONSTRAINT "fk_material_characteristics_material_ID" FOREIGN KEY("material_ID")
REFERENCES "FilamentQuality"."materials" ("material_id");

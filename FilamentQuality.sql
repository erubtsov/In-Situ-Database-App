DO $$DECLARE
    r RECORD;
BEGIN
    -- Drop foreign key constraints if they exist
    FOR r IN (
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
    ) LOOP
        BEGIN
            EXECUTE 'ALTER TABLE ' || quote_ident(r.constraint_name::text) || ' DROP CONSTRAINT ' || quote_ident(r.constraint_name);
        EXCEPTION
            WHEN OTHERS THEN
                -- Constraint does not exist, continue to the next one
                CONTINUE;
        END;
    END LOOP;

    -- Drop tables if they exist
    FOR r IN (
        SELECT table_name
        FROM information_schema.tables
    ) LOOP
        BEGIN
            EXECUTE 'DROP TABLE ' || quote_ident(r.table_name) || ' CASCADE';
        EXCEPTION
            WHEN OTHERS THEN
                -- Table does not exist, continue to the next one
                CONTINUE;
        END;
    END LOOP;

    -- Create tables if they don't exist
    CREATE TABLE IF NOT EXISTS "FilamentQuality"."characteristics" (
        "time_elapsed" real   NOT NULL,
        "material_ID" varchar(50)   NOT NULL,
        "characteristic_name" varchar(100)   NOT NULL,
        "characteristic_value" real   NOT NULL,
        CONSTRAINT "pk_characteristics" PRIMARY KEY (
            "material_ID"
         )
    );

    CREATE TABLE IF NOT EXISTS "FilamentQuality"."parts" (
        "part_ID" varchar(50)   NOT NULL,
        "material_ID" varchar(50)   NOT NULL,
        CONSTRAINT "pk_parts" PRIMARY KEY (
            "part_ID"
         ),
        CONSTRAINT "fk_parts_material_ID" FOREIGN KEY("material_ID")
        REFERENCES "FilamentQuality"."characteristics" ("material_ID")
    );

    CREATE TABLE IF NOT EXISTS "FilamentQuality"."Live_Print_Data" (
        "time_stamp" real   NOT NULL,
        "part_ID" varchar(50)   NOT NULL,
        "characteristic_name" varchar(100)   NOT NULL,
        "characteristic_value" real   NOT NULL,
        CONSTRAINT "fk_Live_Print_Data_part_ID" FOREIGN KEY("part_ID")
        REFERENCES "FilamentQuality"."parts" ("part_ID")
    );

    CREATE TABLE IF NOT EXISTS "FilamentQuality"."BenchTop_Filament_Diameter" (
        "part_ID" varchar(50)   NOT NULL,
        "position" real   NOT NULL,
        "characteristic_name" varchar(100)   NOT NULL,
        "characteristic_value" real   NOT NULL,
        CONSTRAINT "fk_BenchTop_Filament_Diameter_part_ID" FOREIGN KEY("part_ID")
        REFERENCES "FilamentQuality"."parts" ("part_ID")
    );
END$$;

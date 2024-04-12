import psycopg2
import os
import json
import csv
import pandas as pd
import xlrd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

directories = {
    "Characteristics": {"XRD": "", "FTIR": "", "TGA": ""},
    "BenchTop Filament Diameter": "",
    "Live Print Data": "",
    "Parts Quality": {"pressure": ""}
}

def connect_to_database(password):
    try:
        db_params = {
            'dbname': 'postgres',
            'user': 'postgres',
            'password': password,
            'host': 'localhost',
            'port': '5432',
            'options': '-c search_path=filamentquality'
        }
        conn = psycopg2.connect(**db_params)
        logger.info("Connected to the database successfully.")
        return conn
    except psycopg2.Error as e:
        logger.error("Error connecting to PostgreSQL database: %s", e)
        return None

def extract_ids_from_filename(filename):
    """
    Extracts material_id, material, vendor, and color from the filename.
    Assumes filename format like 'material_vendor_other_color'.
    Strips the file extension before processing.
    Material ID is the full filename without the extension.
    """
    # Strip the file extension (handles .csv, .xls, .xlsx, .tdms)
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split('_')
    if len(parts) < 3:  # Ensuring there are at least three parts
        logger.error("Filename format is incorrect, expected at least 3 parts separated by underscores: %s", filename)
        return None, None, None, None

    material_id = base_name.lower()
    material = parts[0].lower()
    vendor = parts[1].lower()
    color = parts[-1].lower()  # Assuming color is the last part, adjust if needed
    
    return material_id, vendor, material, color

def insert_material_if_not_exists(conn, material_id, vendor):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO filamentquality.materials (material_id, vendor) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                (material_id, vendor)
            )
            conn.commit()
            logger.info(f"Material ID '{material_id}' with vendor '{vendor}' ensured in database.")
    except Exception as e:
        logger.error(f"Error ensuring material ID '{material_id}' with vendor '{vendor}': {e}")
        conn.rollback()

def insert_part_if_applicable(conn, part_id, material_id, vendor, part_type):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO filamentquality.parts (part_id, material_id, vendor, part_type) VALUES (%s, %s, %s, %s) ON CONFLICT (part_id) DO NOTHING;",
                (part_id, material_id, vendor, part_type)
            )
            conn.commit()
            logger.info(f"Part ID '{part_id}' with material ID '{material_id}', vendor '{vendor}', and part type '{part_type}' inserted successfully.")
    except psycopg2.Error as e:
        logger.error(f"Error inserting part ID '{part_id}': {e}")
        conn.rollback()
      
def process_data_for_purpose(directory, purpose, conn):
    """
    Process data in the specified directory based on the purpose by mapping the purpose to its loader function.
    """
    if purpose in PURPOSE_MAPPING:
        config = PURPOSE_MAPPING[purpose]
        files = os.listdir(directory)
        logger.info(f"Found {len(files)} files in directory {directory} for processing.")
        for filename in filter(lambda f: any(f.endswith(ext) for ext in config['extensions']), files):
            filepath = os.path.join(directory, filename)
            try:
                logger.info(f"Processing file: {filename} for purpose: {purpose}")
                config['loader'](filepath, conn)
            except Exception as e:
                logger.error(f"Failed to process file {filename} for purpose {purpose}: {e}")
    else:
        logger.warning(f"No processing function defined for the purpose: '{purpose}'.")

def load_characteristics(filepath, conn):
    logger.info(f"Loading characteristics data from {filepath}")
    try:
        base_name = os.path.basename(filepath)
        material_id, vendor, _, _ = extract_ids_from_filename(base_name)  # No part type or part ID for characteristics
        logger.info(f"Extracted IDs - Material ID: {material_id}, Vendor: {vendor}")

        insert_material_if_not_exists(conn, material_id, vendor)
        data_type = 'TGA' if "TGA" in filepath.upper() else 'DSC' if "DSC" in filepath.upper() else None
        if data_type:
            load_thermal_data(filepath, conn, material_id, data_type)
        else:
            logger.info(f"File {filepath} does not match expected data types for processing.")
    except Exception as e:
        logger.error(f"Error loading characteristics data from {filepath}: {e}")

def process_files_in_directory(directory_config, conn):
    """
    Process files in directories based on their purpose.
    """
    for purpose, directory in directory_config.items():
        if os.path.isdir(directory):
            logger.info(f"Processing files in directory: {directory} for purpose: {purpose}")
            process_data_for_purpose(directory, purpose, conn)
        else:
            logger.warning(f"Invalid or non-existent directory path: {directory} for purpose: {purpose}")


def load_live_print_data(filepath, conn):
    logger.info(f"Loading live print data from: {filepath}")
    # Placeholder for actual loading logic
    pass

def load_thermal_data(file_path, conn, material_id, data_type):
    try:
        logger.info(f"Attempting to load {data_type.upper()} data from file: {file_path}")
        _, vendor, _, _ = extract_ids_from_filename(os.path.basename(file_path))  # Re-extract vendor to ensure it's not missed
        logger.info(f"Vendor for {material_id} is identified as {vendor}")

        xls = pd.ExcelFile(file_path)
        # Ensuring the material is in the database before attempting to insert DSC data
        insert_material_if_not_exists(conn, material_id, vendor)

        for sheet_index in range(1, len(xls.sheet_names)):  # Start from 1 to skip any summary sheet if present
            sheet_name = xls.sheet_names[sheet_index]
            headers = pd.read_excel(file_path, sheet_name=sheet_name, nrows=3, header=None)
            combined_headers = headers.iloc[1] + ' ' + headers.iloc[2].fillna('')
            combined_headers = combined_headers.str.replace(r'\s*\([^)]*\)', '', regex=True).str.strip()
            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=3, names=combined_headers)

            dsc_ramp = headers.iloc[0, 0] if headers.shape[1] > 0 else "Unknown Ramp"
            logger.info(f"Processing sheet '{sheet_name}' with DSC ramp: {dsc_ramp}")

            sql_insert = """
                INSERT INTO filamentquality.material_thermal_characteristics
                (material_id, dsc_ramp, time_min, temperature, heat_flow)
                VALUES (%s, %s, %s, %s, %s)
            """
            with conn.cursor() as cursor:
                for index, row in df.iterrows():
                    cursor.execute(sql_insert, (
                        material_id,
                        dsc_ramp,
                        row['Time min'],
                        row['Temperature °C'],
                        row['Heat Flow W/g']
                    ))
                    logger.info(f"Inserted: Material ID {material_id}, Ramp {dsc_ramp}, Time {row['Time min']}")
            conn.commit()
            logger.info(f"Successfully loaded data from sheet '{sheet_name}'.")

    except Exception as e:
        conn.rollback()
        logger.error(f"Exception during loading {data_type.upper()} data: {e}")


def check_data_before_insert(conn, material_id, dsc_ramp, time_min):
    """ Checks if the data already exists to avoid duplicate entry errors. """
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM filamentquality.material_thermal_characteristics WHERE material_id = %s AND dsc_ramp = %s AND time_min = %s",
                (material_id, dsc_ramp, time_min)
            )
            exists = cursor.fetchone() is not None
            if exists:
                logger.debug(f"Data already exists for Material ID: {material_id}, Ramp: {dsc_ramp}, Time Min: {time_min}")
            return exists
    except Exception as e:
        logger.error(f"Error checking for existing data: {e}")
        return False

def load_pressure(file_path, conn):
    material_id, vendor, part_type, part_id = extract_ids_from_filename(os.path.basename(file_path))
    insert_material_if_not_exists(conn, material_id, vendor)
    insert_part_if_applicable(conn, part_id, material_id, vendor, part_type)

    logger.info("Starting to load pressure data from: %s", file_path)
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            column_names = ["X_Value", "Temp (C)", "Pressure", "Flow SLPM (Filtered)"]
            sql_insert = 'INSERT INTO filamentquality.part_characteristics (part_id, time_elapsed, characteristic_name, characteristic_value) VALUES (%s, %s, %s, %s)'

            header_count, data_start_index = 0, None
            for i, line in enumerate(lines):
                if line.strip() == '***End_of_Header***':
                    header_count += 1
                    if header_count == 2:
                        data_start_index = i + 2
                        break

            if data_start_index is None:
                logger.error("Failed to find the end of header in pressure data file: %s", file_path)
                return

            with conn.cursor() as cursor:
                for line in lines[data_start_index:]:
                    values = line.strip().split('\t')
                    cursor.execute(sql_insert, (part_id, values[0], "Pressure", values[2]))
                    logger.info("Inserted pressure data for part ID %s: %s, Pressure, %s", part_id, values[0], values[2])

        conn.commit()
        logger.info("Successfully loaded pressure data for part ID: %s", part_id)
    except Exception as e:
        conn.rollback()
        logger.error("Failed to load pressure data from %s: %s", file_path, e)

def load_diameter(file_path, conn):
    material_id, vendor, part_type, part_id = extract_ids_from_filename(os.path.basename(file_path))
    insert_material_if_not_exists(conn, material_id, vendor)
    insert_part_if_applicable(conn, part_id, material_id, vendor, part_type)
    logger.info("Starting to load diameter data from: %s", file_path)
    try:
        with open(file_path, 'r') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)
            column_names = next(reader)

            sql_insert = ('INSERT INTO filamentquality.benchtop_filament_diameter '
                          '(part_id, position, characteristic_name, characteristic_value) '
                          'VALUES (%s, %s, %s, %s)')

            with conn.cursor() as cursor:
                for values in reader:
                    if len(values) < len(column_names):
                        logger.warning("Mismatched column count in line, skipping.")
                        continue
                    distance_m = values[-1]  # Assuming the last value is the distance/position
                    for i, value in enumerate(values[:-1]):  # Exclude the last value (distance_m) from iteration
                        characteristic_name = column_names[i]  # Use the column name corresponding to the index
                        cursor.execute(sql_insert, (part_id, distance_m, characteristic_name, value))
                        logger.info("Inserted diameter data for part ID %s at position %s: %s, %s", part_id, distance_m, characteristic_name, value)

            conn.commit()
            logger.info("Successfully loaded diameter data for part ID: %s", part_id)
    except Exception as e:
        conn.rollback()
        logger.error("Failed to load diameter data from %s: %s", file_path, e)


# Mapping of purposes to their configurations
PURPOSE_MAPPING = {
    "Parts Quality": {
        "extensions": ['.tdms'],
        "loader": load_pressure
    },
    "BenchTop Filament Diameter": {
        "extensions": ['.csv'],
        "loader": load_diameter
    },
    "Characteristics": {
        "extensions": ['.xls', '.xlsx'],
        "loader": load_characteristics
    },
    "Live Print Data": {
        "extensions": ['.csv'],
        "loader": load_live_print_data
    }
}




import psycopg2
import os
import json
import csv
import pandas as pd
import xlrd

directories = {
    "Characteristics": {
        "XRD": "",
        "FTIR": "",
        "TGA": ""
    },
    "BenchTop Filament Diameter": "",
    "Live Print Data": "",
    "Parts Quality": {
        "pressure": ""
    }
}

def connect_to_database(password):
    try:
        db_params = {
            'dbname': 'postgres',
            'user': 'postgres',
            'password': password,
            'host': 'localhost',
            'port': '5432',
            'options': '-c search_path="FilamentQuality"'
        }
        conn = psycopg2.connect(**db_params)
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)
        return None

def insert_material(conn, material_id):
    try:
        with conn.cursor() as cursor:
            sql_query = 'INSERT INTO "FilamentQuality"."materials" ("material_id") VALUES (%s) ON CONFLICT DO NOTHING'
            cursor.execute(sql_query, (material_id.lower(),))
            conn.commit()
            print("Material ID inserted successfully:", material_id)
    except psycopg2.Error as e:
        print("Error inserting material ID:", e)

def extract_part_type(part_id):
    """Extracts the part type from the given part_id."""
    parts = part_id.split('_')
    # In this case, 'cyl' is the third element in the list
    if len(parts) >= 3:
        return parts[2].lower()  # Return the part type in lowercase
    else:
        print(f"Unable to extract part type from part ID: {part_id}")
        return None

def insert_part(conn, part_id, material_id):
    # Extract the part_type using the function defined above
    part_type = extract_part_type(part_id)
    if part_type is None:
        return  # Skip insertion if the part type is not found

    with conn.cursor() as cursor:
        sql_insert_part = '''
            INSERT INTO "FilamentQuality"."parts" ("part_ID", "material_ID", "part_type")
            VALUES (%s, %s, %s)
            ON CONFLICT ("part_ID") DO NOTHING;
        '''
        cursor.execute(sql_insert_part, (part_id, material_id, part_type))
        conn.commit()


def load_parts_id(directory_path, conn, purpose):
    print(f"Starting load_parts_id with purpose: {purpose} and directory path: {directory_path}")
    
    # Check directory path validity and proceed with parts ID loading
    if not os.path.isdir(directory_path):
        print(f"Invalid directory path: {directory_path}. Skipping processing.")
        return

    # Process files in the directory based on the purpose
    for file_name in os.listdir(directory_path):
        if file_name.endswith((".xls", ".csv", ".tdms")):

            file_path = os.path.join(directory_path, file_name)
            part_id = os.path.splitext(file_name)[0]
            material_id = extract_material_id(file_name)
            
            if purpose in ['BenchTop Filament Diameter', 'Parts Quality', 'Live Print Data']:
                # For non-characteristic purposes, insert the part_id into the "parts" table
                insert_part(conn, part_id, material_id)
            if material_id:
                insert_material(conn, material_id)
                print(f"Inserted material ID '{material_id}' into the database.")
            file_path = os.path.join(directory_path, file_name)
            if purpose == 'Characteristics':
                if 'TGA' in file_path.upper():
                    print(f"Loading TGA data from file: {file_path}")
                    load_thermal_data(file_path, conn, material_id, 'tga')
                elif 'DSC' in file_path.upper():
                    print(f"Loading DSC data from file: {file_path}")
                    load_thermal_data(file_path, conn, material_id, 'dsc')
            elif purpose == 'BenchTop Filament Diameter':
                load_diameter(file_path, conn)
            elif purpose == 'Parts Quality':
                load_pressure(file_path, conn)

    print(f"Finished processing directory '{directory_path}' for purpose '{purpose}'")

def load_thermal_data(file_path, conn, material_id, data_type):
    try:
        # Read the first three rows to get the headers
        headers = pd.read_excel(file_path, sheet_name=1, nrows=3, header=None)

        # Combine the second and third rows to form the complete headers
        combined_headers = headers.iloc[1] + ' ' + headers.iloc[2].where(pd.notnull(headers.iloc[2]), '')

        # Prefix 'DSC_' to the 'Temperature' header if it's DSC data
        combined_headers = [f"DSC_{name}" if 'Temperature' in name and data_type.lower() == 'dsc' else name for name in combined_headers]

        # Read the rest of the data using the new headers
        df = pd.read_excel(file_path, sheet_name=1, skiprows=3)
        df.columns = combined_headers

        # Prepare SQL query for inserting data
        sql_insert = ('INSERT INTO "FilamentQuality"."material_characteristics" '
                      '("material_ID", "time_elapsed", "characteristic_name", "characteristic_value") '
                      'VALUES (%s, %s, %s, %s)')

        with conn.cursor() as cursor:
            # Iterate through DataFrame rows and insert data
            for index, row in df.iterrows():
                # Retrieve time value ensuring the 'Time min' column exists
                if 'Time min' not in df.columns:
                    raise ValueError("Column 'Time min' does not exist in the DataFrame.")
                time_value = row['Time min']
                
                # Loop over each characteristic and insert into the database
                for col in df.columns[df.columns != 'Time min']:  # Skip the 'Time min' column
                    # Execute the insertion
                    cursor.execute(sql_insert, (material_id, time_value, col, row[col]))
                    print(f"Inserted record: Material ID: {material_id}, Time Elapsed: {time_value}, Characteristic Name: {col}, Characteristic Value: {row[col]}")

        conn.commit()
        print(f"{data_type.upper()} data loaded successfully for material ID {material_id} from {file_path}")
    except Exception as e:
        conn.rollback()
        print(f"Error loading {data_type.upper()} data from {file_path}: {e}")


def load_pressure(file_path, conn):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # Manually define column names
            column_names = ["X_Value", "Temp (C)", "Pressure", "Flow SLPM (Filtered)"]

            # Prepare SQL query for inserting data
            sql_insert = 'INSERT INTO "FilamentQuality"."part_characteristics" ("part_ID", "time_elapsed", "characteristic_name", "characteristic_value") VALUES (%s, %s, %s, %s)'

            with conn.cursor() as cursor:
                # Find the second occurrence of the header delimiter
                header_count = 0
                data_start_index = None
                for i, line in enumerate(lines):
                    if line.strip() == '***End_of_Header***':
                        header_count += 1
                        if header_count == 2:
                            data_start_index = i + 2  # Start reading data from the line after the second header
                            break

                if data_start_index is None:
                    print("Error: Second '***End_of_Header***' not found in the file.")
                    return

                # Get part ID from file name
                part_id = os.path.splitext(os.path.basename(file_path))[0]

                # Iterate over data lines and insert into the database
                for line in lines[data_start_index:]:
                    values = line.strip().split('\t')
                    time_elapsed = values[0]
                    pressure = values[2]  # Parse the third column as pressure
                    characteristics_values = values[1:]  # Exclude the time column

                    # Ensure the number of values matches the number of column names
                    if len(characteristics_values) != len(column_names) - 1:
                        print("Error: Number of values does not match the number of columns.")
                        continue

                    # Iterate over characteristics and insert into the database
                    for i, characteristic_value in enumerate(characteristics_values):
                        cursor.execute(sql_insert, (part_id, time_elapsed, column_names[i+1], characteristic_value))
                        print("Inserted row:", (part_id, time_elapsed, column_names[i+1], characteristic_value))

                conn.commit()
        print("Pressure data loaded successfully into 'FilamentQuality.part_characteristics'.")
    except Exception as e:
        print("Error loading pressure data:", e)

def extract_material_id(filename):
    """Extracts the material ID from the given filename, excluding the file extension."""
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split('_')
    if len(parts) >= 2:
        return '_'.join(parts[:2]).lower()
    else:
        print(f"Unable to extract material ID from filename: {filename}")
        return None

def load_diameter(file_path, conn):
    try:
        # Open the file using the csv module, which can handle various types of delimited files
        with open(file_path, 'r') as csvfile:
            # Trying to detect the delimiter
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)  # Reset file pointer after sniffing
            reader = csv.reader(csvfile, dialect)

            # Extract the header
            column_names = next(reader)
            print(f"Column names: {column_names}")

            sql_insert = ('INSERT INTO "FilamentQuality"."BenchTop_Filament_Diameter" '
                          '("part_ID", "position", "characteristic_name", "characteristic_value") '
                          'VALUES (%s, %s, %s, %s)')

            with conn.cursor() as cursor:
                part_id = os.path.splitext(os.path.basename(file_path))[0]

                for values in reader:
                    # Assuming 'Distance (m)' is the last column
                    distance_m = values[-1]
                    for i, value in enumerate(values[:-1]):  # Skip the last column which is 'Distance (m)'
                        cursor.execute(sql_insert, (part_id, distance_m, column_names[i], value))
                        print(f"Inserted {column_names[i]} at {distance_m}m: {value}")

                conn.commit()
            print("Diameter data loaded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error loading diameter data: {e}")

def query_materials(conn):
    try:
        with conn.cursor() as cursor:
            print("Querying materials table...")
            sql_query = 'SELECT "material_id" FROM "FilamentQuality"."materials"'
            print("Executing SQL:", sql_query)
            cursor.execute(sql_query)
            materials = cursor.fetchall()
            print("Materials successfully loaded:")
            if not materials:
                print("No materials found in the database")
            else:
                for material in materials:
                    print(material[0])
    except psycopg2.Error as e:
        print("Error querying materials:", e)

def query_database_by_part_id(part_id, conn, client_socket):
    try:
        with conn.cursor() as cursor:
            print("Querying database for part ID:", part_id)
            # Example SQL query to retrieve data based on part ID
            sql_query = 'SELECT * FROM "FilamentQuality"."parts" WHERE lower("part_ID") = %s'
            cursor.execute(sql_query, (part_id.lower(),))  # Compare with lowercase part_id
            result = cursor.fetchall()
            print("Query result:", result)
            
            # Check if any result is returned
            if not result:
                print("Part ID not found in the database.")
                client_socket.send("Part ID not found".encode())
            else:
                # Print the part IDs
                part_ids = [row[0] for row in result]
                print("Part IDs:", part_ids)

                # Convert the result to JSON format
                result_json = json.dumps(result)
                # Send the result back to the client
                client_socket.send(result_json.encode())  # Send the query result to the client
    except psycopg2.Error as e:
        print("Error querying database by part ID:", e)
        # Inform the client about the error
        client_socket.send("Error querying database".encode())

def query_parts(conn):
    try:
        with conn.cursor() as cursor:
            print("Querying parts table...")
            sql_query = 'SELECT * FROM "FilamentQuality"."parts"'
            print("Executing SQL:", sql_query)
            cursor.execute(sql_query)
            parts = cursor.fetchall()
            print("Parts successfully loaded:")
            if not parts:
                print("No parts found in the database")
                return []  # Return an empty list if no parts found
            else:
                part_ids = [part[0] for part in parts]  # Extracting only the part IDs
                return part_ids  # Return the list of part IDs
    except psycopg2.Error as e:
        print("Error querying parts:", e)
        return None  # Return None in case of error

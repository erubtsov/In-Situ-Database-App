import socket
import json
import psycopg2
import os

# Define global variables to store directory paths
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

def load_parts_id(directory_path, conn):
    try:
        if not isinstance(directory_path, str) or not directory_path:
            print("Invalid directory path. Skipping processing.")
            return

        with conn.cursor() as cursor:
            print("Loading part IDs from directory:", directory_path)
            for filename in os.listdir(directory_path):
                if filename.endswith((".tdms", ".CSV")):
                    part_id = os.path.splitext(filename)[0]
                    split_id = part_id.split('_')
                    material_id = '_'.join(split_id[:2]).lower()  # Convert material_id to lowercase
                    part_type = split_id[2]
                    print("Extracted part ID:", part_id)
                    print("Extracted material ID:", material_id)
                    print("Extracted part type:", part_type)
                    
                    # Check if material exists in the materials table (case-insensitive comparison)
                    cursor.execute('SELECT EXISTS(SELECT 1 FROM "FilamentQuality"."materials" WHERE lower("material_id") = %s)', (material_id,))
                    material_exists = cursor.fetchone()[0]
                    
                    if not material_exists:
                        insert_material(conn, material_id)  # Call check_and_insert_material to check and insert material
                    else:
                        print("Material ID already exists in the 'materials' table:", material_id)
                        
                    sql_query = 'SELECT "part_ID" FROM "FilamentQuality"."parts" WHERE lower("part_ID") = %s'
                    cursor.execute(sql_query, (part_id.lower(),))  # Compare with lowercase part_id
                    existing_part = cursor.fetchone()
                    if not existing_part:
                        sql_insert = 'INSERT INTO "FilamentQuality"."parts" ("part_ID", "material_ID", "part_type") VALUES (%s, %s, %s)'
                        print("Executing SQL:", sql_insert)
                        cursor.execute(sql_insert, (part_id, material_id, part_type))
                        conn.commit()
                        print("Part ID inserted successfully:", part_id)
                        # Call load_pressure after inserting a new part ID
                        load_pressure(os.path.join(directory_path, filename), conn)
                    else:
                        print("Part ID already exists:", part_id)
    except psycopg2.Error as e:
        conn.rollback()  # Rollback transaction in case of error
        print("Error loading part IDs:", e)
    finally:
        conn.commit()  # Commit transaction at the end

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

def load_pressure(directory_path, conn):
    print("Loading pressure data from directory:", directory_path)

def query_parts(conn):
    try:
        with conn.cursor() as cursor:
            print("Querying parts table...")
            #sql_query = 'SELECT "parts"."part_ID" FROM "FilamentQuality"."parts"'
            sql_query = 'SELECT * FROM "FilamentQuality"."parts"'
            print("Executing SQL:", sql_query)
            cursor.execute(sql_query)
            parts = cursor.fetchall()
            print("Parts successfully loaded:")
            if not parts:
                print("No parts found in the database")
            else:
                for part in parts:
                    print(part[0])
    except psycopg2.Error as e:
        print("Error querying parts:", e)

def handle_client(client_socket, conn):
    global directories

    # Receive password
    password_data = client_socket.recv(1024).decode()
    password = json.loads(password_data).get('password', '')

    # Check if there is an existing database connection
    if conn is None:
        conn = connect_to_database(password)

    if conn:
        client_socket.send("Correct".encode())
        print("Waiting for signal...")
        # Receive signal
        signal_data = client_socket.recv(1024).decode()
        signal = json.loads(signal_data).get('signal', '')
        if signal == "DataUpload":
            # Receive selected directories
            selected_directories_data = client_socket.recv(1024).decode()
            selected_directories = json.loads(selected_directories_data).get('selected_directories', {})
            print("Selected directories received:", selected_directories)
            for purpose, directory_path in selected_directories.items():
                if purpose == "Characteristics":
                    if isinstance(directory_path, dict):
                        for sub_purpose, sub_directory_path in directory_path.items():
                            if sub_purpose in directories["Characteristics"]:
                                directories["Characteristics"][sub_purpose] = sub_directory_path
                elif purpose == "Parts Quality":
                    if isinstance(directory_path, str):
                        if "pressure" in directory_path.lower():
                            directories["Parts Quality"]["pressure"] = directory_path
                            load_parts_id(directory_path, conn)

                elif purpose == "BenchTop Filament Diameter":
                    if isinstance(directory_path, str):
                        directories["BenchTop Filament Diameter"] = directory_path
                        load_parts_id(directory_path, conn)

            print("Selected directories:", directories)
            query_parts(conn)
            query_materials(conn)  # Call query_materials function here
        else:
            print("Invalid signal received.")
    else:
        client_socket.send("Incorrect".encode())
        # Receive retry signal
        retry_data = client_socket.recv(1024).decode()
        retry_signal = json.loads(retry_data).get('retry', '')
        if retry_signal == "RetryPassword":
            handle_client(client_socket, None)  # Retry handling the client with a new connection
        else:
            print("Invalid retry signal received.")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5555))
    server_socket.listen(5)
    print("Server is listening for connections...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            handle_client(client_socket, None)
    except KeyboardInterrupt:
        print("Server shutting down...")
        server_socket.close()

if __name__ == '__main__':
    main()


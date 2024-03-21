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
    
def load_parts_id(directory_path, conn):
    try:
        cursor = conn.cursor()
        print("Loading part IDs from directory:", directory_path)
        for filename in os.listdir(directory_path):
            if filename.endswith(".tdms"):
                part_id = os.path.splitext(filename)[0]
                print("Extracted part ID:", part_id)
                sql_insert = 'INSERT INTO "FilamentQuality"."parts" ("part_ID") VALUES (%s)'
                print("Executing SQL:", sql_insert)
                cursor.execute(sql_insert, (part_id,))
        conn.commit()
        print("Part IDs successfully loaded from directory:", directory_path)
    except psycopg2.Error as e:
        print("Error loading part IDs:", e)

def query_parts(conn):
    try:
        print("Querying parts table...") 
        cursor = conn.cursor()
        sql_query = 'SELECT "parts"."part_ID" FROM "FilamentQuality"."parts"'
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

    while True:
        data = client_socket.recv(1024).decode()

        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            print("Error decoding JSON data:", e)
            client_socket.send("Invalid JSON data received".encode())
            continue

        password = data.get('password', '')

        # Check if there is an existing database connection
        if conn is None:
            conn = connect_to_database(password)

        if conn:
            client_socket.send("Correct".encode())
            selected_directories = data.get('selected_directories', {})
            for purpose, directory_path in selected_directories.items():
                if purpose == "Characteristics":
                    if isinstance(directory_path, dict):
                        for sub_purpose, sub_directory_path in directory_path.items():
                            if sub_purpose in directories["Characteristics"]:
                                directories["Characteristics"][sub_purpose] = sub_directory_path
                elif purpose == "Parts Quality":
                    if "pressure" in directory_path.lower():
                        directories["Parts Quality"]["pressure"] = directory_path
                        load_parts_id(directory_path, conn)
            print("Selected directories:", directories)
            query_parts(conn)
            break  # Exit the loop if the password is correct
        else:
            client_socket.send("Incorrect".encode())

    # Close the client socket
    client_socket.close()

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


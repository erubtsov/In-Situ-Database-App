import socket
import json
import psycopg2

# Define global variables to store directory paths
directories = {
    "Characteristics": {
        "pressure": "",
        "XRD": "",
        "FTIR": "",
        "TGA": ""
    },
    "BenchTop Filament Diameter": "",
    "Live Print Data": ""
}

# Establish a connection with the PostgreSQL database
def connect_to_database():
    try:
        # Define database parameters
        db_params = {
            'dbname': 'postgres',
            'user': 'postgres',
            'password': 'x',  # Update with your actual password
            'host': 'localhost',
            'port': '5432',
        }

        # Establish a database connection
        conn = psycopg2.connect(**db_params)
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)
        return None

def handle_client(client_socket, conn):
    global directories

    # Receive data from the client
    data = client_socket.recv(1024).decode()

    try:
        # Decode JSON data
        data = json.loads(data)
    except json.JSONDecodeError as e:
        print("Error decoding JSON data:", e)
        client_socket.send("Invalid JSON data received".encode())
        client_socket.close()
        return

    # Extract the selected directories
    selected_directories = data.get('selected_directories', {})

    # Store the selected directories
    for purpose, directory_path in selected_directories.items():
        if purpose == "Characteristics":
            if isinstance(directory_path, dict):
                for sub_purpose, sub_directory_path in directory_path.items():
                    if "pressure" in sub_directory_path.lower():
                        directories["Characteristics"]["pressure"] = sub_directory_path
                    elif sub_purpose in directories["Characteristics"]:
                        directories["Characteristics"][sub_purpose] = sub_directory_path
            else:
                # Store the directory path directly under "pressure" if it's not a dictionary
                directories["Characteristics"]["pressure"] = directory_path
        elif purpose in directories:
            directories[purpose] = directory_path

    # Print received data (for demonstration purposes)
    print("Selected directories:", directories)

    # Perform database operations
    if conn:
        try:
            # Execute SQL queries here
            # Example: cursor = conn.cursor()
            # Example: cursor.execute("INSERT INTO table_name (column1, column2) VALUES (%s, %s)", (value1, value2))
            # Example: conn.commit()
            print("Database connection established. Perform database operations here.")
        except psycopg2.Error as e:
            print("Error executing SQL query:", e)

    # Send acknowledgment to the client
    client_socket.send("Data received successfully".encode())

    # Close the client socket
    client_socket.close()

def main():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a specific address and port
    server_socket.bind(('localhost', 5555))

    # Listen for incoming connections
    server_socket.listen(5)
    print("Server is listening for connections...")

    # Establish connection with PostgreSQL database
    conn = connect_to_database()

    try:
        while True:
            # Accept a new connection
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")

            # Handle the client in a separate thread or process
            handle_client(client_socket, conn)
    except KeyboardInterrupt:
        print("Server shutting down...")
        # Close the server socket
        server_socket.close()
        # Close the database connection
        if conn:
            conn.close()

if __name__ == '__main__':
    main()

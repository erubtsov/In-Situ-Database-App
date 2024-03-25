import socket
import json
from threading import Thread, Lock
from database_operations import connect_to_database, load_parts_id, query_parts, query_materials

upload_lock = Lock()  # Lock for thread safety

def handle_client(client_socket, conn):
    print("Client connected.")

    authenticated = False

    while True:
        if not authenticated:
            # Receive password
            password_data = client_socket.recv(1024).decode()
            password = json.loads(password_data).get('password', '')
            print("Received password:", password)

            # Check if password is correct
            if not conn:
                conn = connect_to_database(password)
                if conn:
                    client_socket.send("Correct".encode())
                    authenticated = True
                    print("Password correct.")
                else:
                    client_socket.send("Incorrect".encode())
                    print("Password incorrect.")
                    continue  # Retry password

        else:  # Authenticated, waiting for commands
            # Receive data from the client
            data = client_socket.recv(1024).decode()
            if not data:
                # Handle empty data
                print("Received empty data from client.")
                continue

            try:
                data_json = json.loads(data)
            except json.JSONDecodeError as e:
                # Handle JSON decoding error
                print("Error decoding JSON data:", e)
                continue

            print("Received data:", data_json)

            # Extract command from the received data
            command = data_json.get('command', '')
            print("Received command:", command)

            if command == "DataUpload":
                print("Received command: DataUpload")
                selected_directories = data_json.get('selected_directories', None)
                if selected_directories:
                    # Handle data upload command with selected directories
                    upload_thread = Thread(target=upload_data, args=(client_socket, selected_directories))
                    upload_thread.start()
                else:
                    print("No directories selected for upload.")

            elif command == "QueryDatabase":
                print("Received command: QueryDatabase")
                # Handle query database command in the current thread
                query_database(client_socket, conn)  # Pass the connection object

            elif command == "TerminateConnection":
                print("Received termination signal. Terminating connection.")
                break  # Break out of the inner loop to close the connection

            else:
                print("Invalid command received.")

    # Close the client connection
    print("Closing client connection.")
    client_socket.close()

def query_database(client_socket, conn):
    # Query database logic
    # Example: sending query result to client
    query_result = query_parts(conn)  # Pass the connection object
    client_socket.send(json.dumps(query_result).encode())

def upload_data(client_socket, selected_directories):
    with upload_lock:
        # Upload data logic
        print("Uploading Data...")
        # Process the upload with selected_directories
        print("Data uploaded successfully.")
    # Send confirmation to the client after the upload operation completes
    client_socket.send("DataUploaded".encode())

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5555))
    server_socket.listen(5)
    print("Server is listening for connections...")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            # Create a new thread for each client connection
            client_thread = Thread(target=handle_client, args=(client_socket, None))
            client_thread.start()
            
    except KeyboardInterrupt:
        print("Server shutting down...")
        server_socket.close()

if __name__ == "__main__":
    main()

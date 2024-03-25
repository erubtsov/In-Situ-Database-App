import socket
import json
from threading import Thread
from database_operations import connect_to_database, load_parts_id, query_parts, query_materials

def handle_client(client_socket, conn):
    print("Client connected.")

    authenticated = False
    selected_directories = None

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
                if selected_directories:
                    # Handle data upload command with selected directories
                    print("Uploading Data...")
                    # Process the upload with selected_directories
                    print("Data uploaded successfully.")
                    selected_directories = None  # Reset selected directories after upload
                else:
                    print("Please select directories before uploading data.")

            elif command == "QueryDatabase":
                print("Received command: QueryDatabase")
                # Handle query database command in a separate thread
                query_thread = Thread(target=query_database, args=(client_socket,))
                query_thread.start()

            elif command == "SelectedDirectories":
                print("Received selected directories:", data_json.get('directories', ''))
                selected_directories = data_json.get('directories', '')

            elif command == "TerminateConnection":
                print("Received termination signal. Terminating connection.")
                break  # Break out of the inner loop to close the connection

            else:
                print("Invalid command received.")

    # Close the client connection
    print("Closing client connection.")
    client_socket.close()


def query_database(client_socket):
    # Query database logic
    # Example: sending query result to client
    query_result = ['result1', 'result2', 'result3']  # Placeholder result
    client_socket.send(json.dumps(query_result).encode())

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

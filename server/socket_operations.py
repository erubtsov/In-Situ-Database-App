import socket
import json
from concurrent.futures import ThreadPoolExecutor
from database_operations import connect_to_database, process_files_in_directory
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_client(client_socket):
    logging.info("Client connected.")
    conn = None

    try:
        # Keep listening for data from client
        while True:
            # Receive data from the client
            data = client_socket.recv(1024).decode()
            if not data:
                logging.info("No data received. Closing connection.")
                break

            data_json = json.loads(data)
            # Handling based on command
            if 'password' in data_json:
                # This assumes your password verification logic is moved here
                password = data_json['password']
                conn = connect_to_database(password)
                if conn:
                    response = {"status": "Correct"}
                    logging.info("Password correct. Database connection established.")
                else:
                    response = {"status": "Incorrect"}
                    logging.info("Password incorrect. No database connection.")
                client_socket.sendall(json.dumps(response).encode())

            elif data_json.get('command') == 'DataUpload':
                logging.info("Received command: DataUpload")
                selected_directories = data_json.get('selected_directories', {})
                if conn:
                    upload_data(client_socket, selected_directories, conn)
                else:
                    logging.error("No database connection established for data upload.")
                    client_socket.sendall(json.dumps({"status": "Error", "message": "No DB connection"}).encode())

            elif data_json.get('command') == 'TerminateConnection':
                logging.info("Received termination signal. Terminating connection.")
                break

    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
        client_socket.close()
        logging.info("Client connection closed.")

def upload_data(client_socket, selected_directories, conn):
    logging.info("Starting data upload process...")
    process_files_in_directory(selected_directories, conn)
    client_socket.sendall(json.dumps({"status": "DataUploaded"}).encode())
    logging.info("Data upload process completed.")

# Main server function
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5555))
    server_socket.listen(5)
    logging.info("Server is listening for connections...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        try:
            while True:
                client_socket, _ = server_socket.accept()
                logging.info("Client connection established.")
                executor.submit(handle_client, client_socket)
        except KeyboardInterrupt:
            logging.info("Server shutting down...")
    server_socket.close()

if __name__ == "__main__":
    main()

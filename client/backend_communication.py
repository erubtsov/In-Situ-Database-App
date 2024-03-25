import socket
import json
from frontend_components import QueryResultPopup

class BackendCommunication:
    def __init__(self):
        self.backend_socket = None
        self.password = None
        print("BackendCommunication initialized")

    def connect_to_backend(self):
        try:
            self.backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.backend_socket.connect(("localhost", 5555))
            print("Connected to backend server.")
        except ConnectionRefusedError:
            print("Error: Connection refused. Make sure the backend server is running.")
        except Exception as e:
            print("Error connecting to backend:", e)

    def verify_password(self, password):
        try:
            if self.backend_socket is None:
                self.connect_to_backend()

            data = {"password": password}
            self.backend_socket.send(json.dumps(data).encode())
            response = self.backend_socket.recv(1024).decode()
            if response == "Correct":
                self.password = password
                return True
            else:
                return False
        except Exception as e:
            print("Error verifying password:", e)
            return False

    def upload_data(self, selected_directories, password):
        try:
            if self.backend_socket is None:
                self.connect_to_backend()

            if self.verify_password(password):  # Verify password before uploading data
                if any(selected_directories.values()):
                    print("Uploading Data...")
                    data = {
                        "selected_directories": selected_directories,
                        "command": "DataUpload"
                    }
                    print("Data to be sent to backend:", data)
                    self.backend_socket.send(json.dumps(data).encode())
                    print("Data uploaded successfully.")
                else:
                    print("Please select at least one directory before uploading data.")
            else:
                print("Password verification failed. Please submit the correct password.")
        except Exception as e:
            print("Error uploading data:", e)

    def retry_callback_with_arg(self, password):
        self.verify_password(password)

    def query_database(self):
        try:
            print("Query Database button clicked.")
            if self.backend_socket is None:
                self.connect_to_backend()

            data = {"command": "QueryDatabase"}
            print("Sending query to backend...")
            self.backend_socket.send(json.dumps(data).encode())

            query_result = self.backend_socket.recv(4096).decode()

            try:
                part_ids = json.loads(query_result)
                print("Received query result from backend:", part_ids)
                popup = QueryResultPopup(query_result=part_ids)
                popup.open()
            except json.JSONDecodeError as e:
                print("Error decoding JSON:", e)
        except Exception as e:
            print("Error querying database:", e)

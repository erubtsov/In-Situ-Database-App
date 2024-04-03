import socket
import json

class BackendCommunication:
    def __init__(self, query_result_popup_callback):
        self.backend_socket = None
        self.query_result_popup_callback = query_result_popup_callback
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

            data = {"command": "VerifyPassword", "password": password}
            self.backend_socket.send(json.dumps(data).encode())
            response = self.backend_socket.recv(1024).decode()
            if response == "Correct":
                return True
            else:
                return False
        except Exception as e:
            print("Error verifying password:", e)
            return False

    def upload_data(self, selected_directories):
        try:
            if self.backend_socket is None:
                self.connect_to_backend()

            data = {
                "command": "DataUpload",
                "selected_directories": selected_directories
            }
            print("Sending data upload request to the backend:", data)  # Debug print
            self.backend_socket.send(json.dumps(data).encode())
            print("Data upload request sent to the backend.")

            # Receive confirmation from the server
            response = self.backend_socket.recv(1024).decode()
            print("Received response from the server:", response)  # Debug print
            if response == "DataUploaded":
                print("Data uploaded successfully.")
                # Optionally, you can trigger an event/callback to enable the upload button
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
                self.query_result_popup_callback(query_result=part_ids)
            except json.JSONDecodeError as e:
                print("Error decoding JSON:", e)
        except Exception as e:
            print("Error querying database:", e)

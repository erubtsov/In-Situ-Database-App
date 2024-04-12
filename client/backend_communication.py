import socket
import json

class BackendCommunication:
    def __init__(self):
        self.backend_socket = None
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
        self.connect_to_backend()  # Ensure connection is established
        try:
            if self.backend_socket:
                data = {"password": password}  # Adjusted to match backend expectations
                self.backend_socket.send(json.dumps(data).encode())
                response = self.backend_socket.recv(1024).decode()
                response_json = json.loads(response)  # Parse the JSON response
                print(f"Received password verification response: {response}")
                # Check the status in the JSON response
                if response_json.get("status") == "Correct":
                    print("Password correct. Connection established.")
                    return True
                else:
                    print("Password incorrect. Please try again.")
                    return False
        except Exception as e:
            print(f"Error verifying password: {e}")
            return False

    def upload_data(self, selected_directories):
        try:
            if self.backend_socket is None:
                self.connect_to_backend()

            data = {
                "command": "DataUpload",
                "selected_directories": selected_directories
            }
            print("Sending data upload request to the backend:", data)
            self.backend_socket.send(json.dumps(data).encode())
            print("Data upload request sent to the backend.")

            # Receive confirmation from the server
            response = self.backend_socket.recv(1024).decode()
            print("Received response from the server:", response)
            if response == "DataUploaded":
                print("Data uploaded successfully.")
        except Exception as e:
            print("Error uploading data:", e)

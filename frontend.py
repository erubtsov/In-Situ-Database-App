from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
import socket
import json

class PasswordPopup(Popup):
    def __init__(self, callback, **kwargs):
        super(PasswordPopup, self).__init__(**kwargs)
        self.callback = callback
        self.title = "Enter Database Password"
        self.size_hint = (0.6, 0.4)

        # Create a box layout for the content
        layout = BoxLayout(orientation='vertical', padding=10)

        # Add a label
        label = Label(text="Enter password:")
        layout.add_widget(label)

        # Add a text input for the password
        self.password_input = TextInput(text="", multiline=False, password=True)
        layout.add_widget(self.password_input)

        # Add a button to submit the password
        submit_button = Button(text="Submit")
        submit_button.bind(on_press=self.submit_password)
        layout.add_widget(submit_button)

        self.content = layout

    def submit_password(self, instance):
        password = self.password_input.text
        if password:
            self.callback(password)
            self.dismiss()

class ErrorPopup(Popup):
    def __init__(self, error_message, on_retry, retry_callback, **kwargs):
        super(ErrorPopup, self).__init__(**kwargs)
        self.title = "Error"
        self.size_hint = (0.6, 0.4)
        self.on_retry = on_retry  # Callback function for retrying password
        self.retry_callback = retry_callback  # Callback function to send retry signal to backend

        # Create a box layout for the content
        layout = BoxLayout(orientation='vertical', padding=10)

        # Add a label to display the error message
        label = Label(text=error_message)
        layout.add_widget(label)

        # Add a button to allow retrying password
        retry_button = Button(text="Retry")
        retry_button.bind(on_press=self.retry_password)  # Bind directly to the function
        layout.add_widget(retry_button)

        self.content = layout

    def retry_password(self, instance):
        self.on_retry()  # Call the retry function
        self.retry_callback()  # Send the retry signal to the backend
        self.dismiss()  # Dismiss the popup

class DirectorySelectPopup(Popup):
    def __init__(self, callback, purpose, **kwargs):
        super(DirectorySelectPopup, self).__init__(**kwargs)
        self.callback = callback
        self.purpose = purpose
        self.title = "Select Directory"
        self.size_hint = (0.8, 0.8)

        # Create a box layout for the content
        layout = BoxLayout(orientation='vertical', padding=10)

        # Add a label
        label = Label(text="Select a directory:")
        layout.add_widget(label)

        # Add a text input for directory path
        self.text_input = TextInput(text="", multiline=False)
        layout.add_widget(self.text_input)

        # Add a button to open the directory selector
        browse_button = Button(text="Browse")
        browse_button.bind(on_press=self.select_directory)
        layout.add_widget(browse_button)

        # Add a button to select the directory and close the popup
        select_button = Button(text="Select")
        select_button.bind(on_press=self.select_and_close)
        layout.add_widget(select_button)

        self.content = layout

    def select_directory(self, instance):
        # Open a directory selector
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()  # Hide the main window
        directory_path = filedialog.askdirectory()
        root.destroy()  # Destroy the root window after selection

        if directory_path:
            self.text_input.text = directory_path

    def select_and_close(self, instance):
        directory_path = self.text_input.text
        self.callback(directory_path, self.purpose)
        self.dismiss()

class QueryResultPopup(Popup):
    def __init__(self, query_result, **kwargs):
        super(QueryResultPopup, self).__init__(**kwargs)
        self.title = "Query Result"
        self.size_hint = (0.8, 0.8)

        # Create a GridLayout for the content
        layout = GridLayout(cols=1, padding=10)

        # Add labels to display the query results
        for result in query_result:
            label = Label(text=result)
            layout.add_widget(label)

        self.content = layout

class ViewUploadDetailsPopup(Popup):
    def __init__(self, **kwargs):
        super(ViewUploadDetailsPopup, self).__init__(**kwargs)
        self.title = "Upload Details"
        self.size_hint = (0.8, 0.8)

        layout = BoxLayout(orientation='vertical', padding=10)
        label = Label(text="Upload Details Placeholder")  # You can replace this with actual details
        layout.add_widget(label)

        close_button = Button(text="Close")
        close_button.bind(on_press=self.dismiss)
        layout.add_widget(close_button)

        self.content = layout


class PostgreSQLApp(App):
    def __init__(self, **kwargs):
        super(PostgreSQLApp, self).__init__(**kwargs)
        self.selected_directories = {
            "Characteristics": "",
            "BenchTop Filament Diameter": "",
            "Live Print Data": "",
            "Parts Quality": ""
        }
        self.backend_socket = None  # Initialize backend socket to None
        self.password = None

    def connect_to_backend(self):
        self.backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.backend_socket.connect(("localhost", 5555))

    def select_directory_callback(self, directory_path, purpose):
        self.selected_directories[purpose] = directory_path
        print(f"Selected {purpose} directory:", directory_path)

    def query_database(self, instance):
        # Placeholder for querying the database
        query_result = ["Result 1", "Result 2", "Result 3"]  # Example query result
        popup = QueryResultPopup(query_result=query_result)
        popup.open()

    def view_upload_details(self, instance):
        popup = ViewUploadDetailsPopup()
        popup.open()

    def upload_data(self):
        if self.backend_socket is None:  # Check if the backend socket is not connected
            self.connect_to_backend()

        # Check if at least one directory is selected
        if any(self.selected_directories.values()):
            print("Uploading Data...")
            # Prepare data to send to the backend
            data = {
                "selected_directories": self.selected_directories,
                "password": self.password,
                "signal": "DataUpload"  # Add the signal here
            }
            print("Data to be sent to backend:", data)  # Add this line for debugging
            # Send data to the backend
            self.backend_socket.send(json.dumps(data).encode())
            print("Data uploaded successfully.")
        else:
            print("Please select at least one directory before uploading data.")

    def build(self):
        self.layout = BoxLayout(orientation='vertical')

        # Add password input button
        self.open_password_popup()

        return self.layout

    def open_directory_selector(self, purpose):
        popup = DirectorySelectPopup(callback=self.select_directory_callback, purpose=purpose)
        popup.bind(on_dismiss=lambda instance: self.update_button_text(purpose, instance.text_input.text))
        popup.open()

    def update_button_text(self, purpose, directory_path):
        for widget in self.layout.children:
            if isinstance(widget, Button) and f"Select {purpose} Directory" in widget.text:
                widget.text = f"Selected Path: {directory_path}" if directory_path else f"Select {purpose} Directory"

    def open_password_popup(self):
        popup = PasswordPopup(callback=self.verify_password)
        popup.open()

    def verify_password(self, password):
        self.password = password
        # Check if the backend socket is not connected
        if self.backend_socket is None:
            # If not connected, establish the connection
            self.connect_to_backend()

        # Send the password to the backend for verification
        data = {"password": self.password}
        self.backend_socket.send(json.dumps(data).encode())
        response = self.backend_socket.recv(1024).decode()
        if response == "Correct":
            self.show_buttons()
        else:
            self.show_password_error()

    def show_buttons(self):
        # Clear existing widgets
        self.layout.clear_widgets()

        # Add directory selection buttons
        for purpose in self.selected_directories.keys():
            select_button = Button(text=f"Select {purpose} Directory")
            select_button.bind(on_press=lambda instance, purpose=purpose: self.open_directory_selector(purpose))
            self.layout.add_widget(select_button)

        # Add a horizontal layout for query, view details, and upload buttons
        buttons_layout = BoxLayout(orientation='horizontal')

        # Add Query Database Button
        query_button = Button(text="Query Database")
        query_button.bind(on_press=self.query_database)
        buttons_layout.add_widget(query_button)

        # Add View Upload Details Button
        view_details_button = Button(text="View Upload Details")
        view_details_button.bind(on_press=self.view_upload_details)
        buttons_layout.add_widget(view_details_button)

        # Add Upload Data Button
        upload_button = Button(text="Upload Data")
        upload_button.bind(on_press=lambda instance: self.upload_data())
        buttons_layout.add_widget(upload_button)

        self.layout.add_widget(buttons_layout)

    def show_password_error(self):
        def retry_password():
            self.open_password_popup()

        def retry_callback():
            if self.backend_socket is None:  # Check if the backend socket is not connected
                self.connect_to_backend()
            data = {"retry": "RetryPassword"}
            self.backend_socket.send(json.dumps(data).encode())

        error_popup = ErrorPopup(
            error_message="Incorrect password. Please try again.",
            on_retry=retry_password,
            retry_callback=retry_callback  # Pass the retry callback
        )
        error_popup.open()

    def on_stop(self):
        if self.backend_socket is not None:
            self.backend_socket.close()  # Close the backend socket when the application is stopped

if __name__ == '__main__':
    PostgreSQLApp().run()


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from frontend_components import PasswordPopup, ErrorPopup, DirectorySelectPopup, QueryResultPopup, ViewUploadDetailsPopup
from backend_communication import BackendCommunication
from kivy.utils import get_color_from_hex

class PostgreSQLApp(App):
    def __init__(self, **kwargs):
        super(PostgreSQLApp, self).__init__(**kwargs)
        self.backend_communication = None
        self.query_result_popup = None
        self.password_popup = None
        self.password = None
        self.selected_directories = {
            "Characteristics": "",
            "BenchTop Filament Diameter": "",
            "Live Print Data": "",
            "Parts Quality": ""
        }
        self.query_database = None
        self.uploading_data = False  # Track if data is being uploaded
        self.buttons = {}  # Dictionary to store buttons
        
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.open_password_popup()
        return self.layout

    def open_password_popup(self):
        self.password_popup = PasswordPopup(callback=self.submit_password)
        self.password_popup.open()

    def show_query_result_popup(self, query_result):
        self.query_result_popup = QueryResultPopup(query_result=query_result)
        self.query_result_popup.open()

    def submit_password(self, password):
        self.backend_communication = BackendCommunication(query_result_popup_callback=self.show_query_result_popup)
        if self.backend_communication.verify_password(password):
            print("Password correct. You can now upload data.")
            self.query_database = self.backend_communication.query_database
            self.show_buttons()
        else:
            print("Incorrect password. Please try again.")
            self.show_password_error()

    def reset_selected_directories(self):
        for key in self.selected_directories.keys():
            self.selected_directories[key] = ""

    def upload_data(self):
        if not any(self.selected_directories.values()):
            # If no directories have been selected, notify the user.
            print("Please select at least one directory before uploading data.")
            return  # Exit the function early.

        if self.uploading_data:
            # If an upload is already in progress, notify the user and don't start another.
            print("Data upload in progress. Please wait.")
            return

        # Set uploading flag to True to prevent another upload from starting.
        self.uploading_data = True

        # Perform the upload operation.
        try:
            self.backend_communication.upload_data(self.selected_directories)
        finally:
            # Reset the uploading flag and selected directories after the operation, regardless of success.
            self.uploading_data = False
            self.reset_selected_directories()
        
    def view_upload_details(self):
        popup = ViewUploadDetailsPopup()
        popup.open()

    def open_directory_selector(self, purpose):
        popup = DirectorySelectPopup(callback=self.select_directory_callback, purpose=purpose)
        popup.open()

    def select_directory_callback(self, data):
            purpose = data["purpose"]
            selected_dir = data["directory_path"]
            self.directory_selected(selected_dir, purpose)
            print("Selected Directories:", self.selected_directories)  # Print selected directories

    def directory_selected(self, selected_dir, purpose):
            if selected_dir:
                self.selected_directories[purpose] = selected_dir  # Remove [0] to get the full directory path
                self.update_button_text(f"Select {purpose} Directory", selected_dir, purpose)  # Update button text
                print(f"Selected {purpose} Directory:", selected_dir)  # Print selected directory

    def update_button_text(self, button_text, directory_path, purpose):
        button = self.buttons.get(button_text)
        if button:
            button.text = f"Selected Path: {directory_path}" if directory_path else f"Select {purpose} Directory"
    
    def show_buttons(self):
        self.layout.clear_widgets()

        # Create a GridLayout for the top rows
        top_rows_layout = BoxLayout(orientation='vertical')

        button_texts = [f"Select {purpose} Directory" for purpose in self.selected_directories.keys()]
        button_callbacks = [lambda instance, purpose=purpose: self.open_directory_selector(purpose) for purpose in self.selected_directories.keys()]
        purposes = list(self.selected_directories.keys())  # Get the list of purposes
        purposes.extend([None] * 3)  # Add None for the additional buttons

        # Add the "Select Directory" buttons to the top rows layout
        for text, callback in zip(button_texts, button_callbacks):
            button = Button(text=text)  # Create button instance
            button.bind(on_press=callback)  # Bind callback function
            button.disabled_color = get_color_from_hex("#808080")  # Set the disabled color
            self.buttons[text] = button  # Store the button in the dictionary
            top_rows_layout.add_widget(button)  # Add button to top rows layout

        # Add the top rows layout to the main layout
        self.layout.add_widget(top_rows_layout)

        # Create a BoxLayout for the bottom row
        bottom_row_layout = BoxLayout(orientation='horizontal')

        # Add the "Query Database", "View Upload Details", and "Upload Data" buttons to the bottom row layout
        button_texts = ["Query Database", "View Upload Details", "Upload Data"]
        button_callbacks = [
            lambda instance, callback=self.query_database: callback(),
            self.view_upload_details,
            lambda instance: self.upload_data()
        ]

        for text, callback in zip(button_texts, button_callbacks):
            button = Button(text=text)  # Create button instance
            button.bind(on_press=lambda instance, callback=callback: callback(instance))
            button.disabled_color = get_color_from_hex("#808080")  # Set the disabled color
            self.buttons[text] = button  # Store the button in the dictionary
            bottom_row_layout.add_widget(button)  # Add button to bottom row layout

        # Add the bottom row layout to the main layout
        self.layout.add_widget(bottom_row_layout)

    def show_password_error(self):
        error_popup = ErrorPopup(
            error_message="Incorrect password. Please try again.",
            on_retry=self.open_password_popup
        )
        error_popup.open()

if __name__ == '__main__':
    PostgreSQLApp().run()

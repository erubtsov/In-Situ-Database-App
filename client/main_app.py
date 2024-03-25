# main_app.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from frontend_components import PasswordPopup, ErrorPopup, DirectorySelectPopup, QueryResultPopup, ViewUploadDetailsPopup, ButtonDisplay
from backend_communication import BackendCommunication

class PostgreSQLApp(App):
    def __init__(self, **kwargs):
        super(PostgreSQLApp, self).__init__(**kwargs)
        self.backend_communication = None
        self.password_popup = None
        self.password = None
        self.selected_directories = {
            "Characteristics": "",
            "BenchTop Filament Diameter": "",
            "Live Print Data": "",
            "Parts Quality": ""
        }
        self.on_stop = None  # Define on_stop attribute here
        self.query_database = None
        
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.open_password_popup()
        return self.layout

    def open_password_popup(self):
        self.password_popup = PasswordPopup(callback=self.submit_password)
        self.password_popup.open()

    def submit_password(self, password):
        self.backend_communication = BackendCommunication()  # Instantiate the BackendCommunication object
        if self.backend_communication.verify_password(password):
            print("Password correct. You can now upload data.")
            self.query_database = self.backend_communication.query_database
            self.show_buttons()
        else:
            print("Incorrect password. Please try again.")
            self.show_password_error()

    def upload_data(self):
        if self.password is None:
            print("Please submit password first.")
            return

        if any(self.selected_directories.values()):
            self.backend_communication.upload_data(self.selected_directories, self.password)
        else:
            print("Please select at least one directory before uploading data.")
    
    def view_upload_details(self):
        popup = ViewUploadDetailsPopup()
        popup.open()

    def open_directory_selector(self, purpose):
        popup = DirectorySelectPopup(callback=self.select_directory_callback, purpose=purpose)
        popup.bind(on_dismiss=lambda instance: self.update_button_text(purpose, instance.text_input.text))
        popup.open()

    def select_directory_callback(self, directory_path, purpose):
        self.selected_directories[purpose] = directory_path
        print(f"Selected {purpose} directory:", directory_path)

    def update_button_text(self, purpose, directory_path):
        for widget in self.layout.children:
            if isinstance(widget, Button) and f"Select {purpose} Directory" in widget.text:
                widget.text = f"Selected Path: {directory_path}" if directory_path else f"Select {purpose} Directory"

    def show_buttons(self):
        self.layout.clear_widgets()

        button_texts = [f"Select {purpose} Directory" for purpose in self.selected_directories.keys()] + ["Query Database", "View Upload Details", "Upload Data"]
        button_callbacks = [lambda instance, purpose=purpose: self.open_directory_selector(purpose) for purpose in self.selected_directories.keys()] + [self.query_database, self.view_upload_details, lambda instance: self.upload_data()]
        buttons_layout = ButtonDisplay(
                button_texts=button_texts, 
                button_callbacks=button_callbacks, 
                backend_callback=self.backend_communication.connect_to_backend
                )
        self.layout.add_widget(buttons_layout)

    def show_password_error(self):
        error_popup = ErrorPopup(
            error_message="Incorrect password. Please try again.",
            on_retry=self.open_password_popup
        )
        error_popup.open()

if __name__ == '__main__':
    PostgreSQLApp().run()

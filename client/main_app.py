from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import webbrowser
from frontend_components import PasswordPopup, ErrorPopup, DirectorySelectPopup, ViewUploadDetailsPopup
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
        self.uploading_data = False  # Track if data is being uploaded
        self.buttons = {}  # Dictionary to store buttons

    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.open_password_popup()
        return self.layout

    def open_password_popup(self):
        self.password_popup = PasswordPopup(callback=self.submit_password)
        self.password_popup.open()

    def submit_password(self, password):
        self.backend_communication = BackendCommunication()
        if self.backend_communication.verify_password(password):
            print("Password correct. You can now upload data.")
            self.show_buttons()
        else:
            print("Incorrect password. Please try again.")
            self.show_password_error()

    def reset_selected_directories(self):
        for key in self.selected_directories.keys():
            self.selected_directories[key] = ""

    def upload_data(self):
        if not any(self.selected_directories.values()):
            print("Please select at least one directory before uploading data.")
            return
        if self.uploading_data:
            print("Data upload in progress. Please wait.")
            return
        self.uploading_data = True
        try:
            self.backend_communication.upload_data(self.selected_directories)
        finally:
            self.uploading_data = False
            self.reset_selected_directories()

    def open_directory_selector(self, purpose):
        popup = DirectorySelectPopup(callback=self.select_directory_callback, purpose=purpose)
        popup.open()

    def select_directory_callback(self, data):
        purpose = data["purpose"]
        selected_dir = data["directory_path"]
        self.directory_selected(selected_dir, purpose)
        print("Selected Directories:", self.selected_directories)

    def directory_selected(self, selected_dir, purpose):
        if selected_dir:
            self.selected_directories[purpose] = selected_dir
            self.update_button_text(f"Select {purpose} Directory", selected_dir, purpose)
            print(f"Selected {purpose} Directory:", selected_dir)

    def update_button_text(self, button_text, directory_path, purpose):
        button = self.buttons.get(button_text)
        if button:
            button.text = f"Selected Path: {directory_path}" if directory_path else f"Select {purpose} Directory"

    def show_buttons(self):
        self.layout.clear_widgets()
        top_rows_layout = BoxLayout(orientation='vertical')
        button_texts = [f"Select {purpose} Directory" for purpose in self.selected_directories.keys()]
        button_callbacks = [lambda instance, purpose=purpose: self.open_directory_selector(purpose) for purpose in self.selected_directories.keys()]

        for text, callback in zip(button_texts, button_callbacks):
            button = Button(text=text)
            button.bind(on_press=callback)
            self.buttons[text] = button
            top_rows_layout.add_widget(button)
        self.layout.add_widget(top_rows_layout)

        bottom_row_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)

        view_data_button = Button(text="View Data", size_hint_y=None, height=100)
        view_data_button.bind(on_press=lambda instance: self.open_web_app())

        view_details_button = Button(text="View Upload Details", size_hint_y=None, height=100)
        view_details_button.bind(on_press=self.view_upload_details)

        upload_button = Button(text="Upload Data", size_hint_y=None, height=100)
        upload_button.bind(on_press=lambda instance: self.upload_data())

        bottom_row_layout.add_widget(view_data_button)
        bottom_row_layout.add_widget(view_details_button)
        bottom_row_layout.add_widget(upload_button)

        self.layout.add_widget(bottom_row_layout)

    def open_web_app(self):
        webbrowser.open('http://yourwebapp.com')  # Update with your web application's URL

    def view_upload_details(self, instance):
        popup = ViewUploadDetailsPopup()
        popup.open()

    def show_password_error(self):
        error_popup = ErrorPopup(
            error_message="Incorrect password. Please try again.",
            on_retry=self.open_password_popup
        )
        error_popup.open()

if __name__ == '__main__':
    PostgreSQLApp().run()

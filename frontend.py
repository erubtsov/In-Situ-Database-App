import socket
import json
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout


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
        if directory_path:
            self.callback(directory_path, self.purpose)
            self.dismiss()


class PostgreSQLApp(App):
    def __init__(self, **kwargs):
        super(PostgreSQLApp, self).__init__(**kwargs)
        self.selected_directories = {
            "Characteristics": "",
            "BenchTop Filament Diameter": "",
            "Live Print Data": ""
        }
        self.backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.backend_socket.connect(("localhost", 5555))

    def select_directory_callback(self, directory_path, purpose):
        self.selected_directories[purpose] = directory_path
        print(f"Selected {purpose} directory:", directory_path)

    def upload_data(self):
        print("Uploading Data...")
        # Prepare data to send to the backend
        data = {
            "selected_directories": self.selected_directories
        }
        # Send data to the backend
        self.backend_socket.send(json.dumps(data).encode())
        print("Data uploaded successfully.")

    def build(self):
        layout = BoxLayout(orientation='vertical')

        # Add directory selection buttons
        for purpose in self.selected_directories.keys():
            select_button = Button(text=f"Select {purpose} Directory")
            select_button.bind(on_press=lambda instance, purpose=purpose: self.open_directory_selector(purpose))
            layout.add_widget(select_button)

        # Add upload button to the main layout
        upload_button = Button(text="Upload Data")
        upload_button.bind(on_press=lambda instance: self.upload_data())
        layout.add_widget(upload_button)

        return layout

    def open_directory_selector(self, purpose):
        popup = DirectorySelectPopup(callback=self.select_directory_callback, purpose=purpose)
        popup.bind(on_dismiss=lambda instance: self.update_button_text(purpose, instance.text_input.text))
        popup.open()

    def update_button_text(self, purpose, directory_path):
        for widget in self.root.children:
            if isinstance(widget, Button) and f"Select {purpose} Directory" in widget.text:
                widget.text = f"Selected Path: {directory_path}" if directory_path else f"Select {purpose} Directory"


if __name__ == '__main__':
    PostgreSQLApp().run()

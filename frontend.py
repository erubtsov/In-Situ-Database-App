import socket
import json
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout


class DirectorySelectPopup(Popup):
    def __init__(self, callback, **kwargs):
        super(DirectorySelectPopup, self).__init__(**kwargs)
        self.callback = callback
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
        button = Button(text="Browse")
        button.bind(on_press=self.select_directory)
        layout.add_widget(button)

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
            self.callback(directory_path)
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
        popup = DirectorySelectPopup(callback=lambda directory_path: self.select_directory_callback(directory_path, purpose))
        popup.open()


if __name__ == '__main__':
    PostgreSQLApp().run()

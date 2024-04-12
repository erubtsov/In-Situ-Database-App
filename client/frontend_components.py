from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.dropdown import DropDown
from kivy.utils import platform
import tkinter as tk
from tkinter import filedialog
from kivy.properties import BooleanProperty
from kivy.utils import get_color_from_hex


class ButtonDisplay(BoxLayout):
    def __init__(self, button_texts, button_callbacks, backend_callback, purposes=None, **kwargs):
        super(ButtonDisplay, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.backend_callback = backend_callback
        self.buttons = {}  # Dictionary to store buttons

        for text, callback, purpose in zip(button_texts, button_callbacks, purposes):
            button = Button(text=text)
            button.bind(on_press=lambda instance, cmd=text: self.send_command(cmd, purpose))
            self.buttons[text] = button  # Store the button in the dictionary
            self.add_widget(button)

    def send_command(self, command, purpose):
        if purpose is not None:
            self.backend_callback() 

    def update_button_text(self, button_text, directory_path, purpose):
        button = self.buttons.get(button_text)  # Retrieve the button instance from the dictionary
        if button:
            if directory_path:  # If a directory path is selected
                button.text = f"Selected Path: {directory_path}"  # Update button text to display selected path
            else:  # If no directory path is selected
                button.text = f"Select {purpose} Directory"  # Update button text to prompt user to select directory
                    
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
        root = tk.Tk()
        root.withdraw()  # Hide the main window

        directory_path = filedialog.askdirectory()
        if directory_path:
            self.text_input.text = directory_path

    def select_and_close(self, instance):
        directory_path = self.text_input.text
        if directory_path:
            data = {"purpose": self.purpose, "directory_path": directory_path}
            self.callback(data)  # Send data to the callback
            self.dismiss()  # Close the popup after selection

class ViewUploadDetailsPopup(Popup):
    def __init__(self, **kwargs):
        super(ViewUploadDetailsPopup, self).__init__(**kwargs)
        self.title = "Upload Details"
        self.size_hint = (0.8, 0.8)

        layout = BoxLayout(orientation='vertical', padding=10)
        label = Label(text="Upload Details Placeholder")  # Placeholder text
        layout.add_widget(label)

        close_button = Button(text="Close")
        close_button.bind(on_press=self.dismiss)
        layout.add_widget(close_button)

        self.content = layout


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
    def __init__(self, error_message, on_retry, **kwargs):
        super(ErrorPopup, self).__init__(**kwargs)
        self.title = "Error"
        self.size_hint = (0.6, 0.4)
        self.on_retry = on_retry  # Callback function for retrying password

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
        self.dismiss()  # Dismiss the error popup

class ViewUploadDetailsPopup(Popup):
    def __init__(self, **kwargs):
        super(ViewUploadDetailsPopup, self).__init__(**kwargs)
        self.title = 'Custom Popup Window'
        self.size_hint = (None, None)
        self.size = (400, 400)  # Specify the size of the popup
        self.content = Label(text='This is a custom popup!')

class ViewDataPopup(Popup):
    def __init__(self, **kwargs):
        super(ViewDataPopup, self).__init__(**kwargs)
        self.title = "View Data"
        self.size_hint = (0.6, 0.4)

        layout = BoxLayout(orientation='vertical', padding=10)

        label = Label(text='Click the link below to view data:')
        layout.add_widget(label)

        link_button = Button(text='Go to Web Application')
        link_button.bind(on_press=lambda instance: self.open_link())
        layout.add_widget(link_button)

        self.content = layout

    def open_link(self):
        import webbrowser
        webbrowser.open('http://yourwebapp.com')  


from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
import json

class ButtonDisplay(BoxLayout):
    def __init__(self, button_texts, button_callbacks, backend_callback, **kwargs):
        super(ButtonDisplay, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.backend_callback = backend_callback

        for text, callback in zip(button_texts, button_callbacks):
            button = Button(text=text)
            button.bind(on_press=lambda instance, cmd=text: self.send_command(cmd))
            self.add_widget(button)

    def send_command(self, command):
        self.backend_callback()  # Remove the argument here

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

        # Add a button to select the directory and close the popup
        select_button = Button(text="Select")
        select_button.bind(on_press=self.select_and_close)
        layout.add_widget(select_button)

        self.content = layout

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
        layout = BoxLayout(orientation='vertical', padding=10)

        # Create a dropdown menu for query results
        dropdown = DropDown()

        for result in query_result:
            btn = Button(text=result, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)

        # Create a button to trigger the dropdown
        dropdown_button = Button(text='Query Results', size_hint=(None, None))
        dropdown_button.bind(on_release=dropdown.open)
        layout.add_widget(dropdown_button)

        dropdown.bind(on_select=lambda instance, x: setattr(dropdown_button, 'text', x))

        self.content = layout

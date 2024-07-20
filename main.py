import queue
import random
import threading
import speech_recognition as sr
from kivy.app import App
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window

Window.clearcolor = (0, 0, 0, 1)

KV = """
BoxLayout:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: (0, 0, 0, 1)  # Black background
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "Transcribed Text"
        color: (1, 1, 1, 1)
        size_hint_y: None
        height: self.texture_size[1]

    TextInput:
        id: transcribed_text
        size_hint_y: None
        height: dp(390)
        readonly: True
        background_color: (0.2, 0.2, 0.2, 1)
        foreground_color: (1, 1, 1, 1)
        text: ''

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(10)

        Button:
            text: "Start"
            background_normal: ''
            background_color: (0.5, 0.2, 0.2, 1)
            on_press: app.start_live_transcription()

        Button:
            text: "Stop"
            background_normal: ''
            background_color: (0.5, 0.2, 0.2, 1)
            on_press: app.stop_transcription()

    BoxLayout:
        size_hint_y: None
        height: dp(30)
        spacing: dp(10)

        Label:
            text: "Enter Filename:"
            color: (1, 1, 1, 1)
            size_hint_x: 0.5
            font_size: '15sp'
            bold: True

        TextInput:
            id: filename_input
            size_hint_x: 0.5
            multiline: False
            background_color: (0.2, 0.2, 0.2, 1)
            foreground_color: (1, 1, 1, 1)

    Button:
        text: "Download"
        size_hint_x: 0.5
        size_hint_y: None
        pos_hint: {'center_x': 0.5}
        height: dp(50)
        background_normal: ''
        background_color: (0.5, 0.2, 0.2, 1)
        on_press: app.download_transcription()
"""

class MainApp(App):
    def build(self):
        return Builder.load_string(KV)

    def start_live_transcription(self):
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)

        print("Starting transcription...")
        self.listening_thread = threading.Thread(target=self.audio_listener)
        self.listening_thread.start()

        self.transcribing_thread = threading.Thread(target=self.audio_transcriber)
        self.transcribing_thread.start()

    def stop_transcription(self):
        print("Stopping transcription...")
        if hasattr(self, 'stop_event'):
            self.stop_event.set()
        if hasattr(self, 'listening_thread'):
            self.listening_thread.join(timeout=1)
        if hasattr(self, 'audio_queue'):
            self.audio_queue.put(None)  # Signal the transcriber thread to stop
        if hasattr(self, 'transcribing_thread'):
            self.transcribing_thread.join(timeout=1)

    def audio_listener(self):
        print("Listener thread started.")
        while not self.stop_event.is_set():
            with self.microphone as source:
                try:
                    print("Listening...")
                    audio = self.recognizer.listen(source, phrase_time_limit=10)
                    print("Audio captured.")
                    self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    print("Timeout occurred, continuing...")
                    continue
                except Exception as e:
                    print(f"Error in audio listener: {e}")
                    break
        print("Listener thread stopped.")

    def audio_transcriber(self):
        print("Transcriber thread started.")
        while True:
            audio = self.audio_queue.get()
            if audio is None:
                print("Stopping transcriber...")
                break
            print("Transcribing audio...")
            self.recognize_speech(audio)
            self.audio_queue.task_done()
            print("Transcription complete.")
            self.audio_queue.join()  # Ensure all tasks are done

    @mainthread
    def update_transcribed_text(self, text):
        # print(f"Updating text: {text}")
        self.root.ids.transcribed_text.text += text + " "

    def recognize_speech(self, audio):
        try:
            print("Recognizing speech...")
            text = self.recognizer.recognize_google(audio)
            # print(f"Recognized text: {text}")
            self.update_transcribed_text(text)
        except sr.UnknownValueError:
            print("Could not understand the audio")
            self.update_transcribed_text("Could not understand the audio")
        except sr.RequestError as e:
            print(f"API request error: {e}")
            self.update_transcribed_text(f"API request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            self.update_transcribed_text(f"Unexpected error: {e}")

    def download_transcription(self):
        count=random.randint(0,10001)
        if self.root.ids.filename_input.text == '':
            filename = f"output{count}.txt"
        else:
            filename = f"{self.root.ids.filename_input.text}.txt"
        if filename:
            with open(filename, 'w') as f:
                f.write(self.root.ids.transcribed_text.text)

if __name__ == '__main__':
    MainApp().run()

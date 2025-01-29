import keyboard
from dotenv import load_dotenv
import speech_recognition as sr
import os
import subprocess
import asyncio
import re
import sys
import json
from edge_tts import Communicate
from plyer import notification

# File to store conversation history
HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 1000  # Maximum stored messages to prevent overflow

# Suppresses command line pop-ups when executing subprocesses (Windows-specific)
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = 0

# Commands to terminate the assistant
exit_commands = ["bye", "go away", "quit", "shut up"]

def play_sound():
    """
    Plays a confirmation sound when a recording starts/stops.
    Change 'confirmation.mp3' to any other sound file if needed.
    """
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", "confirmation.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo  
    )

# Initialize speech recognition
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Flags to manage recording state
recording = False  
audio_data = None  

def load_conversation_history():
    """
    Loads conversation history from a JSON file. 
    If the file does not exist or is corrupted, a new history file is created.
    """
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "user" in data and "assistant" in data:
                    print("Conversation history loaded.")
                    return data
        except (json.JSONDecodeError, TypeError):
            print("Error loading conversation history, creating new history file.")
    default_history = {"user": [], "assistant": []}
    save_conversation_history(default_history)
    return default_history

def save_conversation_history(history):
    """
    Saves the updated conversation history back to the JSON file.
    """
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)
    print("Conversation history saved.")

def update_conversation_history(user_input, assistant_response):
    """
    Updates the conversation history with the latest user input and assistant response.
    Older messages are removed if the history exceeds MAX_HISTORY.
    """
    history = load_conversation_history()
    history["user"].append(user_input)
    history["assistant"].append(assistant_response)
    history["user"] = history["user"][-MAX_HISTORY:]
    history["assistant"] = history["assistant"][-MAX_HISTORY:]
    save_conversation_history(history)
    print(f"Updated conversation history:\nUser: {user_input}\nAssistant: {assistant_response}")

def get_conversation_context():
    """
    Generates a formatted conversation history to maintain continuity.
    The assistant has a sassy personality but switches to professional mode for serious topics.
    """
    history = load_conversation_history()
    print("Generating conversation context...")
    context = ("Your task is to to be a helpful and personal voice assistant. You have very good memory and can recall previous conversations, keep your answers short and conice and try to be a little humorous, avoid including special characters or emojis in your responses.")

    for user_msg, assistant_msg in zip(history["user"], history["assistant"]):
        context += f"User: {user_msg}\nAI: {assistant_msg}\n"

    return context

def send_notification(title, message):
    """
    Sends a desktop notification with a truncated message (max 256 characters).
    """
    truncated_message = message[:256]
    notification.notify(title=title, message=truncated_message, app_name="Voice Assistant", timeout=2)
    print(f"Notification sent")

def remove_emojis_and_symbols(text):
    """
    Removes non-alphanumeric characters except for punctuation.
    """
    cleaned_text = re.sub(r'[^\w\s,.!?]', '', text)
    print(f"Cleaned text: {cleaned_text}")
    return cleaned_text

async def generate_speech(text):
    """
    Converts text to speech using edge_tts and plays the response.
    Users can change the voice by modifying `voice="en-US-RogerNeural"`.
    """
    clean_text = remove_emojis_and_symbols(text)
    try:
        print("Generating speech...")
        communicate = Communicate(clean_text, voice="en-US-RogerNeural", rate="+30%")
        output_file = "temp_response.mp3"
        await communicate.save(output_file)
        send_notification("AI", clean_text)

        if os.path.exists(output_file):
            subprocess.run(["ffplay", "-nodisp", "-autoexit", output_file], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
            os.remove(output_file)
        print("Speech generation complete.")
    except Exception as e:
        send_notification("Error", f"⚠️ {e}")
        print(f"Error in speech generation: {e}")

def ask_ollama(query):
    """
    Sends a user query to the Llama 3.1 model and retrieves a response.
    Users can modify the model parameters or prompt style here.
    """
    conversation_context = get_conversation_context()
    prompt = f"{conversation_context}\nUser: {query}\nAI:"

    try:
        print("Sending query to Ollama...")
        process = subprocess.Popen(
            ["ollama", "run", "llama3.1"], # Change llama3.1 to the model of your choice by replacing it with the proper model name
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", startupinfo=startupinfo
        )
        response, _ = process.communicate(input=prompt)
        response_text = response.strip() if response else "Sorry, I didn't get that."

        print(f"Llama response: {response_text}")
        update_conversation_history(query, response_text)
        return response_text

    except Exception as e:
        send_notification("Error", f"Communication error: {e}")
        print(f"Error communicating with Ollama: {e}")
        return "Sorry, there was an issue communicating with Ollama."

def toggle_recording():
    """
    Toggles voice recording on/off when the Alt key is pressed.
    Users can change the hotkey in `keyboard.add_hotkey()`.
    """
    global recording, audio_data

    if not recording:
        recording = True
        print("Recording started...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            play_sound()
            send_notification("Listening", "Speak Up!")
            audio_data = recognizer.listen(source, timeout=None)
    else:
        recording = False
        print("Recording stopped.")
        play_sound()
        send_notification("Please Wait", "Generating response...")
        try:
            text = recognizer.recognize_google(audio_data).strip().lower()
            print(f"Recognized text: {text}")

            if text in exit_commands:
                send_notification("Voice Assitant", "Goodbye!")
                print("Exit command received. Shutting down.")
                sys.exit(0)  

            if text:
                response = ask_ollama(text)
                asyncio.run(generate_speech(response))
        except sr.UnknownValueError:
            send_notification("Error", "Could not understand audio.")
        except sr.RequestError as e:
            send_notification("Error", f"Speech recognition error: {e}")

def main():
    """
    Initializes the assistant and listens for keyboard shortcuts.
    """
    print("Assistant initialized. Press Alt to start and stop recording.")
    send_notification("Voice Asistant", "Press Alt to start and stop recording.")
    keyboard.add_hotkey('alt', toggle_recording) #you can change hotkey here
    keyboard.wait('esc')
    play_sound()
    send_notification("Voice Assistant", "Shutting down...")
    print("Assistant shutting down.")

if __name__ == "__main__":
    main()

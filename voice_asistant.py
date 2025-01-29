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

load_dotenv()

HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 1000  

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = 0

exit_commands = ["bye", "go away", "quit", "shut up"]

def play_sound():
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", "confirmation.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo  
    )

recognizer = sr.Recognizer()
mic = sr.Microphone()

recording = False  
audio_data = None  

def load_conversation_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "user" in data and "assistant" in data:
                    print("Conversation history loaded.")
                    return data
        except (json.JSONDecodeError, TypeError):
            print("Error loading conversation history, creating new history file.")
            pass
    default_history = {"user": [], "assistant": []}
    save_conversation_history(default_history)
    return default_history

def save_conversation_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)
    print("Conversation history saved.")

def update_conversation_history(user_input, assistant_response):
    history = load_conversation_history()
    history["user"].append(user_input)
    history["assistant"].append(assistant_response)
    history["user"] = history["user"][-MAX_HISTORY:]
    history["assistant"] = history["assistant"][-MAX_HISTORY:]
    save_conversation_history(history)
    print(f"Updated conversation history:\nUser: {user_input}\nAssistant: {assistant_response}")

def get_conversation_context():
    history = load_conversation_history()
    print("Generating conversation context...")
    context = ("Your task is to act as a sassy voice assistant, but don't mention that you are sassy, just act like it. "
               "Use a slight hint of slang words while maintaining professionalism. Try to understand the user before "
               "asking for clarification. Your creator is Hamza, and he is your user, and you are his very reliable "
               "and personal sidekick. Please refrain from using emojis and weird symbols, as this is a voice-based "
               "conversation. You should be a little mean and tease the user, but when asked about serious topics "
               "like math or general knowledge, switch to a professional tone.\n\nHere is the conversation history:\n")

    for user_msg, assistant_msg in zip(history["user"], history["assistant"]):
        context += f"User: {user_msg}\nHamza's Sidekick: {assistant_msg}\n"

    return context

def send_notification(title, message):
    truncated_message = message[:256]
    notification.notify(title=title, message=truncated_message, app_name="Voice Assistant", timeout=2)
    print(f"Notification sent")

def remove_emojis_and_symbols(text):
    cleaned_text = re.sub(r'[^\w\s,.!?]', '', text)
    print(f"Cleaned text: {cleaned_text}")
    return cleaned_text

async def generate_speech(text):
    clean_text = remove_emojis_and_symbols(text)
    try:
        print("Generating speech...")
        communicate = Communicate(clean_text, voice="en-US-RogerNeural", rate="+30%")
        output_file = "temp_response.mp3"
        await communicate.save(output_file)
        send_notification("Hamza's Sidekick", clean_text)

        if os.path.exists(output_file):
            subprocess.run(["ffplay", "-nodisp", "-autoexit", output_file], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
            os.remove(output_file)
        print("Speech generation complete.")
    except Exception as e:
        send_notification("Error", f"⚠️ {e}")
        print(f"Error in speech generation: {e}")

def ask_ollama(query):
    conversation_context = get_conversation_context()
    prompt = f"{conversation_context}\nUser: {query}\nHamza's Sidekick:"

    try:
        print("Sending query to Ollama...")
        process = subprocess.Popen(
            ["ollama", "run", "llama3.1"],
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
                send_notification("Hamza's Sidekick", "Goodbye!")
                print("Exit command received. Shutting down.")
                sys.exit(0)  

            if text:
                response = ask_ollama(text)
                asyncio.run(generate_speech(response))
        except sr.UnknownValueError:
            send_notification("Error", "Could not understand audio.")
            print("Speech recognition error: Could not understand audio.")
        except sr.RequestError as e:
            send_notification("Error", "Could not request results from speech recognition service.")
            print(f"Speech recognition request error: {e}")

def main():
    print("Assistant initialized. Press Alt to start and stop recording.")
    send_notification("Hamza's Sidekick", "Press Alt to start and stop recording.")
    keyboard.add_hotkey('alt', toggle_recording)
    keyboard.wait('esc')
    play_sound()
    send_notification("Hamza's Sidekick", "Shutting down...")
    print("Assistant shutting down.")

if __name__ == "__main__":
    main()

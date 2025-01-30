import keyboard
from dotenv import load_dotenv
import speech_recognition as sr
import os
import subprocess
import asyncio
import re
import sys
import json
import threading
from edge_tts import Communicate
from plyer import notification
from llm_axe.agents import OnlineAgent
from llm_axe import OllamaChat
import ollama

load_dotenv()

HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 1000  

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = 0

exit_commands = ["bye", "go away", "quit", "shut up"]
speaking = False  
recording = False  
audio_data = None  

def play_sound():
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", "confirmation.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo  
    )

recognizer = sr.Recognizer()
mic = sr.Microphone()

def load_conversation_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "user" in data and "assistant" in data and "context" in data:
                    print("Conversation history loaded.")
                    return data
        except (json.JSONDecodeError, TypeError):
            print("Error loading conversation history, creating new history file.")
            pass
    default_history = {
        "context": "Your task is to be a helpful voice assistant, keep your answers short and concice.",
        "user": [],
        "assistant": []
    }
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
    history["user"] = history["user"][-1000:]
    history["assistant"] = history["assistant"][-1000:]
    save_conversation_history(history)
    print(f"Updated conversation history:\nUser: {user_input}\nAssistant: {assistant_response}")

def get_conversation_context():
    history = load_conversation_history()
    print("Generating conversation context...")
    context = history["context"]
    for user_msg, assistant_msg in zip(history["user"], history["assistant"]):
        context += f"User: {user_msg}\nVoice Assistant: {assistant_msg}\n"
    return context

def send_notification(title, message):
    truncated_message = message[:256]
    notification.notify(title=title, message=truncated_message, app_name="Voice Assistant", timeout=1)
    print(f"Notification sent: {title}")

def remove_emojis_and_symbols(text):
    cleaned_text = re.sub(r'[^\w\s,.!?]', '', text)
    print(f"Cleaned text: {cleaned_text}")
    return cleaned_text

async def generate_speech(text):
    global speaking
    clean_text = remove_emojis_and_symbols(text)
    try:
        print("Generating speech...")
        speaking = True
        communicate = Communicate(clean_text, voice="en-US-RogerNeural", rate="+15%")
        output_file = "temp_response.mp3"
        await communicate.save(output_file)
        send_notification("Voice Assistant", clean_text)

        if os.path.exists(output_file):
            def play_audio():
                global speaking
                process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", output_file],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                process.wait()
                os.remove(output_file)
                speaking = False

            audio_thread = threading.Thread(target=play_audio, daemon=True)
            audio_thread.start()

        print("Speech generation complete.")
    except Exception as e:
        speaking = False
        send_notification("Error", f"⚠️ {e}")
        print(f"Error in speech generation: {e}")

def ask_ollama(query):
    try:
        print("Fetching response...")
        conversation_context = get_conversation_context()
        full_prompt = f"{conversation_context}\nUser: {query}\nVoice Assistant:"
        
        if "online" in query.lower():
            print("Switching to internet search mode...")
            llm = OllamaChat(model="llama3.1")
            agent = OnlineAgent(llm)
            search_response = agent.search(query)
            print("Raw search response:", search_response)
            response_text = search_response.strip() if isinstance(search_response, str) else "I couldn't find real-time information."
        else:
            print("Using local Ollama model...")
            response = ollama.chat(model="llama3.1", messages=[
                {"role": "system", "content": conversation_context},
                {"role": "user", "content": full_prompt}
            ])
            response_text = response["message"]["content"].strip() if response.get("message", {}).get("content") else "Sorry, I couldn't generate a response."

        print(f"Llama response: {response_text}")
        update_conversation_history(query, response_text)
        return response_text
    except Exception as e:
        send_notification("Error", f"Assistant error: {e}")
        print(f"Error in assistant response: {e}")
        return "Sorry, there was an issue processing your request."

def stop_speech():
    global speaking
    print("Stopping speech...")
    speaking = False
    subprocess.run(["taskkill", "/IM", "ffplay.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def toggle_recording():
    global recording, audio_data, speaking
    if speaking:
        stop_speech()
        return  

    if not recording:
        recording = True
        print("Recording started...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            play_sound()
            audio_data = recognizer.listen(source, timeout=None)
    else:
        recording = False
        print("Recording stopped.")
        play_sound()
        try:
            text = recognizer.recognize_google(audio_data).strip().lower()
            print(f"Recognized text: {text}")

            if text in exit_commands:
                send_notification("Voice Assistant", "Goodbye!")
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

if __name__ == "__main__":
    print("Assistant initialized. Press Alt to start and stop recording.")
    send_notification("Voice Assistant", "Press Alt to start and stop recording.")
    keyboard.add_hotkey('alt', toggle_recording)
    keyboard.wait('esc')

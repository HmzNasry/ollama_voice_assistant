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
from langdetect import detect
from datetime import datetime
import keyboard

HISTORY_FILE = "conversation_history.json"

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

def play_close_sound():
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", "close.wav"],
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

    default_history = {
        "context": "Be a sassy and smart voice assistant, use casual words, don't be too formal. Your user's name is Hamza. The user has built a memory system that allows you to refer to previous conversations and timestamps, so you can figure out what time it is and how long it has been since previous conversations. Do not put the timestamp in your response. Keep answers really short, concise, and human-like.",
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
    dt = datetime.now()
    history = load_conversation_history()
    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")  

    history["user"].append(f"{timestamp}: {user_input}")  
    history["assistant"].append(f"{timestamp}: {assistant_response}")  

    save_conversation_history(history)
    print(f"Updated conversation history:\nUser: {user_input}\nAssistant: {assistant_response}")

def get_conversation_context():
    history = load_conversation_history()
    context = history["context"]
    conversation_history = []

    for user_msg, assistant_msg in zip(history["user"], history["assistant"]):
        conversation_history.append(f"User: {user_msg}\nVoice Assistant: {assistant_msg}\n")

    return context + ''.join(conversation_history)

def send_notification(title, message):
    truncated_message = message[:256]
    notification.notify(title=title, message=truncated_message, app_name="Voice Assistant", timeout=1)
    print(f"Notification sent: {title}")

send_notification("Voice Assistant", "Voice assistant has loaded and is ready, press alt to start/stop recording")

def remove_emojis_and_symbols(text):
    cleaned_text = re.sub(r'[^\w\s,.!?]', '', text)
    print(f"Cleaned text: {cleaned_text}")
    return cleaned_text

async def generate_speech(text, lang="en"):
    global speaking
    clean_text = remove_emojis_and_symbols(text)
    try:
        print(f"Generating speech in {lang}...")

        speaking = True
        voice = "en-US-EmmaNeural" if lang == "en" else "es-ES-ElviraNeural" #Custommize Voices here

        communicate = Communicate(clean_text, voice=voice)
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
        
        if "online" in query.lower(): #Customize online triggerword here
            print("Switching to internet search mode...")
            llm = OllamaChat(model="llama3.1") #change model here
            agent = OnlineAgent(llm)
            e = query.replace('online', '')
            search_response = agent.search(e)
            print("Raw search response:", search_response)
            response_text = search_response.strip() if isinstance(search_response, str) else "I couldn't find real-time information."
        else:
            print("Using local Ollama model...")
            response = ollama.chat(model="llama3.1", messages=[ #Change model here
                {"role": "system", "content": conversation_context},
                {"role": "user", "content": full_prompt}
            ])
            response_text = response["message"]["content"].strip() if response.get("message", {}).get("content") else "Sorry, I couldn't generate a response."

        print(f"llama: {response_text}")
        
        detected_lang = detect(response_text)  
        print(f"Detected language of assistant response: {detected_lang}")

        lang_code = "en" if detected_lang == "en" else "es"

        update_conversation_history(query, response_text)
        asyncio.run(generate_speech(response_text, lang=lang_code)) 
        
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
                play_close_sound()
                sys.exit(0)

            if text:
                ask_ollama(text)

        except Exception as e:
            print(f"Speech recognition error: {e}")
            send_notification("Error", "Could not understand audio")

if __name__ == "__main__":
    keyboard.add_hotkey('alt', toggle_recording) #Customize hotkeys here
    keyboard.wait('esc') #Customize exit key here

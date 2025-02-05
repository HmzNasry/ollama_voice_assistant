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
conversation_context = "keep answers short, clear and concise. Do not ask the user questions or offer assistance at the end of your response, just respond to what you were asked. Do not use markdown or symbols in your response, you are communicating through voice, keep answers really short."

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
    print("Playing close sound...")
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", "close.wav"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo  
    )

recognizer = sr.Recognizer()
mic = sr.Microphone()

def load_conversation_history():
    print("Loading conversation history...")
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "user" in data and "assistant" in data:
                    return data
        except (json.JSONDecodeError, TypeError):
            pass

    default_history = {"user": [], "assistant": []}
    save_conversation_history(default_history)
    return default_history

def save_conversation_history(history):
    print("Saving conversation history...")
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

def update_conversation_history(user_input, assistant_response):
    print(f"Updating conversation history: User said '{user_input}', Assistant responded '{assistant_response}'")
    dt = datetime.now()
    history = load_conversation_history()
    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")  

    history["user"].append(f"{timestamp}: 'User': {user_input}")  
    history["assistant"].append(f"{timestamp}: 'Assistant': {assistant_response}") 

    save_conversation_history(history)

def send_notification(title, message):
    print(f"Sending notification: {title} - {message[:50]}...")
    truncated_message = message[:256]
    notification.notify(title=title, message=truncated_message, app_name="Voice Assistant", timeout=1)

send_notification("Voice Assistant", "Voice assistant has loaded and is ready, press alt to start/stop recording")

def remove_emojis_and_symbols(text):
    return re.sub(r'[^\w\s,.!?]', '', text)

async def generate_speech(text, lang="en"):
    global speaking
    clean_text = remove_emojis_and_symbols(text)
    try:
        speaking = True
        voice = "en-US-EmmaNeural" if lang == "en" else "es-ES-ElviraNeural" 
        print(f"Generating speech for: {clean_text}")

        communicate = Communicate(clean_text, voice=voice, rate="+15%")
        output_file = "temp_response.mp3"
        await communicate.save(output_file)
        send_notification("Voice Assistant", clean_text)

        if os.path.exists(output_file):
            def play_audio():
                global speaking
                print("Playing generated speech audio...")
                process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", output_file],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                process.wait()
                os.remove(output_file)
                speaking = False

            threading.Thread(target=play_audio, daemon=True).start()
    except Exception as e:
        speaking = False
        print(f"Error in speech generation: {e}")
        send_notification("Error", f"⚠️ {e}")

def ask_ollama(query):
    try:
        history = load_conversation_history()
        messages = [{"role": "system", "content": conversation_context}]
        
        for u, a in zip(history["user"][-5:], history["assistant"][-5:]):
            messages.append({"role": "user", "content": u})
            messages.append({"role": "assistant", "content": a})
        
        messages.append({"role": "user", "content": query})

        if "online" in query.lower(): 
            llm = OllamaChat(model="llama3.1") 
            agent = OnlineAgent(llm)
            search_response = agent.search(query.replace('online', '').strip())
            response_text = search_response.strip() if isinstance(search_response, str) else "I couldn't find real-time information."
        else:
            response = ollama.chat(model="llama3.1", messages=messages, options={"num_ctx": 32000})  
            response_text = response["message"]["content"].strip() if response.get("message", {}).get("content") else "Sorry, I couldn't generate a response."

        detected_lang = detect(response_text)  
        lang_code = "en" if detected_lang == "en" else "es"

        update_conversation_history(query, response_text)
        asyncio.run(generate_speech(response_text, lang=lang_code)) 
        
        return response_text
    except Exception as e:
        print(f"Error in Ollama processing: {e}")
        send_notification("Error", f"Assistant error: {e}")
        return "Sorry, there was an issue processing your request."

def stop_speech():
    global speaking
    print("Stopping speech playback...")
    speaking = False
    subprocess.run(["taskkill", "/IM", "ffplay.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def toggle_recording():
    global recording, audio_data, speaking
    if speaking:
        stop_speech()
        return  

    if not recording:
        recording = True
        print("Starting recording...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            play_sound()
            audio_data = recognizer.listen(source, timeout=None)
    else:
        recording = False
        print("Stopping recording...")
        play_sound()
        try:
            text = recognizer.recognize_google(audio_data).strip().lower()
            print(f"Recognized speech: {text}")
            
            if text in exit_commands:
                print("Exit command detected, shutting down...")
                send_notification("Voice Assistant", "Goodbye!")
                play_close_sound()
                sys.exit(0)

            if text:
                ask_ollama(text)
        except Exception:
            print("Could not understand audio")
            send_notification("Error", "Could not understand audio")

if __name__ == "__main__":
    print("Voice assistant is running. Press 'Alt' to start/stop recording, 'Esc' to exit.")
    keyboard.add_hotkey('alt', toggle_recording) 
    keyboard.wait('esc')

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

dt = datetime.now()
HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 1000  # Limit stored history entries
MAX_TOKENS = 2048  # Hard limit for conversation context

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = 0

exit_commands = ["bye", "exit", "quit", "shut down"]
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
        "context": "You are a witty, engaging, and highly intelligent voice assistant. Your personality is a blend of professionalism and charm, capable of handling technical inquiries with expertise while maintaining an engaging and friendly tone. You prioritize user assistance, provide thoughtful responses, and adapt to context while ensuring clarity and accuracy.",
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
    history["user"].append(f"{dt}: {user_input}")
    history["assistant"].append(f"{dt}: {assistant_response}")
    history["user"] = history["user"][-MAX_HISTORY:]
    history["assistant"] = history["assistant"][-MAX_HISTORY:]
    save_conversation_history(history)
    print(f"Updated conversation history:\nUser: {user_input}\nAssistant: {assistant_response}")

def count_tokens(text):
    return len(text.split())

def get_conversation_context():
    history = load_conversation_history()
    print("Generating conversation context...")
    context = history["context"]
    conversation_history = []
    
    for user_msg, assistant_msg in zip(history["user"], history["assistant"]):
        conversation_history.append(f"User: {user_msg}\nAssistant: {assistant_msg}\n")
    
    full_conversation = context + ''.join(conversation_history)
    token_count = count_tokens(full_conversation)
    
    while token_count > MAX_TOKENS and len(conversation_history) > 0:
        removed_turn = conversation_history.pop(0)
        token_count -= count_tokens(removed_turn)
        full_conversation = context + ''.join(conversation_history)
    
    return full_conversation

def send_notification(title, message):
    truncated_message = message[:256]
    notification.notify(title=title, message=truncated_message, app_name="Voice Assistant", timeout=1)
    print(f"Notification sent: {title}")

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
        voice = "en-US-EmmaNeural" if lang == "en" else "es-ES-ElviraNeural"
        
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
        response = ollama.chat(model="llama3.1", messages=[
            {"role": "system", "content": conversation_context},
            {"role": "user", "content": query}
        ])
        response_text = response["message"]["content"].strip()
        update_conversation_history(query, response_text)
        asyncio.run(generate_speech(response_text))
        return response_text
    except Exception as e:
        send_notification("Error", f"Assistant error: {e}")
        print(f"Error in assistant response: {e}")
        return "Sorry, there was an issue processing your request."

if __name__ == "__main__":
    print("Assistant initialized. Press Alt to start and stop recording.")
    send_notification("Voice Assistant", "Press Alt to start and stop recording.")
    keyboard.add_hotkey('alt', toggle_recording)
    keyboard.wait('esc')

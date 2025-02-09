import os
import json
import requests
import subprocess
import asyncio
import threading
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper
import keyboard
from datetime import datetime
from langdetect import detect
from plyer import notification
import ollama
from llm_axe import OllamaChat, Agent, OnlineAgent
import edge_tts
import warnings

warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")
warnings.filterwarnings("ignore", message="Performing inference on CPU when CUDA is available")
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# --- Global Settings and Variables ---
HISTORY_FILE = "conversation_history.json"
exit_commands = ["bye", "quit", "exit"]
recording = False
audio_frames = []
whisper_model = whisper.load_model("medium", device="cpu")

# For sound effects (requires ffplay from FFmpeg in your PATH)
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = 0

def play_sound(sound_file):
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", sound_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo
    )

def send_notification(title, message):
    truncated = message[:256]
    notification.notify(title=title, message=truncated, app_name="Voice Assistant", timeout=1)

# --- Location and Conversation Context ---
def get_location():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        data = response.json()
        city = data.get("city", "Unknown")
        country = data.get("country", "Unknown")
        return city, country
    except Exception as e:
        print(f"[get_location] Error: {e}")
        return "Unknown", "Unknown"

city, country = get_location()
dt_now = datetime.now()
date_str = dt_now.strftime("%Y-%m-%d %H:%M:%S")
conversation_context = (
    f"Keep your answers appropriately short and concise. Do not mention being an AI. "
    f"Do not use markdown, symbols, abbreviations, or acronyms that might not be caught well through text. "
    f"The user's location is {city}, {country}, and the current time is {date_str} PST."
)
print(f"[INIT] Detected Location: {city}, {country}")

# --- Conversation History Functions ---
def reset_conversation_history():
    default_data = {"user": [], "assistant": []}
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(default_data, f, indent=4)
    return default_data

def load_conversation_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON format in history file.")
                for key in ["user", "assistant"]:
                    if key not in data:
                        data[key] = []
                return data
        except (json.JSONDecodeError, ValueError):
            print("[load_conversation_history] Corrupted file. Resetting history.")
            return reset_conversation_history()
        except Exception as e:
            print(f"[load_conversation_history] Error: {e}")
            return reset_conversation_history()
    return reset_conversation_history()

def save_conversation_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"[save_conversation_history] Error: {e}")

def update_conversation_history(user_input, assistant_response):
    history = load_conversation_history()
    history["user"].append(user_input)
    history["assistant"].append(assistant_response)
    if len(history["user"]) > 50:
        history["user"].pop(0)
        history["assistant"].pop(0)
    save_conversation_history(history)

# --- Ask Ollama Function (with Internet Search Logic) ---
def ask_ollama(query):
    try:
        print(f"\n[ask_ollama] Processing query: {query}")
        history = load_conversation_history()
        system_prompt = conversation_context
        llm = OllamaChat(model="qwen2.5:7b")

        plan_agent = Agent(
            llm,
            custom_system_prompt=f"""
            You are part of a system where the user interacts with you, first the query goes to you BUT YOUR OWNLY JOB IS to decide if it needs internet search or not, and you must only respond with JSON including internet, which can be yes or no and search_query, which must contain a very optimized saerch query to fetch info from the internet for the user's query. After you say yes, the internet will be searched and relevant information will be extracted and feed it to the next AI model, SO YOU CANNOT PUT ANYTHING IN YOUR RESPONSE OTHER THAN THE JSON to Your response MUST be a valid JSON object.

            TASKS:
            1. Determine if an internet search is required to answer the user's question PAY VERY CLOSE ATTENTION IF INTERNET IS REQUIRED OR NOT, THINGS LIKE WEATHER AND ASKING FOR LATEST STUFF OR NEWS WILL REQUIRE THE INTERNET, FOR EXAMPLE IF THEY SAY WHAT DO I WEAR TODAY THAT NEEDS INETNET SEARCH TO SEE THE FORCAST. Sometimes the user might ask follow-up questions, then you need to include information from past interactions too MAKE SURE TO SAY YES WHEN MOST UP TO DATE INFO IS NEEDED LIKE THE WEATHER AND MORE!!! THE USER IS GONNA ASK FOLLOW UP QUESTIONS LIKE FOR EXAMPLE THE SPECS OF SOMETHING THEY ASKED FOR EARLIER, YOU MUST SEARCH THE INTERNET AND INCLUDE INFO FROM THE LAST INTERACTION.
               - If yes, set "internet": "yes".
               - If no, set "internet": "no".

            2. If "internet" is "yes", generate a precise search query and name it search_query.
               - Consider user location ONLY IF ABSOLUTELY NECESSARY: {city}, {country}.
               - Consider the current DATE and include time if relevant: {date_str} PST.
               - Keep it short, relevant, and avoid unnecessary words.

            Your response MUST only contain these two JSON fields: "internet" (yes/no) and "search_query" (empty if no search needed).
            """
        )
        plan_response = plan_agent.ask(f"USER'S INPUT: {query}, PAST INTERACIONS (USE TO ANSWR FOLLOW UP QUESTIONS): {history}")
        print(f"[Plan Agent] Response: {repr(plan_response)}")
        try:
            plan_data = json.loads(plan_response.strip())
        except json.JSONDecodeError:
            print("[Plan Agent] JSON Parsing Error, defaulting to local response.")
            plan_data = {"internet": "no", "search_query": ""}

        method = None
        summary = None
        url = None

        if plan_data.get("internet") == "yes" and plan_data.get("search_query"):
            print(f"[ask_ollama] Fetching real-time data for: {plan_data['search_query']}")
            search_url = f"http://localhost:8080/search?q={plan_data['search_query']}&format=json"
            try:
                search_response = requests.get(search_url)
                print(f"[DEBUG] Search API Response Code: {search_response.status_code}")
                if search_response.status_code == 200:
                    raw_text = search_response.text.strip()
                    print(f"[DEBUG] Raw response text: {raw_text}")
                    if raw_text in ['"query"', 'query']:
                        print("[ask_ollama] Warning: Search API returned a query string; setting search_results to {}.")
                        search_results = {}
                    else:
                        try:
                            search_results = json.loads(raw_text)
                            if isinstance(search_results, str):
                                print(f"[ask_ollama] Warning: Search results returned as string: {search_results}")
                                search_results = {}
                        except Exception as e:
                            print(f"[ask_ollama] JSON Parsing Error in search response: {raw_text}")
                            search_results = {}
                    print(f"[DEBUG] Raw Search Results:\n{json.dumps(search_results, indent=2, ensure_ascii=False)}")

                    if "answers" in search_results and search_results["answers"]:
                        summary = search_results["answers"][0]
                        method = "answers"
                        print(f"[ask_ollama] Answer Found: {summary}")
                    elif ("results" in search_results and 
                          isinstance(search_results["results"], list) and 
                          len(search_results["results"]) >= 3):
                        third_result = search_results["results"][0]
                        if isinstance(third_result, dict) and "url" in third_result:
                            url = third_result["url"]
                            method = "onlineagent"
                            print(f"[ask_ollama] Using 1st URL from results: {url}")
                        else:
                            print("[ask_ollama] Third search result does not contain a valid URL.")
                    else:
                        print("[ask_ollama] Neither answers nor sufficient results found in search results.")
            except Exception as e:
                print(f"[ask_ollama] Error fetching search results: {e}")

        if method == "answers":
            system_prompt += f" Additional relevant internet data, use whatever you can from this, also do not say 'the text', or 'the website' or mention the souorce because the user doesn't know what you are talking about: {summary}"
            messages = [{"role": "system", "content": system_prompt}]
            for u, a in zip(history["user"][-15:], history["assistant"][-15:]):
                messages.append({"role": "user", "content": u})
                messages.append({"role": "assistant", "content": a})
            messages.append({"role": "user", "content": query})
            response = ollama.chat(model="qwen2.5:7b", messages=messages)
            response_text = response["message"]["content"].strip()
            update_conversation_history(query, response_text)
            return response_text

        elif method == "onlineagent":
            searcher = OnlineAgent(llm)
            online_answer = searcher.search(
                f"{conversation_context}, extract the info from this website: {url} to answer the user's question, {query} also do not say 'the text', or 'the website' or mention the souorce because the user doesn't know what you are talking about, considering the past interactions, {history}")
            update_conversation_history(query, online_answer)
            cleaned_answer = online_answer.replace('According to the information from the internet,', '')
            return cleaned_answer

        else:
            print("[ask_ollama] No valid internet data found. Proceeding with local knowledge.")
            messages = [{"role": "system", "content": system_prompt}]
            for u, a in zip(history["user"][-15:], history["assistant"][-15:]):
                messages.append({"role": "user", "content": u})
                messages.append({"role": "assistant", "content": a})
            messages.append({"role": "user", "content": query})
            response = ollama.chat(model="qwen2.5:7b", messages=messages)
            response_text = response["message"]["content"].strip()
            update_conversation_history(query, response_text)
            return response_text

    except Exception as e:
        print(f"[ask_ollama] Error: {e}")
        return "Sorry, there was an issue processing your request."

# --- Voice Input (Recording and Transcription using Whisper) ---
def audio_callback(indata, frames, time_info, status):
    global audio_frames
    audio_frames.append(indata.copy())

def start_recording():
    global audio_frames, recording, stream
    audio_frames = []
    stream = sd.InputStream(samplerate=16000, channels=1, callback=audio_callback)
    stream.start()
    recording = True
    print("[Voice] Recording started...")
    play_sound("confirmation.mp3")  # play a confirmation sound

def stop_recording():
    global stream, recording
    if stream is not None:
        stream.stop()
        stream.close()
    recording = False
    print("[Voice] Recording stopped.")
    play_sound("confirmation.mp3")
    audio = np.concatenate(audio_frames, axis=0)
    return audio

def save_audio_to_temp(audio, fs=16000):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        sf.write(tmpfile.name, audio, fs)
        return tmpfile.name

def transcribe_audio(audio_file, model):
    print("[Voice] Transcribing audio...")
    result = model.transcribe(audio_file)
    text = result["text"].strip()
    return text

# --- Text-to-Speech using Edge TTS ---
async def speak_text_async(text, lang="en"):
    # Choose voice based on language
    voice = "en-US-EmmaNeural" if lang == "en" else "es-ES-ElviraNeural"
    try:
        communicator = edge_tts.Communicate(text, voice)
        temp_filename = "temp_response.mp3"
        # Save the synthesized speech to a temporary file
        await communicator.save(temp_filename)
        # Play the saved file
        play_sound(temp_filename)
        os.remove(temp_filename)
    except Exception as e:
        send_notification("Voice Assistant", "TTS Error: {e}")
        print(f"[TTS] Error: {e}")

def speak_text(text, lang="en"):
    asyncio.run(speak_text_async(text, lang))

# --- Toggle Recording (Hotkey) ---
def toggle_recording():
    global recording, whisper_model
    if not recording:
        start_recording()
    else:
        audio = stop_recording()
        temp_audio_file = save_audio_to_temp(audio)
        user_text = transcribe_audio(temp_audio_file, whisper_model)
        os.remove(temp_audio_file)
        print(f"[You]: {user_text}")
        if user_text.lower() in exit_commands:
            print("[Assistant]: Goodbye!")
            speak_text("Goodbye!", lang="en")
            send_notification("Voice Assistant", "Goodbye!")
            os._exit(0)
        response = ask_ollama(user_text)
        print(f"[Assistant]: {response}")
        send_notification("Voice Assistant", f"{response}")
        try:
            detected = detect(response)
            lang_code = "en" if detected == "en" else detected
        except Exception as e:
            print(f"[Language Detection] Error: {e}")
            lang_code = "en"
        speak_text(response, lang=lang_code)

# --- Main ---
if __name__ == "__main__":
    print(f"[INIT] Model has initialized. Press Alt to start/stop recording")
    send_notification("Voice Assistant", "Voice assistant is ready. Press alt to start/stop recording")
    keyboard.add_hotkey('alt', toggle_recording) #Customize hotkeys here
    keyboard.wait('esc') #Customize exit key here

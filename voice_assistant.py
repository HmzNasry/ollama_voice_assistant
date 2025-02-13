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
from trio import current_time
import whisper
import keyboard
from datetime import date, datetime
from langdetect import detect
from plyer import notification
import ollama
from llm_axe import OllamaChat, Agent, OnlineAgent
import edge_tts
import warnings
import re
import signal  

warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")
warnings.filterwarnings("ignore", message="Performing inference on CPU when CUDA is available")
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

HISTORY_FILE = "conversation_history.json"
exit_commands = ["bye", "quit", "exit"]
recording = False
audio_frames = []
whisper_model = whisper.load_model("medium", device="cpu")

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = 0

# Global variables for TTS playback
tts_process = None
is_speaking = False  # True when TTS is actively speaking
tts_stop_requested = False  # Flag to signal stop request
current_tts_file = None   # Stores the name of the current TTS temp file

def play_sound(sound_file):
    global tts_process
    tts_process = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", sound_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP 
    )

def stop_speech():
    global tts_process, is_speaking, tts_stop_requested, current_tts_file
    if is_speaking:
        tts_stop_requested = True
        # Attempt to delete the TTS file; this may force ffplay to fail reading.
        if current_tts_file and os.path.exists(current_tts_file):
            try:
                os.remove(current_tts_file)
                print("[TTS] Temp file deleted.")
            except Exception as e:
                print(f"[TTS] Error deleting temp file: {e}")
        is_speaking = False
        tts_process = None
        current_tts_file = None
        print("[TTS] Speech stopped.")

def send_notification(title, message):
    truncated = message[:256]
    notification.notify(title=title, message=truncated, app_name="Voice Assistant", timeout=1)

city, country = "Lynnwood", "United States"
dt_now = datetime.now()
date_str = dt_now.strftime("%Y-%m-%d %H:%M:%S")
conversation_context = (
    f"Keep your answers very short and concise."
    f"Do not ask the user questions, offer assistance or say anything irrelevan, keep your answers concice and very short"
    f"Do not use markdown, symbols, or abbreviations. "
    f"The user's location is {city}, {country}, and the current time is {date_str} PST <- THIS INFORMATION IS NOT THE MAIN POINT OF THE CONVERSATIONS, IT IS NOT RELEVANT UNLESS YOU NEED IT! SO STOP MENTIONING IT EVERY TIME!. "
    f"Do not hallucinate or give false information."
    f"Do not talk about things that you are not updated on, like the weather, news, or sports, ***UNLESS*** You have relevant information from the internet."
    f"Do not the assert the time or location or date randomly if you are not prompted to"
    f"KEEP YOUR ANSWERS SHORT AND DONT SAY STUFF THAT YOU ARE NOT SURE OF"
)
print(f"[INIT] Detected Location: {city}, {country}")

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

async def ask_ollama_async(query):
    try:
        print(f"\n[ask_ollama] Processing query: {query}")
        history = load_conversation_history()
        system_prompt = conversation_context

        llm = OllamaChat(model="qwen2.5:7b")

        plan_agent = Agent(
            llm,
            custom_system_prompt=f"""
            You have one job: decide if the user query requires an internet search for an LLM like yourself.
            Your response MUST be a valid JSON object with exactly two keys: "internet" and "search_query". 
            - "internet" must be either "yes" or "no".
            - "search_query" must be a string: if internet is "yes", provide an optimized search query; if "no", use an empty string.
            Do NOT include any extra text, explanations, markdown, or symbols.
            Respond exactly with the JSON object only.
            if you need the time in location, it is {city}, {country}, {date_str}
            Example: {{{{ "internet": "yes", "search_query": "current weather in Seattle" }}}}
            
            You are just a plan agent, the responses in the history are not from you and you don’t have anything to do with them.
            Your job is only to analyze and decide if an internet search is needed.
            If your response does not follow the format of the example, you will break the system.
            """
        )

        json_regex = r'^\s*\{\s*"internet"\s*:\s*"(yes|no)"\s*,\s*"search_query"\s*:\s*".*"\s*\}\s*$'
        loop = asyncio.get_event_loop()
        plan_response = await loop.run_in_executor(
            None,
            plan_agent.ask,
            (
                "You have one job: decide if the user query requires an internet search. note that you run in the background and you cannot interact with the user, your only job is to decide this, if it is already in conoversation history dont search again. "
                "Your response MUST be a valid JSON object with exactly two keys: \"internet\" and \"search_query\". "
                "- \"internet\" must be either \"yes\" or \"no\". "
                "- \"search_query\" must be a string: if internet is \"yes\", provide an optimized search query; if \"no\", use an empty string. "
                "Do NOT include any extra text, explanations, markdown, or symbols. "
                "Respond exactly with the JSON object only. "
                "Example: {\"internet\": \"yes\", \"search_query\": \"example search query\"} "
                "You are just a plan agent, the responses in the history are not from you and you don’t have anything to do with them. "
                "Your job is only to analyze and decide if an internet search is needed. "
                "If your response does not follow the format of the example, you will break the system. "
                "Remember to only search the internet if UP TO DATE information is required, math problems and general questions do not require internet search!"
                f"USER QUERY: {query}, HISTORY: {history}"
            )
        )

        print(f"[Plan Agent] Response: {repr(plan_response)}")

        if not re.match(json_regex, plan_response.strip()):
            m = re.search(r'\{.*\}', plan_response, re.DOTALL)
            if m:
                try:
                    plan_data = json.loads(m.group(0))
                except json.JSONDecodeError:
                    print("[ERROR] Extracted JSON block invalid. Fallback to direct search.")
                    plan_data = {"internet": "yes", "search_query": query}
            else:
                print("[ERROR] Plan agent did not return valid JSON. Fallback to direct search.")
                plan_data = {"internet": "yes", "search_query": query}
        else:
            try:
                plan_data = json.loads(plan_response)
            except json.JSONDecodeError:
                print("[ERROR] JSON Parsing Failed. Fallback to direct search.")
                plan_data = {"internet": "yes", "search_query": query}

        method = None
        summary = None
        url = None

        if plan_data.get("internet") == "yes" and plan_data.get("search_query"):
            print(f"[ask_ollama] Fetching real-time data for: {plan_data['search_query']}")
            search_url = f"http://localhost:8080/search?q={plan_data['search_query']}&format=json"
            try:
                search_response = await loop.run_in_executor(None, requests.get, search_url)
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
        elif plan_data.get("internet") == "yes" and plan_data.get("search_query") == "":
            print("[ERROR] Plan agent did not return valid JSON. Fallback to direct search.")
            plan_data = {"internet": "yes", "search_query": query}

        if method == "answers":
            system_prompt += f" Additional internet data: {summary}"
            messages = [{"role": "system", "content": system_prompt}]
            for u, a in zip(history["user"][-15:], history["assistant"][-15:]):
                messages.append({"role": "user", "content": u})
                messages.append({"role": "assistant", "content": a})
            messages.append({"role": "user", "content": query})
            response = await loop.run_in_executor(None, ollama.chat, "qwen2.5:7b", messages)
            response_text = response["message"]["content"].strip()
            update_conversation_history(query, response_text)
            return response_text

        elif method == "onlineagent":
            searcher = OnlineAgent(llm)
            online_answer = await loop.run_in_executor(None, searcher.search,
                f"{conversation_context}, extract info from this website: {url} to answer the user's question, {query} considering past interactions, {history}")
            update_conversation_history(query, online_answer)
            cleaned_answer = online_answer.replace('Based to the information from the internet,', '')
            return cleaned_answer

        else:
            print("[ask_ollama] No valid internet data found. Proceeding with local knowledge.")
            messages = [{"role": "system", "content": system_prompt}]
            for u, a in zip(history["user"][-15:], history["assistant"][-15:]):
                messages.append({"role": "user", "content": u})
                messages.append({"role": "assistant", "content": a})
            messages.append({"role": "user", "content": query})
            response = await loop.run_in_executor(None, ollama.chat, "qwen2.5:7b", messages)
            response_text = response["message"]["content"].strip()
            update_conversation_history(query, response_text)
            return response_text

    except Exception as e:
        print(f"[ask_ollama] Error: {e}")
        return "Sorry, there was an issue processing your request."

def ask_ollama(query):
    return asyncio.run(ask_ollama_async(query))

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
    play_sound("confirmation.mp3")

def stop_recording():
    global stream, recording
    if stream is not None:
        stream.stop()
        stream.close()
    recording = False
    print("[Voice] Recording stopped.")
    play_sound("confirmation.mp3")
    if len(audio_frames) > 0:
        audio = np.concatenate(audio_frames, axis=0)
    else:
        audio = np.array([])
    return audio

def save_audio_to_temp(audio, fs=16000):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        sf.write(tmpfile.name, audio, fs)
        return tmpfile.name

def transcribeAudio(audio_file, model):
    print("[Voice] Transcribing audio...")
    result = model.transcribe(audio_file)
    text = result["text"].strip()
    return text

async def speak_text_async(text, lang="en"):
    global tts_process, is_speaking, tts_stop_requested, current_tts_file
    is_speaking = True
    if lang == "en":
        voice = "en-US-EmmaNeural"
    elif lang == "ar":
        voice = "ar-EG-SalmaNeural"
    elif lang == "es":
        voice = "es-ES-ElviraNeural"
    else:
        voice = "en-US-EmmaNeural"
    try:
        communicator = edge_tts.Communicate(text, voice, rate="+15%")
        temp_filename = "temp_response.mp3"
        current_tts_file = temp_filename
        await communicator.save(temp_filename)
        play_sound(temp_filename)

        while tts_process is not None and tts_process.poll() is None:
            if tts_stop_requested:
                break
            await asyncio.sleep(0.1)
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    except Exception as e:
        print(f"[TTS] Error: {e}")
        send_notification("Voice Assistant", f"TTS Error: {e}")
    tts_stop_requested = False
    is_speaking = False

def speak_text(text, lang="en"):
    asyncio.run(speak_text_async(text, lang))

async def speak_and_notify(response, lang="en"):
    speak_task = asyncio.create_task(speak_text_async(response, lang))
    notify_task = asyncio.to_thread(send_notification, "Voice Assistant", response)
    await asyncio.gather(speak_task, notify_task)

def toggle_recording():
    global recording, whisper_model, is_speaking
    if is_speaking:
        stop_speech()
        return
    if not recording:
        start_recording()
    else:
        audio = stop_recording()
        temp_audio_file = save_audio_to_temp(audio)
        user_text = transcribeAudio(temp_audio_file, whisper_model)
        os.remove(temp_audio_file)
        print(f"[You]: {user_text}")
        if user_text.lower() in exit_commands:
            print("[Assistant]: Goodbye!")
            asyncio.run(speak_and_notify("Goodbye!", "en"))
            os._exit(0)
        response = ask_ollama(user_text)
        print(f"[Assistant]: {response}")
        try:
            detected = detect(response)
            lang_code = "en" if detected == "en" else detected
        except Exception as e:
            print(f"[Language Detection] Error: {e}")
            lang_code = "en"
        asyncio.run(speak_and_notify(response, lang_code))

if __name__ == "__main__":
    print("[INIT] Voice Assistant ready, press alt to start/stop recording or to stop speech.")
    send_notification("Voice Assistant", "Voice assistant is ready. Press alt to start/stop recording or stop speech.")
    keyboard.add_hotkey('alt', toggle_recording)
    keyboard.wait('esc')
    send_notification("Shutting Down", "Goodbye!")
    play_sound("close.wav")

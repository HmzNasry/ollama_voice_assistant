from typing import Tuple
import os
import requests
from datetime import datetime

# CUSTOMIZE: File settings
HISTORY_FILE = "conversation_history.json"

# CUSTOMIZE: Voice commands to exit the assistant
EXIT_COMMANDS = ["bye", "quit", "exit"]

# CUSTOMIZE: Audio recording settings
SAMPLE_RATE = 16000  # Audio sample rate in Hz
CHANNELS = 1         # Mono audio
FRAME_DURATION_MS = 30  # Frame duration in milliseconds

# CUSTOMIZE: LLM model settings - change to your preferred Ollama model
LLM_MODEL = "llama3.1"

# CUSTOMIZE: Default location if auto-detection fails
DEFAULT_CITY = "Your City"
DEFAULT_COUNTRY = "Your Country"

def detect_location() -> Tuple[str, str]:
    """Auto-detect user location from IP address with fallback to defaults."""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data.get('city', DEFAULT_CITY), data.get('country_name', DEFAULT_COUNTRY)
        else:
            print(f"[LOCATION] Error: HTTP {response.status_code}")
    except Exception as e:
        print(f"[LOCATION] Detection failed: {e}")
    
    return DEFAULT_CITY, DEFAULT_COUNTRY

# Get location and date information
CITY, COUNTRY = detect_location()
DATE_STR = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# CUSTOMIZE: System prompt that controls the assistant's behavior and responses
CONVERSATION_CONTEXT = (
    f"You are a helpful voice assistant. "
    f"The user's location is {CITY}, {COUNTRY}, and the current time is {DATE_STR}. "
    f"Keep your answers concise, clear and helpful. "
    f"Only mention location and time information when directly relevant to the user's question. "
    f"Do not make up information about current events, weather, or news unless you have access to it via internet search. "
    f"Respond directly to questions without unnecessary acknowledgments or apologies. "
    f"When unsure about something, clearly state that you don't know rather than speculating."
)
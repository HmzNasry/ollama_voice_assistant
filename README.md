Voice Assistant using Llama 3.1 and Speech Recognition

This project is a voice assistant that responds to user queries using Llama 3.1 and provides a sassy yet professional interaction style. It includes voice recognition, text-to-speech synthesis, and conversation history management.

Features

Voice Recognition: Uses speech_recognition to convert speech to text.

Text-to-Speech (TTS): Uses edge_tts to generate speech responses.

Conversation Context: Maintains conversation history in conversation_history.json.

Ollama Integration: Communicates with the Llama 3.1 model via subprocess.

Keyboard Shortcuts: Press Alt to start and stop recording; press Esc to exit.        

Desktop Notifications: Uses plyer.notification for feedback.

Sassy Personality: Responds with a mix of teasing and professionalism.

Requirements

Python 3.13.1

Required dependencies (install using pip):

pip install keyboard dotenv speechrecognition edge_tts plyer

FFmpeg installed (needed for playing audio responses)

Llama 3.1 installed and accessible via ollama

Installation

Clone the Repository:

git clone https://github.com/HmzNasry/windows_voice_assistant_ollama.git
cd \windows_voice_assistant_ollama


Install Dependencies:

pip install -r requirements.txt

Setup Environment Variables:

Create a .env file in the project directory (if needed for customization).

Ollama Setup

Install Ollama:

curl -fsSL https://ollama.ai/install.sh | sh

Verify Installation:

ollama --version

Run Llama 3.1 in Ollama:

ollama run llama3.1

More Information: Visit https://ollama.ai/docs

Running the Assistant

Start the assistant:

python main.py

Usage:

Press Alt to start/stop voice recording.

Press Esc to exit.

Responses will be spoken aloud and displayed in the terminal.

Notes

The assistant saves conversation history in conversation_history.json.

Uses ffplay to play response audio (ffmpeg is required).

Requires a working microphone for speech input.

Download Links

Python 3.13.1: https://www.python.org/downloads/release/python-3131/

FFmpeg: https://ffmpeg.org/download.html

Ollama: https://ollama.ai/docs

Author

Developed by Hamza.

Voice Assistant using Llama 3.1 and Speech Recognition


This project is a voice assistant that responds to user queries using Llama 3.1 and provides a  professional interaction style. It includes voice recognition, text-to-speech synthesis, and conversation history management.

Video Demonstration: https://www.youtube.com/watch?v=2ckEW8PPW-w

Features

Voice Recognition: Uses speech_recognition to convert speech to text.

Text-to-Speech (TTS): Uses edge_tts to generate speech responses.

Conversation Context: Maintains conversation history in conversation_history.json.

Ollama Integration: Communicates with the Llama 3.1 model via subprocess.

Keyboard Shortcuts: Press Alt to start and stop recording; press Esc to exit.        

Desktop Notifications: Uses plyer.notification for feedback.

Requirements

Python 3.13.1 (I Haven't Tested Other Versions)

Required dependencies (install using pip):

pip install keyboard dotenv speechrecognition edge_tts plyer

FFmpeg installed (needed for playing audio responses)

Llama 3.1 installed and accessible via ollama


***NOTES***

***MAKE SURE TO INSTALL FFMPEG AND PUT IT IN YOUR SYSTEM'S PATH ENVIRONMENT VARIABLE**

Make sure you have ollama installed, default model for this is llama3.1, but can be changed from the python file

It is configured to run in the background, press esc to stop it from running, if you cant, go to the task manager and stop pythton, it can also be stopped if you say bye or go away or quit or shut up.

Inside the python code I've added some comments where you can change some of the preferences to however you like, make sure all the files are in the same directory.

Installation

- Clone the Repository: - 

git clone https://github.com/HmzNasry/windows_voice_assistant_ollama.git


cd \windows_voice_assistant_ollama


- Install Dependencies: -

pip install -r requirements.txt

Ollama Setup

- Install Ollama: -

curl -fsSL https://ollama.ai/install.sh | sh

- Verify Installation: -

ollama --version

 - Run Llama 3.1 in Ollama: -

ollama run llama3.1

More Information: Visit https://ollama.ai/docs

Running the Assistant -

- Start the assistant:

python voice_assistant.py

**OR**

Theres a bat file in the same folder that can automatically start the program for you, you can either press win + r and do shell:startup and copy and paste the file in there, or figure out another way to make a hotkey or something to run that .bat file

- Usage: -

Press Alt to start/stop voice recording.

Press Esc to exit.

Responses will be spoken aloud and partly displayed in notifications.

- Notes -

The assistant saves conversation history in conversation_history.json.

Uses ffplay to play response audio (ffmpeg is required).

Requires a working microphone for speech input.

- Download Links -

Python 3.13.1: https://www.python.org/downloads/release/python-3131/

FFmpeg: https://ffmpeg.org/download.html

Ollama: https://ollama.ai/docs

Author

Developed by Hamza.

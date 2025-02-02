🎤 AI Voice Assistant
A local voice assistant powered by Ollama (Llama 3.1) for smart, chatty, and interactive conversations.
It remembers previous conversations, has a sassy personality, and supports multiple languages.

🚀 Features
✔ Voice Recognition: Uses Google Speech Recognition to process spoken commands.
✔ AI Responses: Uses Ollama (Llama 3.1) to generate smart, contextual replies.
✔ Memory System: Saves and recalls conversation history for better interactions.
✔ Text-to-Speech (TTS): Uses Microsoft Edge TTS for natural speech synthesis.
✔ Customizable Personality: Can be sassy, serious, or technical (modifiable in conversation_history.json).
✔ Notification Support: Sends system notifications for assistant responses.
✔ Background Mode: Runs silently in the background using a .bat file.

🔧 Installation Guide
1️⃣ Install Dependencies
Run the following command to install all required Python libraries:

sh
Copy
Edit
pip install -r requirements.txt
OR install manually:

sh
Copy
Edit
pip install speechrecognition plyer langdetect edge-tts llm-axe ollama keyboard
2️⃣ Install ffmpeg (Required for Audio)
✅ Windows:

Download ffmpeg from here.

Extract the ZIP file to C:\ffmpeg.

Add C:\ffmpeg\bin to System Path (Environment Variables).

Verify installation by running:

sh
Copy
Edit
ffmpeg -version
✅ Linux (Debian/Ubuntu):

sh
Copy
Edit
sudo apt install ffmpeg
✅ MacOS:

sh
Copy
Edit
brew install ffmpeg
▶️ How to Use
1️⃣ Start the Assistant
Run the script using:

sh
Copy
Edit
python assistant.py
Or use the background mode:

sh
Copy
Edit
start_assistant.bat
2️⃣ Interacting with the Assistant
Press ALT to start/stop recording.
Speak your question or command.
The assistant will respond vocally.
Press ESC to exit.
3️⃣ Example Commands
Command	Response
"What's the weather?"	"I don't have real-time data, but you can check online!"
"Tell me a joke."	"Why don’t programmers like nature? It has too many bugs!"
"Translate hello to Spanish."	"Hola!"
"Bye."	"Goodbye! Have a great day!"
📜 Understanding the Code
🔹 1. Conversation Memory (conversation_history.json)
Stores past conversations for contextual responses.
Modify Assistant Personality:
json
Copy
Edit
{
  "context": "Be a sassy and very smart voice assistant...",
  "user": [],
  "assistant": []
}
Change "context" to customize personality.
🔹 2. Recording Hotkeys
ALT = Start/Stop recording.
ESC = Exit the assistant.
🔹 3. Audio Playback (ffmpeg)
Uses ffmpeg to play confirmation sounds (confirmation.mp3, close.wav).
Uses edge-tts for speech synthesis.
🔹 4. Assistant Modes
Local Llama 3.1 (default): Runs offline using Ollama.
Online Mode: If "online" is in the query, it will search the web.
🔄 Customizing the Assistant
Change	Location	How to Modify
Personality	conversation_history.json	Edit "context"
Hotkeys	keyboard.add_hotkey()	Change "alt" to another key
Exit Commands	exit_commands list	Add/remove phrases
🏃 Running in the Background (start_assistant.bat)
To start the assistant without a visible console window, use the provided .bat file.

Content of start_assistant.bat:

bat
Copy
Edit
@echo off
pythonw assistant.py
exit
This runs the script silently.
You can stop the assistant by using Task Manager (taskkill /IM pythonw.exe /F).
📌 Troubleshooting
Issue	Solution
"ffmpeg not found"	Make sure ffmpeg is installed and added to PATH.
"No module named X"	Run pip install -r requirements.txt again.
Assistant doesn't speak	Check temp_response.mp3 exists and edge-tts is working.
Hotkeys not working	Run the script as Administrator.
🛠️ Future Improvements
✅ Add wake word detection ("Hey Assistant")
✅ Support for more voices & languages
✅ Improve multi-turn conversation handling
❤️ Credits
Built by Hamza
Using Llama 3.1, ollama, edge-tts, and speechrecognition.

📌 Markdown Code for README
To copy this README into a file (README.md)

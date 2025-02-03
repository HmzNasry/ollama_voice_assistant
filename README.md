# 🎤 AI Voice Assistant

A **local voice assistant** powered by **Ollama (Llama 3.1)** for **smart, chatty, and interactive conversations**.  
It **remembers previous conversations**, has a **sassy personality**, and **supports multiple languages**.

## 🚀 Features

✔ **Voice Recognition**: Uses **Google Speech Recognition** to process spoken commands.  
✔ **AI Responses**: Uses **Ollama (Llama 3.1)** to generate **smart, contextual** replies.  
✔ **Memory System**: Saves and recalls conversation history for **better interactions**.  
✔ **Text-to-Speech (TTS)**: Uses **Microsoft Edge TTS** for **natural speech synthesis**.  
✔ **Customizable Personality**: Can be **sassy, serious, or technical** (modifiable in `conversation_history.json`).  
✔ **Notification Support**: Sends **system notifications** for **assistant responses**.  
✔ **Background Mode**: Runs **silently in the background** using a `.bat` file.  

---

## 🔧 Installation Guide

### **1️⃣ Install Dependencies**
Run the following command to install all required **Python libraries**:

```sh
pip install -r requirements.txt
```

**OR** install manually:

```sh
pip install speechrecognition plyer langdetect edge-tts llm-axe ollama keyboard
```

---

### **2️⃣ Install `ffmpeg` (Required for Audio)**
✅ **Windows**:
1. Download `ffmpeg` from [here](https://www.gyan.dev/ffmpeg/builds/).
2. Extract the ZIP file to `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to **System Path** (Environment Variables).
4. Verify installation by running:

   ```sh
   ffmpeg -version
   ```

✅ **Linux (Debian/Ubuntu)**:
```sh
sudo apt install ffmpeg
```

✅ **MacOS**:
```sh
brew install ffmpeg
```

---

## ▶️ How to Use

### **1️⃣ Start the Assistant**
Run the script using:

```sh
python assistant.py
```

Or use the **background mode**:

```sh
start_assistant.bat
```

### **2️⃣ Interacting with the Assistant**
- Press **ALT** to start/stop recording.  
- Speak your **question** or **command**.  
- The assistant will **respond vocally**.  
- Press **ESC** to **exit**.

### **3️⃣ Example Commands**
| Command | Response |
|---------|----------|
| *"What's the weather?"* | *"I don't have real-time data, but you can check online!"* |
| *"Tell me a joke."* | *"Why don’t programmers like nature? It has too many bugs!"* |
| *"Translate hello to Spanish."* | *"Hola!"* |
| *"Bye."* | *"Goodbye! Have a great day!"* |

---

## 📜 Understanding the Code

### **🔹 1. Conversation Memory (`conversation_history.json`)**
- Stores **past conversations** for **contextual responses**.
- **Modify Assistant Personality**:
  ```json
  {
    "context": "Be a sassy and very smart voice assistant...",
    "user": [],
    "assistant": []
  }
  ```
  - Change `"context"` to **customize personality**.

### **🔹 2. Recording Hotkeys**
- **`ALT`** = Start/Stop recording.
- **`ESC`** = Exit the assistant.

### **🔹 3. Customizing Sounds**
- **Confirmation Sound** (`confirmation.mp3`) = Plays when recording starts/stops.
- **Exit Sound** (`close.wav`) = Plays when the assistant is closed.

### **🔹 4. Key Code Parts**
#### **Speech Recognition (Google API)**
- The assistant **listens to the microphone** and **converts speech to text**:
  ```python
  recognizer = sr.Recognizer()
  mic = sr.Microphone()

  with mic as source:
      recognizer.adjust_for_ambient_noise(source)
      audio_data = recognizer.listen(source, timeout=None)
  ```

#### **AI Model (Ollama Llama 3.1)**
- The **Llama 3.1 model** generates responses:
  ```python
  response = ollama.chat(model="llama3.1", messages=[
      {"role": "system", "content": conversation_context},
      {"role": "user", "content": full_prompt}
  ])
  response_text = response["message"]["content"].strip()
  ```

#### **Text-to-Speech (Microsoft Edge TTS)**
- Converts the assistant's response into **natural-sounding speech**:
  ```python
  communicate = Communicate(response_text, voice="en-US-EmmaNeural")
  await communicate.save("temp_response.mp3")
  ```

---

## 📂 Running the Assistant in the Background

### **What is `start_assistant.bat`?**
This file runs the assistant **silently** in the background.

**Contents of `start_assistant.bat`**:
```bat
@echo off
start /min pythonw assistant.py
```
- **`pythonw`** = Runs Python without opening a console window.
- **`start /min`** = Minimizes the process.

### **How to Use the `.bat` File**
1. **Double-click** `start_assistant.bat` to **run the assistant silently**.
2. Press **ALT** to start/stop voice input.
3. Press **ESC** to exit.

---

## 🎉 Conclusion
Your AI Voice Assistant is now ready to use! Customize responses, adjust memory settings, or change voices to make it more personal. 🚀

Have fun with your smart assistant! 🤖🎤


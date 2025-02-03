#  Ollama Voice Assistant 🦙

A **local voice assistant** powered by **Ollama (Llama 3.1)** for **smart, chatty, and interactive conversations**.  
It **remembers previous conversations**, has a **sassy personality**, and **supports multiple languages**.

## 🚀 Features

- **Voice Recognition**: Uses **Google Speech Recognition** to process spoken commands.  
- **AI Responses**: Uses **Ollama (Llama 3.1)** to generate **smart, contextual** replies.  
- **Memory System**: Saves and recalls conversation history for **better interactions**.  
- **Text-to-Speech (TTS)**: Uses **Microsoft Edge TTS** for **natural speech synthesis**.  
- **Customizable Personality**: Can be **sassy, serious, or technical** (modifiable in `conversation_history.json`).  
- **Notification Support**: Sends **system notifications** for **assistant responses**.  
- **Background Mode**: Runs **silently in the background** using a `.bat` file.  

---

## 🔧 Installation Guide

### **1️. Install Dependencies**
Run the following command to install all required **Python libraries**:

```sh
pip install -r requirements.txt
```

**OR** install manually:

```sh
pip install speechrecognition plyer langdetect edge-tts llm-axe ollama keyboard
```

---

### **2️. Install `ffmpeg` (Required for Audio)**
🇽 **Windows**:
1. Download `ffmpeg` from [here](https://www.gyan.dev/ffmpeg/builds/).
2. Extract the ZIP file to `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to **System Path** (Environment Variables).
4. Verify installation by running:

   ```sh
   ffmpeg -version
   ```

🇱 **Linux (Debian/Ubuntu)**:
```sh
sudo apt install ffmpeg
```

🇲 **MacOS**:
```sh
brew install ffmpeg
```

---

## 📺 Setting up Ollama (Required for AI Responses)

Ollama provides **local LLM inference** without internet dependency.

### **1. Install Ollama**
Download and install Ollama from the official site:
- **Windows/macOS/Linux**: [Ollama Official Site](https://ollama.ai/download)

### **2. Download the Default Model**
Run the following command to download **Llama 3.1**:
```sh
ollama pull llama3.1
```

### **3. Starting Local Server**
After you have the model installed, run:
```
ollama serve
```

### **4. Recommended Models Based on Hardware**

| Hardware Specs | Recommended Model |
|--------------|----------------|
| ✅ **Low-end (8GB RAM, iGPU, laptop)** | `mistral` or `phi` |
| ✅ **Mid-range (16GB RAM, RTX 3060/4060)** | `llama3` (smaller versions) |
| ✅ **High-end (32GB+ RAM, RTX 4080/4090, A100, H100)** | `llama3.1` or `mixtral` |
| ✅ **AI-optimized GPU (3090, 4090, A100, etc.)** | `gemma`, `command-r` |

To change models, update the `model` parameter in the code:
```python
response = ollama.chat(model="<CHANGE THIS>", messages=[
    {"role": "system", "content": conversation_context},
    {"role": "user", "content": full_prompt}
])
```

---

## ▶️ How to Use

### **1️. Start the Assistant**
Run the script using:

```sh
python voice_assistant.py
```

Or use the **background mode**:

```sh
va.bat
```

### **2️. Interacting with the Assistant**
- Press **ALT** to start/stop recording.  
- Speak your **question** or **command**.  
- The assistant will **respond vocally**.
- If you want it to search the internet, you have to mention the trigger word 'online' in your response, but it will be ignored when searching the internet, (it wont mess up your prompt)***
- Press **ESC** to **exit**.

### **3️. Example Commands**
| Command | Response |
|---------|----------|
| *"What's the weather in Seattle online?"* | *"According to the information from the internet, the weather in seattle is 37 degrees fahrenheit"* |
| *"Tell me a joke."* | *"Why don’t programmers like nature? It has too many bugs!"* |
| *"Translate hello to Spanish."* | *"Hola!"* |

---

## 🧠 Understanding the Code

### **🔹 1. Conversation Memory (`conversation_history.json`)**
- Stores **past conversations** for **contextual responses**.
- **Modify Assistant Personality**:
  ```json
  {
    "context": "Be a professional and engaging voice assistant...",
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
### **Online Mode**
- The **Model** generates a response using the internet through llm_axe's onlineagent:
```python
if "online" in query.lower():
      print("Switching to internet search mode...")
      llm = OllamaChat(model="my_llama")
      agent = OnlineAgent(llm)
      e = query.replace('online', '')
      search_response = agent.search(e)
      print("Raw search response:", search_response)
      response_text = search_response.strip() if isinstance(search_response, str) else "I couldn't find real-time information."
```

---

## 📂 Running the Assistant in the Background

### **What is `start_assistant.bat`?**
This file runs the assistant **silently** in the background.

**Contents of `va.bat`**:
```bat
@echo off
start /min pythonw voice_assistant.py
```
- **`pythonw`** = Runs Python without opening a console window.
- **`start /min`** = Minimizes the process.

### **How to Use the `.bat` File**
1. **Double-click** `va.bat` to **run the assistant silently**.
2. Press **ALT** to start/stop voice input.
3. Press **ESC** to exit.

---

## 🎉 Conclusion
Your AI Voice Assistant is now ready to use! Customize responses, adjust memory settings, or change voices to make it more personal. 🚀

Have fun with your smart assistant! 🤖🎤


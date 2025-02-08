# Ollama Voice Assistant – Enhanced Version (Under Development)

> **Note:** This is an updated version of the Ollama Voice Assistant incorporating new AI models, functions, internet search integration via SearxNG, and enhanced voice processing. This README provides comprehensive instructions on installation, configuration, and usage.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation Guide](#installation-guide)
   - [Python Dependencies](#python-dependencies)
   - [FFmpeg Installation](#ffmpeg-installation)
   - [Whisper Installation](#whisper-installation)
   - [Ollama Setup](#ollama-setup)
   - [SearxNG Setup](#searxng-setup)
4. [Usage](#usage)
5. [Code Structure and Customization](#code-structure-and-customization)
6. [Troubleshooting](#troubleshooting)
7. [License and Contributions](#license-and-contributions)

---

## Overview

This voice assistant is a local application that uses:
- **Ollama** for AI model inference (default model: `qwen2.5:7b`, customizable).
- **Whisper (medium model)** for high‑quality speech-to-text transcription.
- **Edge TTS** for natural, synthesized voice responses.
- **SearxNG** for real‑time internet search queries (when required).
- **Keyboard hotkeys** for toggling recording and exiting the assistant.
- **Conversation memory** stored in a JSON file for context‑aware interactions.

---

## Features

- **Voice Recognition:**  
  Captures audio via `sounddevice` and transcribes using OpenAI’s Whisper.

- **AI-Powered Responses:**  
  Uses Ollama (via the `llm_axe` library) to generate intelligent, context‑rich replies.

- **Internet Search Integration:**  
  Employs a custom search logic using a local SearxNG instance to fetch up‑to‑date data when needed.  
  *Refer to the [SearxNG Documentation](https://searxng.github.io/searxng/) for setup instructions.*

- **Natural Text-to-Speech:**  
  Uses Edge TTS to convert responses to speech. Voices adjust based on detected language (default: `en-US-EmmaNeural` for English, `es-ES-ElviraNeural` for Spanish).

- **Conversation Memory:**  
  Stores previous interactions in `conversation_history.json` to provide context in follow‑up conversations.

- **Hotkey Controls:**  
  Press **ALT** to start/stop recording and **ESC** to exit the assistant.

---

## Installation Guide

### Python Dependencies

Ensure you have Python 3.8+ installed. Install the required packages using:

```bash
pip install numpy sounddevice soundfile whisper keyboard langdetect plyer edge-tts ollama llm-axe requests
```

Alternatively, use a `requirements.txt` file if available.

---

### FFmpeg Installation (Required for Audio Playback)

The assistant uses **ffplay** (a component of FFmpeg) to play audio files. Install FFmpeg as follows:

#### **Windows:**

1. Download FFmpeg from [FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/).
2. Extract the ZIP file (e.g., to `C:\ffmpeg`).
3. Add `C:\ffmpeg\bin` to your System PATH (via Environment Variables).
4. Verify installation by running:
   ```bash
   ffmpeg -version
   ```

#### **Linux (Debian/Ubuntu):**

```bash
sudo apt update
sudo apt install ffmpeg
```

#### **macOS:**

```bash
brew install ffmpeg
```

---

### Whisper Installation

Whisper is used for transcribing recorded audio. Install Whisper with:

```bash
pip install -U openai-whisper
```

*Note:* Whisper’s models can require significant memory. The script uses the medium model by default.

---

### Ollama Setup (For AI Responses)

Ollama provides local inference without internet dependency. To set up:

1. **Download and Install Ollama:**  
   Visit the [Ollama Official Site](https://ollama.ai/download) and follow the installation instructions for your OS.

2. **Pull a Model:**  
   For example, to pull the `qwen2.5:7b` model, run:
   ```bash
   ollama pull qwen2.5:7b
   ```

3. **Start the Ollama Server:**  
   Run:
   ```bash
   ollama serve
   ```

4. **Model Customization:**  
   Modify the model name in the code if you wish to use a different model.

---

### SearxNG Setup (For Internet Searches)

This version integrates SearxNG to perform real-time internet searches when needed.

1. **Installation and Configuration:**  
   Follow the detailed setup instructions in the [SearxNG Documentation](https://searxng.github.io/searxng/).

2. **Local Instance:**  
   Ensure your SearxNG instance is running and accessible, typically at `http://localhost:8080/search`.

3. **Integration in Code:**  
   The assistant sends search queries to this endpoint to fetch real-time data.

---

## Usage

### Running the Assistant

To start the voice assistant, run:

```bash
python voice_assistant.py
```

For background mode on Windows, use a batch file (e.g., `va.bat`):

```bat
@echo off
start /min pythonw voice_assistant.py
```

### Interacting with the Assistant

- **Press ALT**: Toggles recording (start/stop capturing your query).
- **Speak Your Command/Question**: Your speech is transcribed by Whisper.
- **Processing:**  
  The assistant uses Ollama to generate responses. It may perform an internet search via SearxNG if necessary (based on the custom prompt logic).
- **Response:**  
  The generated reply is saved in conversation history, synthesized to speech via Edge TTS, and played back.
- **Exit:**  
  Saying exit commands (e.g., "bye", "quit") or pressing ESC will terminate the application.

### Example Commands

| **Command**                                      | **Expected Behavior**                                                                                 |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| *"What's the weather like today"*      | Triggers an internet search via SearxNG and responds with current weather data, based on your city and current time.                       |
| *"Tell me a joke."*                              | Generates a joke using Ollama and reads it aloud.                                                   |
| *"Translate hello to Spanish."*                  | Provides a translation (e.g., "Hola!") and vocalizes the response in the appropriate language.       |

---

## License and Contributions

This project is open source. Contributions, issues, and feature requests are welcome. Please follow the repository’s contribution guidelines when submitting changes or enhancements.

---

Enjoy using the updated Ollama Voice Assistant, and feel free to provide feedback or contribute improvements as this version continues to evolve!


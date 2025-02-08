# Ollama Voice Assistant – Enhanced Version (Under Development)

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
- **Whisper (medium model)** for high-quality speech-to-text transcription.
- **Edge TTS** for natural, synthesized voice responses.
- **SearxNG** for real-time internet search queries (when required).
- **Keyboard hotkeys** for toggling recording and exiting the assistant.
- **Conversation memory** stored in a JSON file for context-aware interactions.

---

## Features

- **Voice Recognition:**  
  Captures audio via `sounddevice` and transcribes using OpenAI’s Whisper.

- **AI-Powered Responses:**  
  Uses Ollama (via the `llm_axe` library) to generate intelligent, context-rich replies.

- **Internet Search Integration:**  
  Employs a custom search logic using a local SearxNG instance to fetch up-to-date data when needed.  
  *Refer to the [SearxNG Documentation](https://searxng.github.io/searxng/) for setup instructions.*

- **Natural Text-to-Speech:**  
  Uses Edge TTS to convert responses to speech. Voices adjust based on detected language (default: `en-US-EmmaNeural` for English, `es-ES-ElviraNeural` for Spanish).

- **Conversation Memory:**  
  Stores previous interactions in `conversation_history.json` to provide context in follow-up conversations.

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

---

### SearxNG Setup

This version integrates SearxNG to perform real-time internet searches when needed.

1. **Installation and Configuration:**  
   Follow the detailed setup instructions in the [SearxNG Documentation](https://searxng.github.io/searxng/).

2. **Local Instance:**  
   Ensure your SearxNG instance is running and accessible, typically at `http://localhost:8080/search`.

3. **Integration in Code:**  
   The assistant sends search queries to this endpoint to fetch real-time data.

#### Quick Setup (Using Docker)
To quickly set up SearxNG, run:
```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng
```

Once running, access the container with:
```bash
docker exec -it searxng /bin/sh
```

To configure, edit the necessary settings files:

- **Windows (PowerShell)**
  ```powershell
  notepad C:\searxng\settings.yml
  ```
- **Linux/macOS**
  ```bash
  sudo nano /etc/searxng/settings.yml
  ```
- **Inside Docker Container**
  ```bash
  docker exec -it searxng /bin/sh
  nano /etc/searxng/settings.yml
  ```

After editing, restart the container:
```bash
docker restart searxng
```

---

## Usage

To start the voice assistant, run:
```bash
python main.py
```

Press **ALT** to start/stop recording and **ESC** to exit.

---

## Code Structure and Customization

The assistant consists of multiple components:
- `main.py`: Core script handling voice input/output.
- `speech_processing.py`: Handles Whisper and Edge TTS.
- `search_integration.py`: Manages SearxNG queries.
- `conversation_memory.json`: Stores user interactions.

You can customize:
- The default AI model (`qwen2.5:7b` in `main.py`).
- The speech synthesis voice (modify `Edge TTS` settings).
- The search behavior (`search_integration.py`).

---

## Troubleshooting

If issues arise:
- Ensure all dependencies are installed correctly.
- Verify that Whisper, Ollama, and SearxNG services are running.
- Check for missing environment variables or configuration errors.
- Run `python main.py --debug` for detailed logs.

---

## License and Contributions

This project is open-source. Contributions, bug fixes, and feature suggestions are welcome! Feel free to submit pull requests or open issues.

---

Enjoy using the enhanced Ollama Voice Assistant! 🚀


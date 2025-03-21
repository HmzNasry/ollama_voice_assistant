# Ollama Voice Assistant


---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation Guide](#installation-guide)
   - [Python Dependencies](#python-dependencies)
   - [FFmpeg Installation](#ffmpeg-installation)
   - [Whisper Installation](#whisper-installation)
   - [Ollama Setup](#ollama-setup)
   - [SearXNG Setup](#searxng-setup)
4. [Usage](#usage)
5. [Code Structure and Customization](#code-structure-and-customization)
6. [Troubleshooting](#troubleshooting)
7. [License and Contributions](#license-and-contributions)
8. [Adding the Zip Package on GitHub](#adding-the-zip-package-on-github)

---

## Overview

This voice assistant is a local application that uses:

- **Ollama** for AI model inference (default model: `llama3.1`, customizable).
- **Whisper (medium model)** for high-quality speech-to-text transcription.
- **Edge TTS** for natural, synthesized voice responses.
- **SearXNG** for real-time internet search queries (when required).
- **Keyboard hotkeys** for toggling recording and exiting the assistant.
- **Conversation memory** stored in a JSON file for context-aware interactions.

---

## Features

- **Voice Recognition:**\
  Captures audio via `sounddevice` and transcribes using OpenAI’s Whisper.

- **Internet Search Integration:**\
  Employs a custom search logic using a local SearXNG instance to fetch up-to-date data when needed.\
  *Refer to the [SearXNG Documentation](https://searxng.github.io/searxng/) for setup instructions.*

- **Natural Text-to-Speech:**\
  Uses Edge TTS to convert responses to speech. Voices adjust based on detected language (default: `en-US-AndrewNeural` for English, `es-ES-ElviraNeural` for Spanish).

- **Conversation Memory:**\
  Stores previous interactions in `conversation_history.json` to provide context in follow-up conversations.

- **Hotkey Controls:**\
  Press **ALT** to start/stop recording and **ESC** to exit the assistant.

---

## Installation Guide

### Python Dependencies

Ensure you have Python 3.8+ installed. Install the required packages using:

```bash
pip install -r requirements.txt
```

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

---

### Whisper Installation

Whisper is used for transcribing recorded audio. Install Whisper with:

```bash
pip install -U openai-whisper
```

*Note:* Whisper’s models can require significant memory. The script uses the medium model by default.
⚠️The script runs whisper on CPU to conserve memory for the ollama model⚠️

---

### Ollama Setup (For AI Responses)

Ollama provides local inference without internet dependency. To set up:

1. **Download and Install Ollama:**\
   Visit the [Ollama Official Site](https://ollama.ai/download) and follow the installation instructions for your OS.

2. **Pull a Model:**\
   For example, to pull the `llama3.1` model, run:

   ```bash
   ollama pull llama3.1
   ```

3. **Start the Ollama Server:**\
   Run:

   ```bash
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

This will start the assistant and allow it to run in the background.

---

### SearXNG Setup

This version integrates SearXNG to perform real-time internet searches when needed.

1. **Installation and Configuration:**  
   Follow the detailed setup instructions in the [SearXNG Documentation](https://searxng.github.io/searxng/).

2. **Local Instance:**  
   Ensure your SearXNG instance is running and accessible, typically at `http://localhost:8080/search`.

3. **Integration in Code:**  
   The assistant sends search queries to this endpoint to fetch real-time data.

#### Quick Setup (Using Docker)

Ensure that **SearXNG is inside the same directory as this project** or that you are **in the `searxng-docker/searxng` directory** when running these commands.

### **Editing Configuration Files for SearXNG (Docker Setup)**

#### **Windows (PowerShell)**
```powershell
cd searxng-docker\searxng
notepad settings.yml
```

**Paste the updated `settings.yml` content below:**

```yml
# see https://docs.searxng.org/admin/settings/settings.html#settings-use-default-settings
use_default_settings: true

server:
  secret_key: "<PUT A SECRET KEY HERE>"
  limiter: false  # Fully disable rate limiting
  public_instance: false  # Allow API access
  image_proxy: true
  api_enabled: true  
  http_protocol_version: "1.1"
  default_http_headers:
    Access-Control-Allow-Origin: "*"
    Access-Control-Allow-Methods: "GET, POST, OPTIONS"
    Access-Control-Allow-Headers: "*"

ui:
  static_use_hash: true

redis:
  url: redis://redis:6379/0

search:
  formats:
    - html
    - json 

```
Save and exit, then restart SearXNG:
```bash
docker restart searxng
```

#### **Editing `Caddyfile` (If Using Caddy)**
##### **Windows (PowerShell)**
```powershell
cd searxng-docker\searxng
notepad Caddyfile
```
**Paste the updated `Caddyfile` content below:**
```txt
{
  admin off
}

{$SEARXNG_HOSTNAME} {
  log {
        output discard
  }

  tls {$SEARXNG_TLS}

  @api {
        path /config
        path /healthz
        path /stats/errors
        path /stats/checker
        path /search
  }

  @static {
        path /static/*
  }

  @notstatic {
        not path /static/*
  }

  @imageproxy {
        path /image_proxy
  }

  @notimageproxy {
        not path /image_proxy
  }

  header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-XSS-Protection "1; mode=block"
        X-Content-Type-Options "nosniff"
        Permissions-Policy "accelerometer=(),ambient-light-sensor=(),autoplay=(),camera=(),encrypted-media=(),focus-without-user-activation=(),geolocation=(),gyroscope=(),magnetometer=(),microphone=(),midi=(),payment=(),picture-in-picture=(),speaker=(),sync-xhr=(),usb=(),vr=()"
        Feature-Policy "accelerometer 'none';ambient-light-sensor 'none'; autoplay 'none';camera 'none';encrypted-media 'none';focus-without-user-activation 'none'; geolocation 'none';gyroscope 'none';magnetometer 'none';microphone 'none';midi 'none';payment 'none';picture-in-picture 'none'; speaker 'none';sync-xhr 'none';usb 'none';vr 'none'"
        Referrer-Policy "no-referrer"
        X-Robots-Tag "noindex, noarchive, nofollow"
        -Server
  }

  header @api {
        Access-Control-Allow-Origin  "*"
        Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Access-Control-Allow-Headers "*"
        Access-Control-Expose-Headers "*"
  }

  header @static {
        Cache-Control "public, max-age=31536000"
        defer
  }

  header @notstatic {
        Cache-Control "no-cache, no-store"
        Pragma "no-cache"
  }

  header @imageproxy {
        Content-Security-Policy "default-src 'none'; img-src 'self' data:"
  }

  header @notimageproxy {
        Content-Security-Policy "upgrade-insecure-requests; default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self' https://github.com/searxng/searxng/issues/new; font-src 'self'; frame-ancestors 'self'; base-uri 'self'; connect-src 'self' https://overpass-api.de; img-src 'self' data: https://*.tile.openstreetmap.org; frame-src https://www.youtube-nocookie.com https://player.vimeo.com https://www.dailymotion.com https://www.deezer.com https://www.mixcloud.com https://w.soundcloud.com https://embed.spotify.com"
  }

  # SearXNG
  handle {
        encode zstd gzip

        reverse_proxy localhost:8080 {
               header_up X-Real-IP {remote_host}
               header_up X-Forwarded-For {remote_host}
               header_up X-Forwarded-Port {http.request.port}
               header_up X-Forwarded-Proto {http.request.scheme}

               header_up Access-Control-Allow-Origin "*"
               header_up Access-Control-Allow-Methods "GET, POST, OPTIONS"
               header_up Access-Control-Allow-Headers "*"
               header_up Access-Control-Expose-Headers "*"
               header_up User-Agent ""
        }
  }

  @api_requests path /*
  
  handle @api_requests {
      header Access-Control-Allow-Origin "*"
      header Access-Control-Allow-Methods "GET, POST, OPTIONS"
      header Access-Control-Allow-Headers "*"
      header Access-Control-Expose-Headers "*"

      reverse_proxy localhost:8080

```
Restart Caddy:
```bash
docker restart caddy
```

#### **Editing `.env` File (Environment Variables for SearXNG)**
##### **Windows (PowerShell)**
```powershell
cd searxng-docker\searxng
notepad .env
```
**Paste the updated `.env` content below:**
```ini
# By default listen on https://localhost
# To change this:
# * uncomment SEARXNG_HOSTNAME, and replace <host> by the SearXNG hostname
# * uncomment LETSENCRYPT_EMAIL, and replace <email> by your email (require to create a Let's Encrypt certificate)

# SEARXNG_HOSTNAME=<host>
# LETSENCRYPT_EMAIL=<email>

# Optional:
# If you run a very small or a very large instance, you might want to change the amount of used uwsgi workers and threads per worker
# More workers (= processes) means that more search requests can be handled at the same time, but it also causes more resource usage

# SEARXNG_UWSGI_WORKERS=4
# SEARXNG_UWSGI_THREADS=4
SEARXNG_RATE_LIMIT=0

```
Restart SearXNG:
```bash
docker restart searxng
```

---

## Usage

To start the voice assistant, run:

```bash
python voice_assistant.py
```

Press **ALT** to start/stop recording and **ESC** to exit.

---

## Code Structure and Customization

The assistant consists of multiple components:

- `voice_assistant.py`: Core script handling voice input/output.
- `conversation_history.json`: Stores user interactions.
- `va.bat`: (For Windows) to run the script in the background

### Customization Options

- **Whisper Model Size:** Change the model size in `audio_manager.py` (options: tiny, base, small, medium, large).
- **AI Model:** Change the default AI model in `config.py` (default: `llama3.1`).
- **Voice Commands:** Customize exit commands in `config.py`.
- **Audio Settings:** Modify sample rate, channels, and frame duration in `config.py`.
- **Voice Selection:** Customize TTS voices for different languages in `audio_manager.py`.
- **System Prompts:** Modify the assistant's behavior and responses in `config.py`.
- **Notification Settings:** Customize notification settings in `ui_manager.py`.

---

## Troubleshooting

If issues arise:

- Ensure all dependencies are installed correctly.
- Verify that Whisper, Ollama, and SearXNG services are running.
- Check for missing environment variables or configuration errors.

---

## License and Contributions

This project is open-source. Contributions, bug fixes, and feature suggestions are welcome! Feel free to submit pull requests or open issues.

---

For any questions refer to `Discord:` `hamzanasry`

---


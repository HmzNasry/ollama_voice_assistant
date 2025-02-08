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

---

### SearxNG Quick Setup (For Internet Searches)

#### Quick Setup (Using Docker)
To quickly set up SearxNG, run the following **Docker command** inside the same directory as the voice assistant Python script:
```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng
```

Once the container is running, access it using:
```bash
docker exec -it searxng /bin/sh
```

To copy and paste the **configuration files** into the container:

Windows (PowerShell)
```powershell
notepad C:\searxng\settings.yml  # Main settings
notepad C:\searxng\Caddyfile     # Reverse proxy settings
notepad C:\searxng\.env          # Environment settings
Windows (WSL - If Running SearxNG in a Linux Environment)
```
Windows (WSL - If Running SearxNG in a Linux Environment)
```
nano /etc/searxng/settings.yml  # Main settings
nano /etc/searxng/Caddyfile     # Reverse proxy settings
nano /etc/searxng/.env          # Environment settings
```
Linux / macOS (Terminal)
```
sudo nano /etc/searxng/settings.yml  # Main settings
sudo nano /etc/searxng/Caddyfile     # Reverse proxy settings
sudo nano /etc/searxng/.env          # Environment settings
If Running Inside a Docker Container (Linux/macOS/WSL)
```
```
docker exec -it searxng /bin/sh
nano /etc/searxng/settings.yml  # Main settings
nano /etc/searxng/Caddyfile     # Reverse proxy settings
nano /etc/searxng/.env          # Environment settings
```
**Copy and paste the following files into their respective locations**:

#### **Caddyfile**
```
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
  }

  debug
}

```

#### **.env File**
```
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

#### **settings.yaml**
```
# see https://docs.searxng.org/admin/settings/settings.html#settings-use-default-settings
use_default_settings: true

server:
  secret_key: "a8s7d98a7sd9a87sd98a7sd98a7sd"
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

After editing, restart the container:
```bash
docker restart searxng
```

---

Enjoy using the updated Ollama Voice Assistant, and feel free to provide feedback or contribute improvements as this version continues to evolve!


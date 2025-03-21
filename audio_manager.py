import os
import tempfile
import subprocess
import pyaudio
import wave
import whisper
import warnings
from typing import List, Optional, Tuple
import time

from config import SAMPLE_RATE, CHANNELS, FRAME_DURATION_MS
from ui_manager import UIManager

# Suppress unnecessary warnings
warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")
warnings.filterwarnings("ignore", message="Performing inference on CPU when CUDA is available")
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

class AudioManager:
    def __init__(self, ui_manager: UIManager):
        """Initialize audio recording and processing components."""
        self.ui_manager = ui_manager
        self.recording = False
        self.audio_frames: List[bytes] = []
        
        # CUSTOMIZE: Whisper model size - options: tiny, base, small, medium, large
        # Larger models are more accurate but use more memory and CPU
        print("[AUDIO] Loading Whisper model...")
        self.whisper_model = whisper.load_model("medium", device="cpu")
        print("[AUDIO] Whisper model loaded.")
        
        # Audio settings from config
        self.chunk_size = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
        self.audio = pyaudio.PyAudio()
        
        # Start recording stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.chunk_size
        )
    
    def start_recording(self) -> None:
        """Start audio recording."""
        if not self.recording:
            self.recording = True
            self.audio_frames = []
            print("[AUDIO] Recording started...")
            
    def stop_recording(self) -> None:
        """Stop audio recording."""
        if self.recording:
            self.recording = False
            print(f"[AUDIO] Recording stopped. Captured {len(self.audio_frames)} frames")
            
    def record_audio_frame(self) -> None:
        """Record a single audio frame if recording is active."""
        if self.recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.audio_frames.append(data)
            except Exception as e:
                print(f"[AUDIO] Error recording frame: {e}")
    
    def save_recording(self) -> Optional[str]:
        """Save recorded audio to a temporary WAV file."""
        if not self.audio_frames:
            return None
            
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()
        return temp_file.name
    
    def transcribe_audio(self, audio_file: str) -> Tuple[str, str]:
        """Transcribe audio file to text using Whisper."""
        try:
            result = self.whisper_model.transcribe(audio_file)
            transcription = result.get("text", "").strip()
            detected_lang = result.get("language", "en")
            print(f"[AUDIO] Transcribed text: {transcription}")
            return transcription, detected_lang
        except Exception as e:
            print(f"[AUDIO] Transcription error: {e}")
            return "", "en"
    
    def text_to_speech(self, text: str, lang: str = "en") -> None:
        """Convert text to speech and play it."""
        if not text or self.ui_manager.is_speaking:
            return
            
        try:
            # Create temp file for TTS output
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            self.ui_manager.current_tts_file = temp_file.name
            temp_file.close()
            
            # Determine voice based on language
            voice = self.get_voice_for_language(lang)
            
            # Use edge-tts for speech synthesis
            tts_process = subprocess.Popen(
                ["edge-tts", "--voice", voice, "--text", text, "--write-media", self.ui_manager.current_tts_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=self.ui_manager.startupinfo
            )
            tts_process.wait()
            
            # Play the generated audio
            self.ui_manager.is_speaking = True
            self.ui_manager.play_sound(self.ui_manager.current_tts_file)
            
        except Exception as e:
            print(f"[TTS] Error: {e}")
            self.ui_manager.is_speaking = False
    
    def get_voice_for_language(self, lang: str) -> str:
        """Get the appropriate voice for a language."""
        # CUSTOMIZE: Voice selection for different languages
        voice_map = {
            "en": "en-US-AndrewNeural",  # English
            "ar": "ar-EG-SalmaNeural",   # Arabic
            "es": "es-ES-ElviraNeural",  # Spanish
            "fr": "fr-FR-DeniseNeural",  # French
            "de": "de-DE-KatjaNeural",   # German
            "zh": "zh-CN-XiaoxiaoNeural", # Chinese
            "ja": "ja-JP-NanamiNeural",  # Japanese
            "ru": "ru-RU-SvetlanaNeural" # Russian
        }
        return voice_map.get(lang, "en-US-AndrewNeural")
        
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
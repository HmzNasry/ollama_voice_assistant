import os
import asyncio
import tempfile
import keyboard
import numpy as np
import soundfile as sf
import warnings
import time

from ui_manager import UIManager
from audio_manager import AudioManager
from llm_interface import LLMInterface
from conversation_manager import ConversationManager
from config import EXIT_COMMANDS

# Suppress Whisper model warnings
warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")
warnings.filterwarnings("ignore", message="Performing inference on CPU when CUDA is available")
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

class VoiceAssistant:
    def __init__(self):
        """Initialize the voice assistant components."""
        print("[INIT] Initializing Voice Assistant components...")
        self.ui_manager = UIManager()
        self.conversation_manager = ConversationManager()
        self.audio_manager = AudioManager(self.ui_manager)
        self.llm_interface = LLMInterface(self.conversation_manager)
        
        self.shutting_down = False
        
        self.ui_manager.send_notification(
            "Voice Assistant", 
            "Voice assistant is ready. Press alt to start/stop recording or stop speech."
        )
        print("[INIT] Voice Assistant ready, press alt to start/stop recording or to stop speech.")
        
    def toggle_recording(self):
        """Toggle recording or stop speech if speaking."""
        if self.ui_manager.is_speaking and self.ui_manager.tts_process is not None:
            self.ui_manager.stop_speech()
            return
        
        if not self.audio_manager.recording:
            self.start_new_recording()
        else:
            self.process_recording()
            
    def start_new_recording(self):
        """Start a new audio recording session."""
        self.audio_manager.start_recording()
        self.ui_manager.play_sound("confirmation.mp3")
        
    def process_recording(self):
        """Process recorded audio and get AI response."""
        self.audio_manager.stop_recording()
        self.ui_manager.play_sound("confirmation.mp3")
        
        audio_file = self.audio_manager.save_recording()
        if not audio_file:
            print("[ERROR] No audio recorded")
            return
            
        user_text, detected_lang = self.audio_manager.transcribe_audio(audio_file)
        os.remove(audio_file)
            
        print(f"[You]: {user_text}")
        
        # Check for exit commands
        if user_text.lower() in EXIT_COMMANDS:
            print("[Assistant]: Goodbye!")
            asyncio.run(self.audio_manager.text_to_speech("Goodbye!", "en"))
            self.shutdown()
            return
            
        self.process_query(user_text)
        
    async def process_query_async(self, query):
        """Get LLM response and speak it."""
        response = await self.llm_interface.ask_llm(query)
        print(f"[Assistant]: {response}")
        
        self.llm_interface.update_conversation(query, response)
        
        # Detect response language for TTS
        try:
            from langdetect import detect
            lang_code = detect(response)
            lang_code = "en" if lang_code == "en" else lang_code
        except Exception as e:
            print(f"[Language Detection] Error: {e}")
            lang_code = "en"
            
        self.ui_manager.send_notification("Voice Assistant", response)
        self.audio_manager.text_to_speech(response, lang_code)
        
    def process_query(self, query):
        """Process user query synchronously."""
        asyncio.run(self.process_query_async(query))
        
    def shutdown(self):
        """Clean up resources and exit."""
        self.shutting_down = True
        self.ui_manager.send_notification("Shutting Down", "Goodbye!")
        self.ui_manager.play_sound("close.wav")
        self.audio_manager.cleanup()
        os._exit(0)
        
    def run(self):
        """Run the voice assistant main loop."""
        # Set hotkey - customize this if you prefer a different activation key
        keyboard.add_hotkey('alt', self.toggle_recording)
        
        print("[INIT] Running... (Press ESC to exit)")
        try:
            while not self.shutting_down:
                self.audio_manager.record_audio_frame()
                time.sleep(0.01)  # Prevent CPU overload
        except KeyboardInterrupt:
            print("\n[KEYBOARD] Interrupted by user")
            self.shutdown()
        
if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
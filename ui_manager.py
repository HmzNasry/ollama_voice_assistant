import subprocess
import os
import time
from typing import Optional
from plyer import notification

class UIManager:
    def __init__(self):
        """Initialize UI components for notifications and audio playback."""
        # Hide console windows for subprocess calls on Windows
        self.startupinfo = subprocess.STARTUPINFO()
        self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.startupinfo.wShowWindow = 0
        
        self.tts_process: Optional[subprocess.Popen] = None
        self.is_speaking: bool = False
        self.tts_stop_requested: bool = False
        self.current_tts_file: Optional[str] = None

    def play_sound(self, sound_file: str) -> None:
        """Play an audio file using ffplay."""
        try:
            self.tts_process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", sound_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=self.startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP 
            )
        except Exception as e:
            print(f"[UI] Error playing sound: {e}")

    def stop_speech(self) -> None:
        """Stop currently playing speech and clean up resources."""
        # Track if we were actually speaking (for logging)
        was_speaking = self.is_speaking and self.tts_process is not None
        
        if self.is_speaking and self.tts_process:
            try:
                # First terminate the process if it's still running
                if self.tts_process.poll() is None:
                    self.tts_process.terminate()
                    # Wait briefly for process to terminate
                    for _ in range(5):
                        if self.tts_process.poll() is not None:
                            break
                        time.sleep(0.1)
                    
                    # Force kill if still running
                    if self.tts_process.poll() is None:
                        self.tts_process.kill()
                        time.sleep(0.2)
                
                # Try to delete the temp file
                if self.current_tts_file and os.path.exists(self.current_tts_file):
                    try:
                        os.remove(self.current_tts_file)
                        if was_speaking:
                            print("[TTS] Temp file deleted.")
                    except Exception as e:
                        print(f"[TTS] Error deleting temp file: {e}")
                        # Schedule file for deletion on exit
                        try:
                            os.rename(self.current_tts_file, self.current_tts_file + ".delete")
                        except:
                            pass
            except Exception as e:
                print(f"[TTS] Error stopping speech: {e}")
                
            # Always reset state
            self.is_speaking = False
            self.tts_process = None
            self.current_tts_file = None
            
            if was_speaking:
                print("[TTS] Speech stopped.")
        else:
            # Reset state if out of sync
            self.is_speaking = False
            self.tts_process = None
            self.current_tts_file = None

    def send_notification(self, title: str, message: str) -> None:
        """Show a desktop notification with the assistant's response."""
        try:
            # CUSTOMIZE: Notification settings
            # Limit message length to avoid notification issues
            truncated = message[:100] + "..." if len(message) > 100 else message
            
            notification.notify(
                title=title, 
                message=truncated, 
                app_name="Voice Assistant", 
                timeout=1
            )
        except Exception as e:
            print(f"[UI] Notification error: {e}")
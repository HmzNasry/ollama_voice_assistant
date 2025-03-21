import os
import json
from typing import Dict, List, Any

from config import HISTORY_FILE

class ConversationManager:
    def __init__(self):
        """Initialize conversation history manager."""
        self.history_file = HISTORY_FILE
        self.history = self.load_conversation_history()
    
    def reset_conversation_history(self) -> Dict[str, List[str]]:
        """Reset conversation history file and return empty history."""
        default_data = {"user": [], "assistant": []}
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data

    def load_conversation_history(self) -> Dict[str, List[str]]:
        """Load conversation history from file or create new if not exists."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        raise ValueError("Invalid JSON format in history file.")
                    for key in ["user", "assistant"]:
                        if key not in data:
                            data[key] = []
                    return data
            except (json.JSONDecodeError, ValueError):
                print("[HISTORY] Corrupted file. Resetting history.")
                return self.reset_conversation_history()
            except Exception as e:
                print(f"[HISTORY] Error loading history: {e}")
                return self.reset_conversation_history()
        return self.reset_conversation_history()

    def save_conversation_history(self) -> None:
        """Save current conversation history to file."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"[HISTORY] Error saving history: {e}")

    def update_conversation(self, user_input: str, assistant_response: str) -> None:
        """Add new conversation turn and maintain history size."""
        self.history["user"].append(user_input)
        self.history["assistant"].append(assistant_response)
        
        # CUSTOMIZE: Maximum number of conversation turns to store
        # Reduce this number if you want to limit memory usage
        max_history_size = 50
        
        if len(self.history["user"]) > max_history_size:
            self.history["user"].pop(0)
            self.history["assistant"].pop(0)
        self.save_conversation_history()
        
    def get_recent_history(self, max_turns: int = 15) -> Dict[str, List[str]]:
        """Get the most recent conversation history for context."""
        # CUSTOMIZE: Number of recent turns to include in LLM context
        # Lower values save tokens, higher values give more conversation context
        return {
            "user": self.history["user"][-max_turns:],
            "assistant": self.history["assistant"][-max_turns:]
        }
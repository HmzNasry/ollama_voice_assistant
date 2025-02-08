#!/bin/bash
cd "<INSERT PATH TO VOICE_ASSISTANT.PY HERE>" || exit
nohup python3 voice_assistant.py >/dev/null 2>&1 &

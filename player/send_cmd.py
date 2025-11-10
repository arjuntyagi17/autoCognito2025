from __future__ import annotations

import os
import sys
import json
import time
from pathlib import Path

DEFAULT_CMD_FILE = Path(__file__).with_name("command_queue.json")
CMD_FILE = Path(os.getenv("BOT_CMD_FILE", str(DEFAULT_CMD_FILE)))

ALIASES = {
    "space": " ",
}

VALID_KEYS = {"w", "a", "s", "d", " "}


def send_command(key: str) -> bool:
    """Add a command to the queue file."""
    if key not in VALID_KEYS and key not in ALIASES:
        return False
    
    actual_key = ALIASES.get(key, key)
    try:
        if CMD_FILE.exists():
            with open(CMD_FILE, 'r') as f:
                queue = json.load(f)
                if not isinstance(queue, list):
                    queue = []
        else:
            queue = []
    except:
        queue = []
    
    queue.append({
        "key": actual_key,
        "timestamp": time.time()
    })
    try:
        with open(CMD_FILE, 'w') as f:
            json.dump(queue, f)
    except Exception as e:
        return False
    
    return True
import threading
import time
from config import SESSION_TIMEOUT
from docker_manager import docker_manager

sessions = {}  # { session_id: { "container": "vbrowser-test", "last_seen": timestamp } }

def update_heartbeat(session_id):
    if session_id in sessions:
        sessions[session_id]["last_seen"] = time.time()

def cleanup_loop():
    while True:
        time.sleep(60)
        now = time.time()
        for session_id, data in list(sessions.items()):
            if now - data["last_seen"] > SESSION_TIMEOUT:
                docker_manager.stop_container(data["container"])  # ← so aufrufen
                del sessions[session_id]

def register_session(session_id: str, container_name: str, token: str):
    sessions[session_id] = {
        "container": container_name,
        "last_seen": time.time(),
        "token": token
    }

def validate_token(token: str) -> bool:
    for data in sessions.values():
        if data.get("token") == token:
            return True
    return False


# Beim App-Start aufrufen
threading.Thread(target=cleanup_loop, daemon=True).start()

import threading
import time
import logging
from config import SESSION_TIMEOUT
from docker_manager import docker_manager

logger = logging.getLogger("vbrowser")

sessions = {}  # { session_id: { "container": "vbrowser-test", "last_seen": timestamp, "token": token } }


def update_heartbeat(session_id):
    if session_id in sessions:
        sessions[session_id]["last_seen"] = time.time()


def cleanup_loop():
    while True:
        time.sleep(60)
        now = time.time()
        for session_id, data in list(sessions.items()):
            if now - data["last_seen"] > SESSION_TIMEOUT:
                logger.info(f"Session timeout: stopping container for {session_id}")
                docker_manager.stop_container(data["container"])
                del sessions[session_id]


def cleanup_orphaned_containers():
    """Beim Start: alle vbrowser-user Container stoppen die vom letzten Run übrig sind"""
    try:
        containers = docker_manager.client.containers.list()
        for c in containers:
            if c.name.startswith("vbrowser-") and c.name not in ("vbrowser-backend", "vbrowser-traefik"):
                c.remove(force=True)
                logger.info(f"Startup cleanup: removed orphan {c.name}")
    except Exception as e:
        logger.warning(f"Startup cleanup failed: {e}")


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


# Beim App-Start: verwaiste Container aufräumen, dann Cleanup-Loop starten
cleanup_orphaned_containers()
threading.Thread(target=cleanup_loop, daemon=True).start()

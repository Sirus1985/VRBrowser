import threading
import time
import logging
from config import SESSION_TIMEOUT
from database import (
    db_list_sessions, db_create_session, db_update_heartbeat,
    db_delete_session, db_get_session_by_token, db_get_timed_out_sessions
)
from docker_manager import docker_manager

logger = logging.getLogger("vbrowser")


def update_heartbeat(session_id: str):
    db_update_heartbeat(session_id)


def register_session(session_id: str, user_id: int, username: str, container_name: str, token: str, container_ip: str = None): 
    db_create_session(session_id, user_id, username, container_name, token, container_ip)  

def validate_token(token: str) -> bool:
    return db_get_session_by_token(token) is not None


def cleanup_loop():
    while True:
        time.sleep(60)
        for session in db_get_timed_out_sessions(SESSION_TIMEOUT):
            logger.info(f"Session timeout: stopping container for {session['username']} ({session['session_id']})")
            docker_manager.stop_container(session["container_name"])
            db_delete_session(session["session_id"])


def cleanup_orphaned_containers():
    """Beim Start: Container stoppen die in DB fehlen"""
    try:
        active = {s["container_name"] for s in db_list_sessions()}
        containers = docker_manager.client.containers.list()
        for c in containers:
            if c.name.startswith("vbrowser-") and c.name not in ("vbrowser-backend", "vbrowser-traefik"):
                if c.name not in active:
                    c.remove(force=True)
                    logger.info(f"Startup cleanup: removed orphan {c.name}")
    except Exception as e:
        logger.warning(f"Startup cleanup failed: {e}")


cleanup_orphaned_containers()
threading.Thread(target=cleanup_loop, daemon=True).start()

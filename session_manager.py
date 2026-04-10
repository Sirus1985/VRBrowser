import time
import logging
from config import SESSION_TIMEOUT, MAX_SESSION_DURATION
from database import (
    db_get_timed_out_sessions,
    db_list_sessions,
    db_delete_session,
    db_create_session,
    db_update_heartbeat,
    db_get_session_by_token,
    db_get_session_by_id,
)
from docker_manager import docker_manager

logger = logging.getLogger(__name__)

SYSTEM_CONTAINERS = {"vbrowser-backend", "vbrowser-traefik"}
SYSTEM_PREFIXES   = ("vbrowser-db",)


def register_session(session_id: str, user_id: int, username: str, container_name: str, token: str, container_ip: str = None, image: str = None):
    db_create_session(session_id, user_id, username, container_name, token, container_ip, image)

def update_heartbeat(session_id: str):
    db_update_heartbeat(session_id)

def validate_token(token: str) -> bool:
    return db_get_session_by_token(token) is not None


def cleanup_orphaned_containers():
    try:
        active = {s["container_name"] for s in db_list_sessions()}
        for c in docker_manager.list_vbrowser_containers():
            is_system = c.name in SYSTEM_CONTAINERS or any(
                c.name.startswith(p) for p in SYSTEM_PREFIXES
            )
            if c.name.startswith("vbrowser-") and not is_system:
                if c.name not in active:
                    docker_manager.stop_container(c.name)
                    logger.info("Startup cleanup: removed orphan %s", c.name)
    except Exception as e:
        logger.warning("Startup cleanup failed: %s", e)


def cleanup_loop():
    logger.info("Cleanup-Loop gestartet (Timeout=%ss, MaxDuration=%ss)", SESSION_TIMEOUT, MAX_SESSION_DURATION)
    while True:
        try:
            # 1. Inaktive Sessions
            timed_out = db_get_timed_out_sessions(SESSION_TIMEOUT)
            for session in timed_out:
                logger.info(f"Session Timeout: {session['username']} ({session['session_id']})")
                try:
                    docker_manager.stop_container(session["container_name"])
                except Exception as e:
                    logger.error(f"Fehler beim Stoppen von {session['container_name']}: {e}")
                db_delete_session(session["session_id"])

            # 2. Hard Limit (Max Duration)
            if MAX_SESSION_DURATION > 0:
                all_sessions = db_list_sessions()
                now = time.time()
                for s in all_sessions:
                    if now - s["created_at"] > MAX_SESSION_DURATION:
                        logger.info(f"Max Duration erreicht: {s['username']} ({s['session_id']})")
                        try:
                            docker_manager.stop_container(s["container_name"])
                        except Exception as e:
                            logger.error(f"Fehler beim Stoppen: {e}")
                        db_delete_session(s["session_id"])

            # 3. Verwaiste Docker-Container aufräumen
            all_sessions = db_list_sessions()
            valid_containers = {s["container_name"] for s in all_sessions}

            try:
                for c in docker_manager.list_vbrowser_containers():
                    is_system = c.name in SYSTEM_CONTAINERS or any(
                        c.name.startswith(p) for p in SYSTEM_PREFIXES
                    )
                    if c.name.startswith("vbrowser-") and not is_system:
                        if c.name not in valid_containers:
                            logger.info(f"Verwaisten Container gefunden: {c.name}. Stoppe ihn...")
                            try:
                                docker_manager.stop_container(c.name)
                            except Exception as e:
                                logger.error(f"Konnte verwaisten Container {c.name} nicht stoppen: {e}")
            except Exception as e:
                logger.error(f"Fehler beim Überprüfen laufender Container: {e}")

        except Exception as e:
            logger.error(f"Fehler im Cleanup-Loop: {e}")

        time.sleep(60)

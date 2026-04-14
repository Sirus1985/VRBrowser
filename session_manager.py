import time
import logging
from config import SESSION_TIMEOUT, MAX_SESSION_DURATION
from database import (
    db_list_sessions,
    db_delete_session,
    db_create_session,
    db_update_heartbeat,
    db_get_session_by_token,
    db_get_session_by_id,
    db_get_container_def_timeouts,
)
from docker_manager import docker_manager

logger = logging.getLogger(__name__)

SYSTEM_CONTAINERS = {"vbrowser-backend", "vbrowser-traefik"}
SYSTEM_PREFIXES   = ("vbrowser-db",)


def register_session(session_id: str, user_id: int, username: str, container_name: str,
                     token: str, container_ip: str = None, image: str = None,
                     container_def_id: int = None):
    db_create_session(session_id, user_id, username, container_name, token,
                      container_ip, image, container_def_id)

def update_heartbeat(session_id: str):
    db_update_heartbeat(session_id)

def validate_token(token: str) -> bool:
    return db_get_session_by_token(token) is not None


def _effective_timeout(session: dict) -> int:
    """Gibt den effektiven session_timeout fuer eine Session zurueck.
    Nutzt container_def-Override wenn gesetzt, sonst globalen Default.
    """
    def_id = session.get("container_def_id")
    if def_id:
        overrides = db_get_container_def_timeouts(def_id)
        if overrides["session_timeout"] is not None:
            return int(overrides["session_timeout"])
    return SESSION_TIMEOUT


def _effective_max_duration(session: dict) -> int:
    """Gibt die effektive max_session_duration fuer eine Session zurueck.
    0 bedeutet deaktiviert.
    """
    def_id = session.get("container_def_id")
    if def_id:
        overrides = db_get_container_def_timeouts(def_id)
        if overrides["max_session_duration"] is not None:
            return int(overrides["max_session_duration"])
    return MAX_SESSION_DURATION


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


def _calc_sleep_interval(sessions: list) -> int:
    """Berechnet das optimale Sleep-Intervall des Cleanup-Loops.
    Basiert auf 1/3 des kleinsten aktiven Session-Timeouts.
    Minimum: 10s, Maximum: 60s.
    """
    if not sessions:
        return 30
    try:
        min_timeout = min(_effective_timeout(s) for s in sessions)
        return max(10, min(60, min_timeout // 3))
    except Exception:
        return 30


def cleanup_loop():
    logger.info("Cleanup-Loop gestartet (Timeout=%ss, MaxDuration=%ss)", SESSION_TIMEOUT, MAX_SESSION_DURATION)
    while True:
        try:
            all_sessions = db_list_sessions()
            now = time.time()

            for session in all_sessions:
                session_id = session["session_id"]

                # Timestamps aus ISO-String zurueck in float konvertieren
                try:
                    import datetime
                    last_seen_raw = session.get("last_seen")
                    created_at_raw = session.get("created_at")
                    last_seen = datetime.datetime.fromisoformat(last_seen_raw.replace("Z", "+00:00")).timestamp() if isinstance(last_seen_raw, str) else float(last_seen_raw)
                    created_at = datetime.datetime.fromisoformat(created_at_raw.replace("Z", "+00:00")).timestamp() if isinstance(created_at_raw, str) else float(created_at_raw)
                except Exception as e:
                    logger.warning("Zeitstempel-Parsing fehlgeschlagen fuer %s: %s", session_id, e)
                    continue

                # 1. Inaktivitaets-Timeout (per Container-Def oder global)
                timeout = _effective_timeout(session)
                if now - last_seen > timeout:
                    logger.info("Session Timeout (%ss): %s (%s)", timeout, session['username'], session_id)
                    try:
                        docker_manager.stop_container(session["container_name"])
                    except Exception as e:
                        logger.error("Fehler beim Stoppen von %s: %s", session["container_name"], e)
                    db_delete_session(session_id)
                    continue

                # 2. Hard Limit (per Container-Def oder global)
                max_dur = _effective_max_duration(session)
                if max_dur > 0 and now - created_at > max_dur:
                    logger.info("Max Duration erreicht (%ss): %s (%s)", max_dur, session['username'], session_id)
                    try:
                        docker_manager.stop_container(session["container_name"])
                    except Exception as e:
                        logger.error("Fehler beim Stoppen: %s", e)
                    db_delete_session(session_id)

            # 3. Verwaiste Docker-Container aufraumen
            valid_containers = {s["container_name"] for s in db_list_sessions()}
            try:
                for c in docker_manager.list_vbrowser_containers():
                    is_system = c.name in SYSTEM_CONTAINERS or any(
                        c.name.startswith(p) for p in SYSTEM_PREFIXES
                    )
                    if c.name.startswith("vbrowser-") and not is_system:
                        if c.name not in valid_containers:
                            logger.info("Verwaisten Container gefunden: %s. Stoppe ihn...", c.name)
                            try:
                                docker_manager.stop_container(c.name)
                            except Exception as e:
                                logger.error("Konnte verwaisten Container %s nicht stoppen: %s", c.name, e)
            except Exception as e:
                logger.error("Fehler beim Ueberpruefen laufender Container: %s", e)

        except Exception as e:
            logger.error("Fehler im Cleanup-Loop: %s", e)

        # Dynamischer Sleep: 1/3 des kleinsten Session-Timeouts (min 10s, max 60s)
        try:
            current_sessions = db_list_sessions()
            sleep_interval = _calc_sleep_interval(current_sessions)
        except Exception:
            sleep_interval = 30
        logger.debug("Cleanup-Loop schlaeft %ss", sleep_interval)
        time.sleep(sleep_interval)

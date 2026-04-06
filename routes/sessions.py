import logging
import secrets
import uuid
import traceback

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from datetime import datetime, timezone

from auth import get_current_user, require_admin
from docker_manager import create_container, stop_container, container_exists, get_container_ip
from config import BASE_DOMAIN, USE_TLS
from session_manager import register_session, update_heartbeat, validate_token
from database import (
    db_get_session_by_user,
    db_delete_session,
    db_update_user_settings,
    db_get_user_settings,
    db_list_sessions,
    db_get_container_def,
    db_get_default_container_def,
)







router = APIRouter(tags=["sessions"])
logger = logging.getLogger(__name__)


@router.post("/api/session/start")
async def start_session(request: Request, user: dict = Depends(get_current_user)):
    user_id = user["uid"]
    username = user["sub"]

    existing = db_get_session_by_user(user_id)
    if existing:
        # Prüfen, ob der Container wirklich noch in Docker existiert
        if container_exists(existing["container_name"]):
            token = existing["token"]
            session_id = existing["session_id"]
            url = f"https://{session_id[:8]}.{BASE_DOMAIN}/" if BASE_DOMAIN else f"http://{session_id[:8]}.localhost/"
            response = JSONResponse({
                "status": "resumed", "url": url, "session_id": session_id, "token": token
            })
            response.set_cookie(
                key="vbrowser_token", value=token,
                domain=f".{BASE_DOMAIN}" if BASE_DOMAIN else None,
                httponly=True, samesite="none", secure=USE_TLS, max_age=86400
            )
            return response
        else:
            # Geister-Session aus der DB löschen, da der Container tot ist
            db_delete_session(existing["session_id"])

    body = {}
    try: 
        body = await request.json()
    except Exception: 
        pass

    try:
        container_def_id = body.get("container_def_id")
        if container_def_id:
            container_def = db_get_container_def(int(container_def_id)) 
        else:
            container_def = db_get_default_container_def()

        if not container_def:
            return JSONResponse({"detail": "Keine Container-Definition vorhanden."}, status_code=500)

        session_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)

        # HIER fangen wir den Fehler ab:
        container = create_container(username, session_id, token, container_def)
        container_ip = get_container_ip(container)

        register_session(session_id, user_id, username, container.name, token, container_ip)

        url = f"https://{session_id[:8]}.{BASE_DOMAIN}/" if BASE_DOMAIN else f"http://{session_id[:8]}.localhost/"
        response = JSONResponse({
            "status": "started", "url": url, "session_id": session_id, "token": token
        })
        response.set_cookie(
            key="vbrowser_token", value=token,
            domain=f".{BASE_DOMAIN}" if BASE_DOMAIN else None,
            httponly=True, samesite="none", secure=USE_TLS, max_age=86400
        )
        return response

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Fehler beim Starten der Session: {error_trace}")
        return PlainTextResponse(f"Crash in start_session: {str(e)}\n\n{error_trace}", status_code=500)



@router.post("/api/session/stop")
@router.delete("/api/session/{session_id}")
def api_stop_session(session_id: str = None, user: dict = Depends(get_current_user)):
    session = db_get_session_by_user(user["uid"])
    if session:
        stop_container(session["container_name"])
        db_delete_session(session["session_id"])
    return {"ok": True}



@router.get("/api/session/status")
def session_status(user: dict = Depends(get_current_user)):
    session = db_get_session_by_user(user["uid"])
    if not session: 
        return {"active": False}
    return {
        "active": container_exists(session["container_name"]),
        "session_id": session["session_id"],
        "container_name": session["container_name"],
    }



@router.post("/api/session/reset")
def reset_session(user: dict = Depends(get_current_user)):
    session = db_get_session_by_user(user["uid"])
    if session:
        stop_container(session["container_name"])
        db_delete_session(session["session_id"])
    return {"ok": True}



def _ts_to_iso(ts):
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        return None


@router.get("/api/sessions")
@router.get("/api/session/list")
def list_sessions(user: dict = Depends(get_current_user)):
    if user.get("isadmin") or user.get("admin"):
        sessions = db_list_sessions()
    else:
        sessions = db_list_sessions(user["uid"])

    for s in sessions:
        s["created_at"] = _ts_to_iso(s.get("created_at"))
        s["last_seen"] = _ts_to_iso(s.get("last_seen"))

    return sessions



@router.post("/heartbeat/{session_id}")
@router.post("/api/session/{session_id}/heartbeat")
def heartbeat(session_id: str, request: Request):
    token = request.cookies.get("vbrowser_token")
    if not token or not validate_token(token):
        return Response(status_code=401)
    update_heartbeat(session_id)
    return Response(status_code=204)



@router.get("/auth/verify")
def auth_verify(request: Request):
    token = request.cookies.get("vbrowser_token")
    if not token or not validate_token(token):
        return Response(status_code=401)
    return Response(status_code=200)



@router.get("/auth/set-cookie")
def set_cookie_redirect(token: str, redirect: str):
    if not validate_token(token):
        return Response(status_code=401)
    response = Response(status_code=302, headers={"Location": redirect})
    response.set_cookie(
        key="vbrowser_token", value=token,
        httponly=True, samesite="none", secure=True, max_age=86400
    )
    return response
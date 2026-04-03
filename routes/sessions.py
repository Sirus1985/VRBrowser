import secrets
import uuid
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from auth import get_current_user, require_admin
# KORREKT: Nur die verfügbaren Funktionen importieren!
from docker_manager import create_container, stop_container, container_exists
from config import BASE_DOMAIN, PROXY_NETWORK, USE_TLS
from session_manager import register_session
from database import (
    db_get_session_by_user,
    db_delete_session,
    db_update_user_settings,
    db_get_user_settings,
    db_list_sessions
)

router = APIRouter(tags=["sessions"])

@router.post("/api/session/start")
def start_session(user: dict = Depends(get_current_user)):
    user_id = user["uid"]
    username = user["sub"]

    existing = db_get_session_by_user(user_id)
    if existing:
        token = existing["token"]
        host_id = existing["container_name"].replace("vbrowser-", "")
        url = f"https://{host_id}.{BASE_DOMAIN}/" if BASE_DOMAIN else f"http://{host_id}.localhost/"
        response = JSONResponse({
            "status": "resumed",
            "url": url,
            "session_id": existing["session_id"],
            "token": token
        })
        response.set_cookie(
            key="vbrowser_token", value=token,
            domain=f".{BASE_DOMAIN}" if BASE_DOMAIN else None, httponly=True,
            samesite="none", secure=True, max_age=86400
        )
        return response

    session_id = str(uuid.uuid4())
    container_name = f"vbrowser-{session_id[:8]}"
    host_id = session_id[:8]
    token = secrets.token_urlsafe(32)

    # Korrekter Aufruf gemäß multidocker Branch
    url, container_ip = create_container(user_id, username, container_name, host_id)

    register_session(session_id, user_id, username, container_name, token, container_ip)

    response = JSONResponse({
        "status": "started",
        "url": url,
        "session_id": session_id,
        "token": token
    })
    response.set_cookie(
        key="vbrowser_token", value=token,
        domain=f".{BASE_DOMAIN}" if BASE_DOMAIN else None, httponly=True,
        samesite="none", secure=True, max_age=86400
    )
    return response


@router.post("/api/session/stop")
def api_stop_session(user: dict = Depends(get_current_user)):
    session = db_get_session_by_user(user["uid"])
    if session:
        stop_container(session["container_name"])
        db_delete_session(session["session_id"])
    response = JSONResponse({"status": "stopped"})
    response.delete_cookie("vbrowser_token", domain=f".{BASE_DOMAIN}" if BASE_DOMAIN else None)
    return response


@router.get("/api/session/status")
def session_status(user: dict = Depends(get_current_user)):
    session = db_get_session_by_user(user["uid"])
    if not session:
        return {"running": False}
    try:
        running = container_exists(session["container_name"])
        return {"running": running}
    except Exception:
        return {"running": False}


@router.post("/api/session/reset")
def reset_session(user: dict = Depends(get_current_user)):
    username = user["sub"]
    user_id = user["uid"]
    session = db_get_session_by_user(user_id)
    if session:
        stop_container(session["container_name"])
        db_delete_session(session["session_id"])
    # reset_profile wurde aus dem multidocker branch entfernt
    response = JSONResponse({"status": "reset"})
    response.delete_cookie("vbrowser_token", domain=f".{BASE_DOMAIN}" if BASE_DOMAIN else None)
    return response


@router.get("/api/user/settings")
def get_settings(user: dict = Depends(get_current_user)):
    return db_get_user_settings(user["uid"])


@router.patch("/api/user/settings")
def update_settings(body: dict, user: dict = Depends(get_current_user)):
    auto_start = bool(body.get("auto_start_session", False))
    db_update_user_settings(user["uid"], auto_start)
    return {"status": "ok", "auto_start_session": auto_start}


@router.get("/api/sessions")
def api_list_sessions(user: dict = Depends(require_admin)):
    return db_list_sessions()
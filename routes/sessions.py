import logging
import secrets
import uuid

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

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


@router.post("/api/session/start")
async def start_session(request: Request, user: dict = Depends(get_current_user)):
    user_id = user["uid"]
    username = user["sub"]

    existing = db_get_session_by_user(user_id)
    if existing:
        token = existing["token"]
        session_id = existing["session_id"]
        if BASE_DOMAIN:
            url = f"https://{session_id[:8]}.{BASE_DOMAIN}/"
        else:
            url = f"http://{session_id[:8]}.localhost/"

        response = JSONResponse({
            "status": "resumed",
            "url": url,
            "session_id": session_id,
            "token": token
        })
        response.set_cookie(
            key="vbrowser_token",
            value=token,
            domain=f".{BASE_DOMAIN}" if BASE_DOMAIN else None,
            httponly=True,
            samesite="none",
            secure=USE_TLS,
            max_age=86400
        )
        return response

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    container_def_id = body.get("container_def_id")
    container_def = None

    if container_def_id:
        container_def = db_get_container_def(int(container_def_id))

    if not container_def:
        container_def = db_get_default_container_def()

    if not container_def:
        return JSONResponse({"detail": "Keine Container-Definition vorhanden."}, status_code=500)

    session_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)

    container = create_container(username, session_id, token, container_def)
    container_ip = get_container_ip(container)

    register_session(
        session_id,
        user_id,
        username,
        container.name,
        token,
        container_ip
    )

    if BASE_DOMAIN:
        url = f"https://{session_id[:8]}.{BASE_DOMAIN}/"
    else:
        url = f"http://{session_id[:8]}.localhost/"

    response = JSONResponse({
        "status": "started",
        "url": url,
        "session_id": session_id,
        "token": token
    })
    response.set_cookie(
        key="vbrowser_token",
        value=token,
        domain=f".{BASE_DOMAIN}" if BASE_DOMAIN else None,
        httponly=True,
        samesite="none",
        secure=USE_TLS,
        max_age=86400
    )
    return response


@router.post("/api/session/stop")
def api_stop_session(user: dict = Depends(get_current_user)):
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

    running = container_exists(session["container_name"])
    return {
        "active": running,
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


@router.get("/api/user/settings")
def get_user_settings(user: dict = Depends(get_current_user)):
    return db_get_user_settings(user["uid"])


@router.patch("/api/user/settings")
def patch_user_settings(payload: dict, user: dict = Depends(get_current_user)):
    auto_start = bool(payload.get("auto_start_session", False))
    db_update_user_settings(user["uid"], auto_start)
    return {"ok": True, "auto_start_session": auto_start}


@router.get("/api/sessions")
@router.get("/api/session/list")
def list_sessions(user: dict = Depends(get_current_user)):
    if user.get("isadmin"):
        return db_list_sessions()
    return db_list_sessions(user["uid"])


@router.get("/api/session/settings")
def get_session_settings(user: dict = Depends(get_current_user)):
    return db_get_user_settings(user["uid"])


@router.post("/api/session/settings")
def set_session_settings(payload: dict, user: dict = Depends(get_current_user)):
    auto_start = bool(payload.get("auto_start_session", False))
    db_update_user_settings(user["uid"], auto_start)
    return {"ok": True, "auto_start_session": auto_start}


@router.get("/api/admin/sessions")
def admin_list_sessions(user: dict = Depends(require_admin)):
    return db_list_sessions()


@router.post("/heartbeat/{session_id}")
def heartbeat(session_id: str, request: Request):
    token = request.cookies.get("vbrowser_token")
    if not token or not validate_token(token):
        return Response(status_code=401)
    update_heartbeat(session_id)
    return Response(status_code=204)


@router.get("/auth/verify")
def auth_verify(request: Request):
    logger = logging.getLogger("vbrowser")
    token = request.cookies.get("vbrowser_token")
    if not token or not validate_token(token):
        return Response(status_code=401)

    path = request.headers.get("x-forwarded-uri", "")
    if path.startswith("/websockify"):
        return Response(status_code=200)

    referer = request.headers.get("referer", "")
    if "/vnc.html" in path:
        return Response(status_code=200)
    if referer and (referer.endswith("/vnc.html") or "/vnc.html?" in referer):
        return Response(status_code=200)
    return Response(status_code=200)


@router.get("/auth/set-cookie")
def set_cookie_redirect(token: str, redirect: str):
    if not validate_token(token):
        return Response(status_code=401)
    response = Response(status_code=302, headers={"Location": redirect})
    response.set_cookie(
        key="vbrowser_token",
        value=token,
        httponly=True,
        samesite="none",
        secure=True,
        max_age=86400
    )
    return response
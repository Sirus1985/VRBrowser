import secrets
import uuid
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from auth import get_current_user, require_admin
from docker_manager import docker_manager
from config import BASE_DOMAIN, PROXY_NETWORK, USE_TLS
from session_manager import update_heartbeat, register_session, validate_token
from database import db_get_session_by_user, db_delete_session, db_list_sessions

router = APIRouter(tags=["sessions"])


@router.post("/api/session/start")
def start_session(user: dict = Depends(get_current_user)):
    user_id  = user["uid"]
    username = user["sub"]

    existing = db_get_session_by_user(user_id)
    if existing:
        token   = existing["token"]
        host_id = existing["container_name"].replace("vbrowser-", "")
        url     = f"{'https' if USE_TLS else 'http'}://{host_id}.{BASE_DOMAIN}/"
        response = JSONResponse({
            "status": "resumed",
            "url": url,
            "session_id": existing["session_id"],
            "token": token
        })
        response.set_cookie(
            key="vbrowser_token", value=token,
            domain=f".{BASE_DOMAIN}", httponly=True,
            samesite="none", secure=True, max_age=86400
        )
        return response

    session_id     = str(uuid.uuid4())
    container_name = f"vbrowser-{session_id[:8]}"
    host_id        = session_id[:8]
    token          = secrets.token_urlsafe(32)

    url = docker_manager.create_container(user_id, username, container_name, host_id)
    register_session(session_id, user_id, username, container_name, token)

    response = JSONResponse({
        "status": "started",
        "url": url,
        "session_id": session_id,
        "token": token
    })
    response.set_cookie(
        key="vbrowser_token", value=token,
        domain=f".{BASE_DOMAIN}", httponly=True,
        samesite="none", secure=True, max_age=86400
    )
    return response


@router.post("/api/session/stop")
def stop_session(user: dict = Depends(get_current_user)):
    session = db_get_session_by_user(user["uid"])
    if session:
        docker_manager.stop_container(session["container_name"])
        db_delete_session(session["session_id"])
    response = JSONResponse({"status": "stopped"})
    response.delete_cookie("vbrowser_token", domain=f".{BASE_DOMAIN}")
    return response


@router.get("/api/sessions")
def list_sessions(user: dict = Depends(require_admin)):
    return db_list_sessions()


@router.get("/api/health")
def health():
    return {"status": "ok", "base_domain": BASE_DOMAIN, "proxy_network": PROXY_NETWORK}


@router.post("/heartbeat/{session_id}")
def heartbeat(session_id: str):
    update_heartbeat(session_id)
    return {"status": "ok"}


@router.get("/auth/verify")
def auth_verify(request: Request):
    import logging
    logger = logging.getLogger("vbrowser")
    logger.warning(f"AUTH VERIFY - path: {request.headers.get('x-forwarded-uri', 'NONE')}")
    logger.warning(f"AUTH VERIFY - upgrade: {request.headers.get('upgrade', 'NONE')}")
    logger.warning(f"AUTH VERIFY - referer: {request.headers.get('referer', 'NONE')}")
    logger.warning(f"AUTH VERIFY - origin: {request.headers.get('origin', 'NONE')}")
    logger.warning(f"AUTH VERIFY - cookie: {'YES' if request.cookies.get('vbrowser_token') else 'NO'}")

    token = request.cookies.get("vbrowser_token")
    if not token or not validate_token(token):
        logger.warning("AUTH VERIFY - RESULT: 401 (no/invalid token)")
        return Response(status_code=401)

    path = request.headers.get("x-forwarded-uri", "")
    if path.startswith("/websockify"):
        logger.warning("AUTH VERIFY - RESULT: 200 (websocket)")
        return Response(status_code=200)

    referer = request.headers.get("referer", "")
    origin  = request.headers.get("origin", "")
    referer_ok = f".{BASE_DOMAIN}" in referer or f"https://{BASE_DOMAIN}" in referer
    origin_ok  = f".{BASE_DOMAIN}" in origin  or f"https://{BASE_DOMAIN}" in origin
    no_headers = not referer and not origin

    if no_headers or (not referer_ok and not origin_ok):
        logger.warning(f"AUTH VERIFY - RESULT: 403 (referer={referer} origin={origin})")
        return Response(status_code=403)

    logger.warning("AUTH VERIFY - RESULT: 200 (ok)")
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

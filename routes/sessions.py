import secrets
from urllib.parse import urlparse, parse_qs
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from auth import get_current_user
from docker_manager import docker_manager
from config import BASE_DOMAIN, PROXY_NETWORK
from session_manager import sessions, update_heartbeat, register_session, validate_token

router = APIRouter(tags=["sessions"])


@router.post("/api/session/start")
def start_session(user: dict = Depends(get_current_user)):
    username = user["sub"]
    container_name = docker_manager.container_name(username)
    session_id = username
    token = secrets.token_urlsafe(32)

    url = docker_manager.create_container(user["uid"], username)
    register_session(session_id, container_name, token)

    response = JSONResponse({
        "status": "started",
        "url": url,
        "session_id": session_id,
        "token": token        # ← neu
    })
    response.set_cookie(
        key="vbrowser_token",
        value=token,
        domain=f".{BASE_DOMAIN}",
        httponly=True,
        samesite="lax",
        max_age=86400
    )
    return response



@router.post("/api/session/stop")
def stop_session(user: dict = Depends(get_current_user)):
    docker_manager.stop_container(user["sub"])
    response = JSONResponse({"status": "stopped"})
    response.delete_cookie("vbrowser_token", domain=f".{BASE_DOMAIN}")
    return response


@router.get("/api/health")
def health():
    return {"status": "ok", "base_domain": BASE_DOMAIN, "proxy_network": PROXY_NETWORK}


@router.post("/heartbeat/{session_id}")
def heartbeat(session_id: str):
    update_heartbeat(session_id)
    return {"status": "ok"}


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
        key="vbrowser_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400
    )
    return response

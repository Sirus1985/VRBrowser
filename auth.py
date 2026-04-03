import time
import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import SECRETKEY

# auto_error=False sorgt dafür, dass FastAPI nicht sofort abbricht, 
# wenn der Authorization-Header fehlt (da wir stattdessen das Cookie prüfen)
security = HTTPBearer(auto_error=False)
TOKEN_TTL = 3600


def create_token(user: dict, admin_teams: list) -> str:
    payload = {
        "uid": user["id"],
        "sub": user["username"],
        "admin": bool(user["isadmin"]),
        "team_id": user["team_id"],
        "admin_teams": [t["id"] for t in admin_teams],
        "exp": time.time() + TOKEN_TTL,
    }
    return jwt.encode(payload, SECRETKEY, algorithm="HS256")


def get_current_user(request: Request, creds: HTTPAuthorizationCredentials = Depends(security)):
    # 1. Token aus Header auslesen (für API-Requests aus dem Frontend)
    token = creds.credentials if creds else None
    
    # 2. Token aus Cookie auslesen (für Traefik ForwardAuth)
    if not token:
        token = request.cookies.get("vbrowser_token")
        
    if not token:
        raise HTTPException(401, "Missing authentication token")

    try:
        return jwt.decode(token, SECRETKEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


def require_admin(user: dict = Depends(get_current_user)):
    if not user.get("admin"):
        raise HTTPException(403, "Superadmin only")
    return user


def require_admin_or_teamadmin(user: dict = Depends(get_current_user)):
    if user.get("admin") or user.get("admin_teams"):
        return user
    raise HTTPException(403, "Admin or Team-Admin required")
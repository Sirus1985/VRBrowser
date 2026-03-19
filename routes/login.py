from fastapi import APIRouter, HTTPException
from models import UserLogin
from database import db_get_user, db_get_admin_teams
from auth import create_token

router = APIRouter(tags=["auth"])


@router.post("/api/login")
def login(u: UserLogin):
    user = db_get_user(u.username, u.password)
    if not user:
        raise HTTPException(401, "Login failed")
    admin_teams = db_get_admin_teams(user["id"])
    return {
        "token": create_token(user, admin_teams),
        "isadmin": bool(user["isadmin"]),
        "team_id": user["team_id"],
        "admin_teams": admin_teams,
        "auto_start_session": bool(user.get("auto_start_session", 0)),  # NEU
    }

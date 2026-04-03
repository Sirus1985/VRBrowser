from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from models import NewUser
from database import (
    db_list_users, db_get_user_by_id, db_add_user, db_delete_user,
    db_update_user, db_is_team_admin, db_get_session_by_user, db_delete_session
)
from auth import require_admin_or_teamadmin
from docker_manager import stop_container

# PREFIX auf /api/admin/users geändert
router = APIRouter(prefix="/api/admin/users", tags=["users"])

class UpdateUser(BaseModel):
    team_id:  Optional[int] = None
    password: Optional[str] = None

@router.get("")
def list_users(user: dict = Depends(require_admin_or_teamadmin)):
    if user.get("admin"):
        return db_list_users()
    result = []
    for team_id in user.get("admin_teams", []):
        result += db_list_users(team_id=team_id)
    return result

@router.post("")
def add_user(n: NewUser, user: dict = Depends(require_admin_or_teamadmin)):
    if user.get("admin"):
        if n.isadmin and n.team_id:
            raise HTTPException(400, "Superadmin cannot be in a team")
    else:
        if not n.team_id:
            raise HTTPException(400, "team_id required")
        if not db_is_team_admin(user["uid"], n.team_id):
            raise HTTPException(403, "Not your team")
        if n.isadmin:
            raise HTTPException(403, "Cannot create Superadmin")
    try:
        db_add_user(n.username, n.password, n.isadmin, n.team_id)
    except Exception:
        raise HTTPException(400, "Username already exists")
    return {"status": "ok"}

@router.patch("/{userid}")
def update_user(userid: int, body: UpdateUser, user: dict = Depends(require_admin_or_teamadmin)):
    target = db_get_user_by_id(userid)
    if not target:
        raise HTTPException(404, "User not found")
    if target["username"] == "admin":
        raise HTTPException(400, "Cannot modify default admin")
    if target["isadmin"]:
        raise HTTPException(400, "Cannot modify Superadmin")
    if not user.get("admin"):
        if not target["team_id"] or not db_is_team_admin(user["uid"], target["team_id"]):
            raise HTTPException(403, "Not your team")
        if body.team_id is not None:
            if not db_is_team_admin(user["uid"], body.team_id):
                raise HTTPException(403, "Cannot assign to a team you don't administrate")

    data = {}
    if body.team_id is not None:
        data["team_id"] = body.team_id
    if body.password is not None:
        data["password"] = body.password
    if data:
        db_update_user(userid, data)
    return {"status": "ok"}

@router.delete("/{userid}")
def delete_user(userid: int, user: dict = Depends(require_admin_or_teamadmin)):
    target = db_get_user_by_id(userid)
    if not target:
        return {"status": "ok"}
    if target["username"] == "admin":
        raise HTTPException(400, "Cannot delete default admin")
    if target["isadmin"]:
        raise HTTPException(400, "Cannot delete Superadmin")
    if not user.get("admin"):
        if not target["team_id"] or not db_is_team_admin(user["uid"], target["team_id"]):
            raise HTTPException(403, "Not your team")
    session = db_get_session_by_user(userid)
    if session:
        stop_container(session["container_name"])
        db_delete_session(session["id"])
    db_delete_user(userid)
    return {"status": "ok"}
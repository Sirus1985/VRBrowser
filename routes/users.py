from fastapi import APIRouter, HTTPException, Depends
from models import NewUser
from database import db_list_users, db_get_user_by_id, db_add_user, db_delete_user, db_is_team_admin
from auth import require_admin_or_teamadmin
from docker_manager import docker_manager

router = APIRouter(prefix="/api/users", tags=["users"])


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
    docker_manager.stop_container(target["username"])
    db_delete_user(userid)
    return {"status": "ok"}

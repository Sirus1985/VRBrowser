from fastapi import APIRouter, HTTPException, Depends
from models import NewTeam, TeamAdminAssign
from database import (
    db_list_teams, db_get_team, db_create_team, db_delete_team,
    db_list_users, db_get_user_by_id, db_is_team_admin,
    db_assign_team_admin, db_remove_team_admin, db_get_team_admins, db_get_admin_teams,
)
from auth import require_admin, require_admin_or_teamadmin

# PREFIX auf /api/admin/teams geändert
router = APIRouter(prefix="/api/admin/teams", tags=["teams"])

@router.get("")
def list_teams(user: dict = Depends(require_admin_or_teamadmin)):
    if user.get("admin"):
        return db_list_teams()
    return db_get_admin_teams(user["uid"])

@router.post("")
def add_team(t: NewTeam, user: dict = Depends(require_admin)):
    try:
        db_create_team(t.name)
        # ID zurückgeben
        teams = db_list_teams()
        new_team = next((t2 for t2 in teams if t2["name"] == t.name), None)
        return {"status": "ok", "id": new_team["id"] if new_team else None}
    except Exception:
        raise HTTPException(400, "Team already exists")

@router.delete("/{team_id}")
def delete_team(team_id: int, user: dict = Depends(require_admin)):
    if not db_get_team(team_id):
        raise HTTPException(404, "Team not found")
    db_delete_team(team_id)
    return {"status": "ok"}

@router.get("/{team_id}/users")
def get_team_users(team_id: int, user: dict = Depends(require_admin_or_teamadmin)):
    if not user.get("admin") and not db_is_team_admin(user["uid"], team_id):
        raise HTTPException(403, "Not your team")
    return db_list_users(team_id=team_id)

@router.get("/{team_id}/admins")
def get_team_admins(team_id: int, user: dict = Depends(require_admin)):
    return db_get_team_admins(team_id)

@router.post("/{team_id}/admins")
def assign_team_admin(team_id: int, body: TeamAdminAssign, user: dict = Depends(require_admin)):
    if not db_get_team(team_id):
        raise HTTPException(404, "Team not found")
    target = db_get_user_by_id(body.user_id)
    if not target:
        raise HTTPException(404, "User not found")
    if target["isadmin"]:
        raise HTTPException(400, "Superadmin cannot be Team-Admin")
    db_assign_team_admin(body.user_id, team_id)
    return {"status": "ok"}

@router.delete("/{team_id}/admins/{user_id}")
def remove_team_admin(team_id: int, user_id: int, user: dict = Depends(require_admin)):
    db_remove_team_admin(user_id, team_id)
    return {"status": "ok"}
import logging
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user, require_admin
from models import NewContainerDef, UpdateContainerDef
from database import (
    db_list_container_defs, db_get_container_def,
    db_create_container_def, db_update_container_def, db_delete_container_def
)

router = APIRouter()         # Admin-Routen
user_router = APIRouter()    # Nutzer-Routen
logger = logging.getLogger(__name__)

# ── Admin-Routen ────────────────────────────────────────────

@router.get("/api/admin/containers")
def admin_list_containers(current_user=Depends(require_admin)):
    return db_list_container_defs()

@router.get("/api/admin/containers/{def_id}")
def admin_get_container(def_id: int, current_user=Depends(require_admin)):
    cd = db_get_container_def(def_id)
    if not cd:
        raise HTTPException(status_code=404, detail="Container-Definition nicht gefunden.")
    return cd

@router.post("/api/admin/containers", status_code=201)
def admin_create_container(data: NewContainerDef, current_user=Depends(require_admin)):
    try:
        return db_create_container_def(data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/api/admin/containers/{def_id}")
def admin_update_container(def_id: int, data: UpdateContainerDef,
                           current_user=Depends(require_admin)):
    cd = db_get_container_def(def_id)
    if not cd:
        raise HTTPException(status_code=404, detail="Container-Definition nicht gefunden.")
    db_update_container_def(def_id, data.dict(exclude_unset=True))
    return db_get_container_def(def_id)

@router.delete("/api/admin/containers/{def_id}")
def admin_delete_container(def_id: int, current_user=Depends(require_admin)):
    try:
        ok = db_delete_container_def(def_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Container-Definition nicht gefunden.")
    return {"ok": True}

# ── Nutzer-Routen ────────────────────────────────────────────

@user_router.get("/api/containers")
def user_list_containers(current_user=Depends(get_current_user)):
    """Gibt die für den Nutzer erlaubten Container zurück."""
    team_id = current_user.get("team_id")
    is_admin = current_user.get("isadmin") or current_user.get("is_admin") or False
    if is_admin:
        return db_list_container_defs()
    return db_list_container_defs(team_id=team_id)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import get_current_user
from database import (
    db_get_user_by_id, db_update_user,
    db_get_user_settings, db_update_user_settings,
    db_get_container_def,
)

router = APIRouter(prefix="/api/me", tags=["user-settings"])


class UserSettingsPatch(BaseModel):
    password: Optional[str] = None
    auto_start_session: Optional[bool] = None
    preferred_container_def_id: Optional[int] = None


@router.get("/settings")
def get_my_settings(user: dict = Depends(get_current_user)):
    uid = user["uid"]
    settings = db_get_user_settings(uid)
    u = db_get_user_by_id(uid)
    return {
        "auto_start_session": settings.get("auto_start_session", False),
        "preferred_container_def_id": settings.get("preferred_container_def_id"),
    }


@router.patch("/settings")
def update_my_settings(body: UserSettingsPatch, user: dict = Depends(get_current_user)):
    uid = user["uid"]

    if body.password is not None:
        if len(body.password) < 6:
            raise HTTPException(400, "Passwort muss mindestens 6 Zeichen haben")
        db_update_user(uid, {"password": body.password})

    if body.auto_start_session is not None or body.preferred_container_def_id is not None:
        settings = db_get_user_settings(uid)
        new_auto = body.auto_start_session if body.auto_start_session is not None else settings.get("auto_start_session", False)
        new_cid = body.preferred_container_def_id if body.preferred_container_def_id is not None else settings.get("preferred_container_def_id")

        if new_cid is not None and not db_get_container_def(int(new_cid)):
            raise HTTPException(404, "Container-Definition nicht gefunden")

        db_update_user_settings(uid, new_auto, new_cid)

    return {"status": "ok"}

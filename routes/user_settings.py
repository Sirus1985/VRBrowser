from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import get_current_user
from database import db_update_user, db_get_user_by_id, db_update_user_settings, db_get_user_settings

router = APIRouter(prefix="/api/me", tags=["me"])

class MeSettings(BaseModel):
    password: Optional[str] = None
    auto_start_session: Optional[bool] = None
    preferred_container_def_id: Optional[int] = None

@router.get("/settings")
def get_settings(user: dict = Depends(get_current_user)):
    settings = db_get_user_settings(user["uid"])
    return settings

@router.patch("/settings")
def update_settings(body: MeSettings, user: dict = Depends(get_current_user)):
    if body.password is not None and body.password.strip():
        db_update_user(user["uid"], {"password": body.password})
    if body.auto_start_session is not None or body.preferred_container_def_id is not None:
        db_update_user_settings(
            user["uid"],
            body.auto_start_session or False,
            body.preferred_container_def_id
        )
    return {"status": "ok"}
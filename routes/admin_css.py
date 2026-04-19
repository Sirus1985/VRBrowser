from fastapi import APIRouter, Depends
from pydantic import BaseModel
from auth import require_admin
from database import db_get_custom_css, db_set_custom_css

router = APIRouter(prefix="/api/admin/css", tags=["admin-css"])


class CSSPayload(BaseModel):
    css: str


@router.get("")
def get_css(_user: dict = Depends(require_admin)):
    return {"css": db_get_custom_css()}


@router.post("")
def set_css(payload: CSSPayload, _user: dict = Depends(require_admin)):
    db_set_custom_css(payload.css)
    return {"ok": True}

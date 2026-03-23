from fastapi import APIRouter, Depends, Query
from typing import Optional
from auth import require_admin
from database import db_usage_ranking, db_user_session_log, db_find_user_by_container

router = APIRouter(prefix="/api/admin/logging", tags=["admin-logging"])


@router.get("/ranking")
def usage_ranking(
    period: str = Query("all", description="all|day|week|month|year"),
    year:   Optional[int] = None,
    month:  Optional[int] = None,
    week:   Optional[int] = None,
    day:    Optional[str] = None,
    _user: dict = Depends(require_admin),
):
    return db_usage_ranking(period=period, year=year, month=month, week=week, day=day)


@router.get("/user/{user_id}")
def user_sessions(
    user_id: int,
    period: str = Query("all"),
    year:   Optional[int] = None,
    month:  Optional[int] = None,
    week:   Optional[int] = None,
    day:    Optional[str] = None,
    _user: dict = Depends(require_admin),
):
    return db_user_session_log(user_id, period=period, year=year, month=month, week=week, day=day)


@router.get("/container/{container_name}")
def container_to_user(
    container_name: str,
    _user: dict = Depends(require_admin),
):
    return db_find_user_by_container(container_name)

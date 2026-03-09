from pydantic import BaseModel
from typing import Optional


class UserLogin(BaseModel):
    username: str
    password: str


class NewUser(BaseModel):
    username: str
    password: str
    isadmin: bool = False
    team_id: Optional[int] = None


class NewTeam(BaseModel):
    name: str


class TeamAdminAssign(BaseModel):
    user_id: int

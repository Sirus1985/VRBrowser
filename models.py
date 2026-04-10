from pydantic import BaseModel
from typing import Optional, List


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


class ContainerEnvVar(BaseModel):
    key: str
    value: str
    masked: bool = False  # True → GUI zeigt ••••••••


class NewContainerDef(BaseModel):
    name: str
    image: str
    internal_port: int = 5800
    shm_size: str = "2g"
    cpu_limit: Optional[float] = None   # z.B. 1.5 = 1.5 CPU-Kerne
    mem_limit: Optional[str] = None     # z.B. "2g"
    restart_policy: str = "no"
    description: Optional[str] = None
    is_default: bool = False
    env_vars: List[ContainerEnvVar] = []
    team_ids: List[int] = []            # leere Liste = alle Teams
    session_timeout: Optional[int] = None        # Sekunden; None = globaler Wert
    max_session_duration: Optional[int] = None   # Sekunden; None = globaler Wert


class UpdateContainerDef(BaseModel):
    name: Optional[str] = None
    image: Optional[str] = None
    internal_port: Optional[int] = None
    shm_size: Optional[str] = None
    cpu_limit: Optional[float] = None
    mem_limit: Optional[str] = None
    restart_policy: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    env_vars: Optional[List[ContainerEnvVar]] = None
    team_ids: Optional[List[int]] = None
    session_timeout: Optional[int] = None        # Sekunden; None = globaler Wert
    max_session_duration: Optional[int] = None   # Sekunden; None = globaler Wert


class StartSessionRequest(BaseModel):
    container_def_id: Optional[int] = None  # None → Default-Container

import os
import sqlite3
import time
from typing import Optional
from config import DBPATH


def _ensuredir():
    dbdir = os.path.dirname(DBPATH)
    if dbdir:
        os.makedirs(dbdir, exist_ok=True)


def initdb():
    _ensuredir()
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            isadmin INTEGER DEFAULT 0,
            team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL
        )
    """)

    for col in [
        "ALTER TABLE users ADD COLUMN isadmin INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL",
    ]:
        try:
            cur.execute(col)
        except sqlite3.OperationalError:
            pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS team_admins (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, team_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            username TEXT NOT NULL,
            container_name TEXT NOT NULL,
            token TEXT NOT NULL,
            last_seen REAL NOT NULL,
            created_at REAL NOT NULL
        )
    """)

    cur.execute(
        "INSERT OR IGNORE INTO users (username, password, isadmin) VALUES (?, ?, ?)",
        ("admin", "adminpass", 1),
    )
    conn.commit()
    conn.close()


def get_conn():
    conn = sqlite3.connect(DBPATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---- Users ----

def db_get_user(username: str, password: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, isadmin, team_id FROM users WHERE username=? AND password=?",
            (username, password),
        ).fetchone()
    return dict(row) if row else None


def db_get_user_by_id(userid: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, isadmin, team_id FROM users WHERE id=?", (userid,)
        ).fetchone()
    return dict(row) if row else None


def db_list_users(team_id: Optional[int] = None):
    with get_conn() as conn:
        if team_id is not None:
            rows = conn.execute(
                "SELECT id, username, isadmin, team_id FROM users WHERE team_id=? ORDER BY username",
                (team_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, username, isadmin, team_id FROM users ORDER BY username"
            ).fetchall()
    return [dict(r) for r in rows]


def db_add_user(username: str, password: str, isadmin: bool, team_id: Optional[int] = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (username, password, isadmin, team_id) VALUES (?, ?, ?, ?)",
            (username, password, 1 if isadmin else 0, team_id),
        )
        conn.commit()


def db_delete_user(userid: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (userid,))
        conn.commit()


# ---- Teams ----

def db_list_teams():
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name FROM teams ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def db_get_team(team_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT id, name FROM teams WHERE id=?", (team_id,)).fetchone()
    return dict(row) if row else None


def db_add_team(name: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO teams (name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid


def db_delete_team(team_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM teams WHERE id=?", (team_id,))
        conn.commit()


# ---- Team Admins ----

def db_get_admin_teams(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT t.id, t.name FROM teams t
               JOIN team_admins ta ON t.id = ta.team_id
               WHERE ta.user_id = ?""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def db_is_team_admin(user_id: int, team_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM team_admins WHERE user_id=? AND team_id=?", (user_id, team_id)
        ).fetchone()
    return row is not None


def db_assign_team_admin(user_id: int, team_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO team_admins (user_id, team_id) VALUES (?, ?)", (user_id, team_id)
        )
        conn.commit()


def db_remove_team_admin(user_id: int, team_id: int):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM team_admins WHERE user_id=? AND team_id=?", (user_id, team_id)
        )
        conn.commit()


def db_get_team_admins(team_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT u.id, u.username FROM users u
               JOIN team_admins ta ON u.id = ta.user_id
               WHERE ta.team_id = ?""",
            (team_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---- Sessions ----

def db_create_session(session_id: str, user_id: int, username: str, container_name: str, token: str):
    now = time.time()
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO sessions
               (session_id, user_id, username, container_name, token, last_seen, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, username, container_name, token, now, now),
        )
        conn.commit()


def db_update_heartbeat(session_id: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET last_seen=? WHERE session_id=?",
            (time.time(), session_id),
        )
        conn.commit()


def db_delete_session(session_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        conn.commit()


def db_list_sessions():
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT s.session_id, s.username, s.container_name, s.last_seen, s.created_at,
                      u.team_id
               FROM sessions s
               JOIN users u ON s.user_id = u.id
               ORDER BY s.created_at DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


def db_get_session_by_token(token: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE token=?", (token,)
        ).fetchone()
    return dict(row) if row else None


def db_get_session_by_user(user_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE user_id=?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def db_get_timed_out_sessions(timeout: float):
    cutoff = time.time() - timeout
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE last_seen < ?", (cutoff,)
        ).fetchall()
    return [dict(r) for r in rows]

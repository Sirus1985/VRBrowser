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
        "ALTER TABLE users ADD COLUMN auto_start_session INTEGER DEFAULT 0",
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

    # NEU: Historischer Session-Log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS session_log (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            username       TEXT NOT NULL,
            container_name TEXT NOT NULL,
            started_at     REAL NOT NULL,
            ended_at       REAL NOT NULL,
            duration       REAL NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_log_user    ON session_log(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_log_started ON session_log(started_at)")

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
            "SELECT id, username, isadmin, team_id, auto_start_session FROM users WHERE username=? AND password=?",
            (username, password),
        ).fetchone()
        return dict(row) if row else None


def db_get_user_by_id(userid: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, isadmin, team_id, auto_start_session FROM users WHERE id=?", (userid,)
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


def db_update_user_settings(user_id: int, auto_start_session: bool):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET auto_start_session=? WHERE id=?",
            (1 if auto_start_session else 0, user_id),
        )
        conn.commit()


def db_get_user_settings(user_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT auto_start_session FROM users WHERE id=?", (user_id,)
        ).fetchone()
        return dict(row) if row else {"auto_start_session": 0}


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


def db_close_session(session_id: str):
    """Archiviert eine Sitzung in session_log und löscht sie aus der aktiven Tabelle."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT user_id, username, container_name, created_at, last_seen FROM sessions WHERE session_id=?",
            (session_id,)
        ).fetchone()
        if row:
            ended_at = time.time()
            duration = ended_at - row["created_at"]
            conn.execute(
                """INSERT INTO session_log (user_id, username, container_name, started_at, ended_at, duration)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (row["user_id"], row["username"], row["container_name"],
                 row["created_at"], ended_at, duration)
            )
            conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
            conn.commit()


# Alias: altes db_delete_session wird durch db_close_session ersetzt
def db_delete_session(session_id: str):
    db_close_session(session_id)


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
        row = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
        return dict(row) if row else None


def db_get_session_by_user(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def db_get_timed_out_sessions(timeout: float):
    cutoff = time.time() - timeout
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE last_seen < ?", (cutoff,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---- Session Log / Nutzungsanalyse ----

def _build_time_filter(period: str, year=None, month=None, week=None, day=None):
    """Baut WHERE-Klausel + Params für Zeitfilter."""
    conditions = []
    params = []

    if period == "day" and day:
        # day = "YYYY-MM-DD"
        import datetime
        dt = datetime.datetime.strptime(day, "%Y-%m-%d")
        ts_start = dt.timestamp()
        ts_end   = (dt + datetime.timedelta(days=1)).timestamp()
        conditions.append("started_at >= ? AND started_at < ?")
        params += [ts_start, ts_end]

    elif period == "week" and year and week:
        import datetime
        dt_start = datetime.datetime.fromisocalendar(int(year), int(week), 1)
        dt_end   = dt_start + datetime.timedelta(weeks=1)
        conditions.append("started_at >= ? AND started_at < ?")
        params += [dt_start.timestamp(), dt_end.timestamp()]

    elif period == "month" and year and month:
        import datetime, calendar
        dt_start = datetime.datetime(int(year), int(month), 1)
        last_day = calendar.monthrange(int(year), int(month))[1]
        dt_end   = datetime.datetime(int(year), int(month), last_day, 23, 59, 59)
        conditions.append("started_at >= ? AND started_at < ?")
        params += [dt_start.timestamp(), dt_end.timestamp() + 1]

    elif period == "year" and year:
        import datetime
        dt_start = datetime.datetime(int(year), 1, 1)
        dt_end   = datetime.datetime(int(year) + 1, 1, 1)
        conditions.append("started_at >= ? AND started_at < ?")
        params += [dt_start.timestamp(), dt_end.timestamp()]

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params


def db_usage_ranking(period="all", year=None, month=None, week=None, day=None):
    """Rangliste aller Nutzer nach Gesamtnutzungszeit."""
    where, params = _build_time_filter(period, year, month, week, day)
    with get_conn() as conn:
        rows = conn.execute(f"""
            SELECT username, user_id,
                   COUNT(*) as session_count,
                   SUM(duration) as total_seconds
            FROM session_log
            {where}
            GROUP BY user_id
            ORDER BY total_seconds DESC
        """, params).fetchall()
    return [dict(r) for r in rows]


def db_user_session_log(user_id: int, period="all", year=None, month=None, week=None, day=None):
    """Alle archivierten Sitzungen eines Nutzers."""
    where, params = _build_time_filter(period, year, month, week, day)
    and_clause = where.replace("WHERE", "AND") if where else ""
    with get_conn() as conn:
        rows = conn.execute(f"""
            SELECT id, container_name, started_at, ended_at, duration
            FROM session_log
            WHERE user_id=? {and_clause}
            ORDER BY started_at DESC
        """, [user_id] + params).fetchall()
    return [dict(r) for r in rows]


def db_find_user_by_container(container_name: str):
    """Rückwärtssuche: Welche Nutzer haben diesen Container genutzt?"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT DISTINCT sl.username, sl.user_id,
                   COUNT(*) as session_count,
                   SUM(sl.duration) as total_seconds
            FROM session_log sl
            WHERE sl.container_name = ?
            GROUP BY sl.user_id
            ORDER BY sl.username
        """, (container_name,)).fetchall()
    return [dict(r) for r in rows]

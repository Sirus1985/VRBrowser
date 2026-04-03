import os
import sqlite3
import time
import json
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
            container_ip TEXT,
            token TEXT NOT NULL,
            last_seen REAL NOT NULL,
            created_at REAL NOT NULL
        )
    """)

    # Migration für bestehende sessions-Tabelle
    try:
        cur.execute("ALTER TABLE sessions ADD COLUMN container_ip TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE sessions ADD COLUMN image TEXT")
    except sqlite3.OperationalError:
        pass

    # KORRIGIERTE SYNTAX FÜR session_log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS session_log (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            username       TEXT NOT NULL,
            container_name TEXT NOT NULL,
            container_ip   TEXT,
            started_at     REAL NOT NULL,
            ended_at       REAL NOT NULL,
            duration       REAL NOT NULL,
            image          TEXT
        )
    """)
    
    try:
        cur.execute("ALTER TABLE session_log ADD COLUMN image TEXT")
    except sqlite3.OperationalError:
        pass

    # Migration für bestehende session_log-Tabelle
    try:
        cur.execute("ALTER TABLE session_log ADD COLUMN container_ip TEXT")
    except sqlite3.OperationalError:
        pass

    # --- FEHLENDE CONTAINER DEFS TABELLE HINZUGEFÜGT ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS container_defs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            image TEXT NOT NULL,
            tag TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            team_ids TEXT
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_log_user    ON session_log(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_log_started ON session_log(started_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_log_ip      ON session_log(container_ip)")

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

# --- FEHLENDE DB_UPDATE_USER FUNKTION HINZUGEFÜGT ---
def db_update_user(userid: int, data: dict):
    if not data:
        return
    fields = []
    values = []
    for k, v in data.items():
        fields.append(f"{k}=?")
        values.append(v)
    values.append(userid)
    
    query = f"UPDATE users SET {', '.join(fields)} WHERE id=?"
    with get_conn() as conn:
        conn.execute(query, values)
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

def db_create_session(session_id: str, user_id: int, username: str,
                      container_name: str, token: str, container_ip: str = None, image: str = None):
    now = time.time()
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO sessions
               (session_id, user_id, username, container_name, container_ip, token, last_seen, created_at, image)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, username, container_name, container_ip, token, now, now, image),
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
            "SELECT user_id, username, container_name, container_ip, created_at, image FROM sessions WHERE session_id=?",
            (session_id,)
        ).fetchone()
        if row:
            ended_at = time.time()
            duration = ended_at - row["created_at"]
            conn.execute(
                """INSERT INTO session_log
                   (user_id, username, container_name, container_ip, started_at, ended_at, duration, image)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (row["user_id"], row["username"], row["container_name"], row["container_ip"],
                 row["created_at"], ended_at, duration, row.get("image"))
            )
            conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
            conn.commit()

# Alias: altes db_delete_session wird durch db_close_session ersetzt
def db_delete_session(session_id: str):
    db_close_session(session_id)

def db_list_sessions(user_id: int = None):
    with get_conn() as conn:
        if user_id:
            rows = conn.execute(
                """SELECT s.session_id, s.username, s.container_name, s.container_ip,
                          s.last_seen, s.created_at, u.team_id, s.image
                   FROM sessions s
                   JOIN users u ON s.user_id = u.id
                   WHERE s.user_id = ?
                   ORDER BY s.created_at DESC""", (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT s.session_id, s.username, s.container_name, s.container_ip,
                          s.last_seen, s.created_at, u.team_id, s.image
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
            SELECT id, container_name, container_ip, started_at, ended_at, duration, image
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

def db_search_session_log(
    query: str = None,
    container_ip: str = None,
    period="all", year=None, month=None, week=None, day=None
):
    """
    Durchsucht den Session-Log nach username, container_name oder IP.
    Zeitraum-Filter identisch zur Nutzungsrangliste.
    """
    where, params = _build_time_filter(period, year, month, week, day)
    conditions = [where.replace("WHERE ", "")] if where else []

    if container_ip:
        conditions.append("container_ip = ?")
        params.append(container_ip)

    if query:
        conditions.append("(username LIKE ? OR container_name LIKE ? OR container_ip LIKE ?)")
        q = f"%{query}%"
        params += [q, q, q]

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_conn() as conn:
        rows = conn.execute(f"""
            SELECT id, username, user_id, container_name, container_ip,
                   started_at, ended_at, duration, image
            FROM session_log
            {where_clause}
            ORDER BY started_at DESC
            LIMIT 500
        """, params).fetchall()
    return [dict(r) for r in rows]

# --- FEHLENDE FUNKTION FÜR ADMIN LOGGING HINZUGEFÜGT ---
def db_team_ranking(period="all", year=None, month=None, week=None, day=None):
    """Rangliste aller Teams nach Gesamtnutzungszeit."""
    where, params = _build_time_filter(period, year, month, week, day)
    with get_conn() as conn:
        rows = conn.execute(f"""
            SELECT t.name as team_name, t.id as team_id,
                   COUNT(sl.id) as session_count,
                   SUM(sl.duration) as total_seconds
            FROM session_log sl
            JOIN users u ON sl.user_id = u.id
            JOIN teams t ON u.team_id = t.id
            {where.replace("WHERE", "WHERE ")}
            GROUP BY t.id
            ORDER BY total_seconds DESC
        """, params).fetchall()
    return [dict(r) for r in rows]

# --- FEHLENDE CONTAINER DEFS FUNKTIONEN HINZUGEFÜGT ---
def db_list_container_defs(team_id: Optional[int] = None):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM container_defs ORDER BY name").fetchall()
        
    result = []
    for r in rows:
        d = dict(r)
        d["team_ids"] = json.loads(d["team_ids"]) if d["team_ids"] else []
        if team_id is None or d["is_default"] or team_id in d["team_ids"]:
            result.append(d)
    return result

def db_get_container_def(def_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM container_defs WHERE id=?", (def_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["team_ids"] = json.loads(d["team_ids"]) if d["team_ids"] else []
        return d

def db_get_default_container_def():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM container_defs WHERE is_default=1 LIMIT 1").fetchone()
        if not row:
            row = conn.execute("SELECT * FROM container_defs LIMIT 1").fetchone()
        if not row:
            return None
        d = dict(row)
        d["team_ids"] = json.loads(d["team_ids"]) if d["team_ids"] else []
        return d

def db_create_container_def(data: dict):
    with get_conn() as conn:
        if data.get("is_default"):
            conn.execute("UPDATE container_defs SET is_default=0")
            
        cur = conn.execute(
            """INSERT INTO container_defs (name, image, tag, is_default, team_ids)
               VALUES (?, ?, ?, ?, ?)""",
            (
                data["name"], data["image"], data.get("tag", "latest"),
                1 if data.get("is_default") else 0,
                json.dumps(data.get("team_ids", []))
            )
        )
        conn.commit()
        return db_get_container_def(cur.lastrowid)

def db_update_container_def(def_id: int, data: dict):
    current = db_get_container_def(def_id)
    if not current:
        return None
        
    with get_conn() as conn:
        if data.get("is_default"):
            conn.execute("UPDATE container_defs SET is_default=0")
            
        fields = []
        values = []
        for k, v in data.items():
            if k == "team_ids":
                v = json.dumps(v)
            fields.append(f"{k}=?")
            values.append(v)
        values.append(def_id)
        
        if fields:
            conn.execute(f"UPDATE container_defs SET {', '.join(fields)} WHERE id=?", values)
            conn.commit()
    return db_get_container_def(def_id)

def db_delete_container_def(def_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM container_defs WHERE id=?", (def_id,))
        conn.commit()
        return cur.rowcount > 0
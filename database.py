import os
import sqlite3
import time
import json
import datetime
from typing import Optional
from config import DBPATH, SECRETKEY

def to_dict(row):
    if not row: return None
    d = dict(row)
    for k in ["created_at", "last_seen", "started_at", "ended_at", "timestamp"]:
        if k in d and d[k] is not None:
            d[k] = datetime.datetime.fromtimestamp(float(d[k]), tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    return d

def get_conn():
    conn = sqlite3.connect(DBPATH)
    conn.row_factory = sqlite3.Row
    return conn

def initdb():
    os.makedirs(os.path.dirname(DBPATH), exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            isadmin INTEGER DEFAULT 0,
            team_id INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS team_admins (
            user_id INTEGER,
            team_id INTEGER,
            PRIMARY KEY (user_id, team_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            container_name TEXT NOT NULL,
            container_ip TEXT,
            token TEXT NOT NULL,
            last_seen REAL NOT NULL,
            created_at REAL NOT NULL,
            image TEXT,
            container_def_id INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            container_name TEXT,
            container_ip TEXT,
            started_at REAL,
            ended_at REAL,
            duration REAL,
            image TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            auto_start_session INTEGER DEFAULT 0
        )
    """)

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
        ("admin", SECRETKEY, 1),
    )
    conn.commit()

    # --- Migrationen: neue Spalten (nicht-destruktiv)
    migrations = [
        "ALTER TABLE sessions ADD COLUMN image TEXT",
        "ALTER TABLE session_log ADD COLUMN image TEXT",
        "ALTER TABLE container_defs ADD COLUMN env_vars TEXT",
        "ALTER TABLE container_defs ADD COLUMN internal_port INTEGER DEFAULT 5800",
        "ALTER TABLE container_defs ADD COLUMN cpu_limit TEXT",
        "ALTER TABLE container_defs ADD COLUMN mem_limit TEXT",
        "ALTER TABLE container_defs ADD COLUMN shm_size TEXT DEFAULT '2g'",
        "ALTER TABLE container_defs ADD COLUMN restart_policy TEXT DEFAULT 'no'",
        # RFC-07: per-Container Timeout-Overrides
        "ALTER TABLE container_defs ADD COLUMN session_timeout INTEGER",
        "ALTER TABLE container_defs ADD COLUMN max_session_duration INTEGER",
        # RFC-07: sessions speichert container_def_id fuer Timeout-Lookup
        "ALTER TABLE sessions ADD COLUMN container_def_id INTEGER",
        "ALTER TABLE user_settings ADD COLUMN preferred_container_def_id INTEGER",
        
    ]
    for sql in migrations:
        try:
            cur.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass

    if cur.execute("SELECT COUNT(*) FROM container_defs").fetchone()[0] == 0:
        default_env = json.dumps([
            {"key": "KEEP_APP_RUNNING", "value": "1"},
            {"key": "FF_PREF_network.trr.mode", "value": "5"}
        ])
        cur.execute("""
            INSERT INTO container_defs
            (name, image, tag, is_default, internal_port, env_vars, shm_size, restart_policy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Firefox (Default)", "jlesage/firefox", "latest", 1, 5800, default_env, "2g", "no"))
        conn.commit()

    conn.close()

# ---------------------------------------------------------
# USERS
# ---------------------------------------------------------
def db_get_user(username: str, password: str):
    with get_conn() as conn:
        return to_dict(conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone())

def db_get_user_by_id(userid: int):
    with get_conn() as conn:
        return to_dict(conn.execute("SELECT * FROM users WHERE id=?", (userid,)).fetchone())

def db_list_users(team_id: Optional[int] = None):
    with get_conn() as conn:
        if team_id is not None:
            rows = conn.execute("""
                SELECT u.id, u.username, u.isadmin, u.team_id, t.name as team_name
                FROM users u
                LEFT JOIN teams t ON u.team_id = t.id
                WHERE u.team_id = ?
            """, (team_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT u.id, u.username, u.isadmin, u.team_id, t.name as team_name
                FROM users u
                LEFT JOIN teams t ON u.team_id = t.id
            """).fetchall()
        return [to_dict(r) for r in rows]

def db_add_user(username: str, password: str, isadmin: bool, team_id: Optional[int] = None):
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, password, isadmin, team_id) VALUES (?, ?, ?, ?)",
                (username, password, 1 if isadmin else 0, team_id),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def db_update_user(userid: int, data: dict):
    with get_conn() as conn:
        try:
            updates = []
            values = []
            if "username" in data:
                updates.append("username=?")
                values.append(data["username"])
            if "password" in data and data["password"]:
                updates.append("password=?")
                values.append(data["password"])
            if "isadmin" in data:
                updates.append("isadmin=?")
                values.append(1 if data["isadmin"] else 0)
            if "team_id" in data:
                updates.append("team_id=?")
                values.append(data["team_id"])
            if not updates:
                return False
            values.append(userid)
            conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id=?", values)
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def db_delete_user(userid: int):
    with get_conn() as conn:
        user = conn.execute("SELECT isadmin FROM users WHERE id=?", (userid,)).fetchone()
        if user and user["isadmin"]:
            admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE isadmin=1").fetchone()[0]
            if admin_count <= 1:
                return False
        conn.execute("DELETE FROM users WHERE id=?", (userid,))
        conn.commit()
        return True

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------
def db_update_user_settings(user_id: int, auto_start_session: bool, preferred_container_def_id: int = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_settings (user_id, auto_start_session, preferred_container_def_id) VALUES (?, ?, ?)",
            (user_id, 1 if auto_start_session else 0, preferred_container_def_id),
        )
        conn.commit()

def db_get_user_settings(user_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT auto_start_session, preferred_container_def_id FROM user_settings WHERE user_id=?",
            (user_id,)
        ).fetchone()
        return {
            "auto_start_session": bool(row["auto_start_session"]) if row else False,
            "preferred_container_def_id": row["preferred_container_def_id"] if row else None,
        }
# ---------------------------------------------------------
# TEAMS
# ---------------------------------------------------------
def db_list_teams():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM teams").fetchall()
        result = []
        for r in rows:
            d = to_dict(r)
            d["users_count"] = conn.execute("SELECT COUNT(*) FROM users WHERE team_id=?", (d["id"],)).fetchone()[0]
            admins = conn.execute("SELECT user_id FROM team_admins WHERE team_id=?", (d["id"],)).fetchall()
            d["admin_ids"] = [a["user_id"] for a in admins]
            result.append(d)
        return result

def db_get_team(team_id: int):
    with get_conn() as conn:
        return to_dict(conn.execute("SELECT * FROM teams WHERE id=?", (team_id,)).fetchone())

def db_add_team(name: str) -> int:
    with get_conn() as conn:
        try:
            cur = conn.execute("INSERT INTO teams (name) VALUES (?)", (name,))
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

def db_delete_team(team_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET team_id=NULL WHERE team_id=?", (team_id,))
        conn.execute("DELETE FROM teams WHERE id=?", (team_id,))
        conn.commit()
        return True

def db_get_admin_teams(user_id: int):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT t.* FROM teams t
            JOIN team_admins ta ON t.id = ta.team_id
            WHERE ta.user_id=?
        """, (user_id,)).fetchall()
        return [to_dict(r) for r in rows]

def db_is_team_admin(user_id: int, team_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM team_admins WHERE user_id=? AND team_id=?", (user_id, team_id)).fetchone()
        return row is not None

def db_assign_team_admin(user_id: int, team_id: int):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO team_admins (user_id, team_id) VALUES (?, ?)", (user_id, team_id))
        conn.commit()

def db_remove_team_admin(user_id: int, team_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM team_admins WHERE user_id=? AND team_id=?", (user_id, team_id))
        conn.commit()

def db_get_team_admins(team_id: int):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT u.id, u.username
            FROM users u
            JOIN team_admins ta ON u.id = ta.user_id
            WHERE ta.team_id=?
        """, (team_id,)).fetchall()
        return [to_dict(r) for r in rows]

# ---------------------------------------------------------
# SESSIONS
# ---------------------------------------------------------
def db_create_session(session_id: str, user_id: int, username: str,
                      container_name: str, token: str, container_ip: str = None,
                      image: str = None, container_def_id: int = None):
    now = time.time()
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO sessions
               (session_id, user_id, username, container_name, container_ip, token,
                last_seen, created_at, image, container_def_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, username, container_name, container_ip, token,
             now, now, image, container_def_id),
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
                 row["created_at"], ended_at, duration, row["image"])
            )
            conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
            conn.commit()

def db_delete_session(session_id: str):
    db_close_session(session_id)

def db_list_sessions(user_id: int = None):
    with get_conn() as conn:
        if user_id:
            rows = conn.execute(
                """SELECT s.session_id, s.username, s.container_name, s.container_ip,
                          s.last_seen, s.created_at, u.team_id, s.image, s.container_def_id
                   FROM sessions s
                   LEFT JOIN users u ON s.user_id = u.id
                   WHERE s.user_id = ?""",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT s.session_id, s.username, s.container_name, s.container_ip,
                          s.last_seen, s.created_at, u.team_id, s.image, s.container_def_id
                   FROM sessions s
                   LEFT JOIN users u ON s.user_id = u.id"""
            ).fetchall()
        return [to_dict(r) for r in rows]

def db_get_session_by_token(token: str):
    with get_conn() as conn:
        return to_dict(conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone())

def db_get_session_by_id(session_id: str):
    with get_conn() as conn:
        return to_dict(conn.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone())

def db_get_session_by_user(user_id: int):
    with get_conn() as conn:
        return to_dict(conn.execute("SELECT * FROM sessions WHERE user_id=?", (user_id,)).fetchone())

def db_get_timed_out_sessions(timeout: float):
    """Liefert Sessions deren last_seen aelter als timeout Sekunden ist (globaler Fallback)."""
    cutoff = time.time() - timeout
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM sessions WHERE last_seen < ?", (cutoff,)).fetchall()
        return [to_dict(r) for r in rows]

def db_get_container_def_timeouts(container_def_id: int) -> dict:
    """Gibt session_timeout und max_session_duration eines Container-Defs zurueck (oder None je Feld)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT session_timeout, max_session_duration FROM container_defs WHERE id=?",
            (container_def_id,)
        ).fetchone()
        if not row:
            return {"session_timeout": None, "max_session_duration": None}
        return {"session_timeout": row["session_timeout"], "max_session_duration": row["max_session_duration"]}

# ---------------------------------------------------------
# DASHBOARD / LOGS
# ---------------------------------------------------------
def db_usage_ranking(period="all", year=None, month=None, week=None, day=None, image=None, container_name=None):
    with get_conn() as conn:
        q = """
            SELECT user_id, username,
                   COUNT(*) AS session_count,
                   COALESCE(SUM(duration), 0) AS total_seconds
            FROM session_log
        """
        cond = []
        p = []

        if period == "month" and year and month:
            cond.append("strftime('%Y', datetime(started_at, 'unixepoch')) = ?")
            cond.append("strftime('%m', datetime(started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{month:02d}"])
        elif period == "week" and year and week:
            cond.append("strftime('%Y', datetime(started_at, 'unixepoch')) = ?")
            cond.append("strftime('%W', datetime(started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{week:02d}"])
        elif period == "day" and year and month and day:
            cond.append("strftime('%Y', datetime(started_at, 'unixepoch')) = ?")
            cond.append("strftime('%m', datetime(started_at, 'unixepoch')) = ?")
            cond.append("strftime('%d', datetime(started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{month:02d}", f"{day:02d}"])

        if image:
            cond.append("image = ?")
            p.append(image)

        if container_name:
            cond.append("container_name LIKE ?")
            p.append(f"%{container_name}%")

        if cond:
            q += " WHERE " + " AND ".join(cond)

        q += " GROUP BY user_id, username ORDER BY total_seconds DESC LIMIT 20"
        rows = conn.execute(q, p).fetchall()
        return [to_dict(r) for r in rows]

def db_user_session_log(user_id: int, period="all", year=None, month=None, week=None, day=None, image=None, container_name=None):
    with get_conn() as conn:
        q = "SELECT * FROM session_log WHERE user_id=?"
        cond = []
        p = [user_id]

        if period == "month" and year and month:
            cond.append("strftime('%Y', datetime(started_at, 'unixepoch')) = ?")
            cond.append("strftime('%m', datetime(started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{month:02d}"])
        elif period == "week" and year and week:
            cond.append("strftime('%Y', datetime(started_at, 'unixepoch')) = ?")
            cond.append("strftime('%W', datetime(started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{week:02d}"])
        elif period == "day" and year and month and day:
            cond.append("strftime('%Y', datetime(started_at, 'unixepoch')) = ?")
            cond.append("strftime('%m', datetime(started_at, 'unixepoch')) = ?")
            cond.append("strftime('%d', datetime(started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{month:02d}", f"{day:02d}"])

        if image:
            cond.append("image = ?")
            p.append(image)

        if container_name:
            cond.append("container_name LIKE ?")
            p.append(f"%{container_name}%")

        if cond:
            q += " AND " + " AND ".join(cond)

        q += " ORDER BY id DESC"
        rows = conn.execute(q, p).fetchall()
        return [to_dict(r) for r in rows]

def db_find_user_by_container(container_name: str):
    with get_conn() as conn:
        row = conn.execute("SELECT username FROM session_log WHERE container_name=?", (container_name,)).fetchone()
        if row: return to_dict(row)["username"]
        row = conn.execute("SELECT username FROM sessions WHERE container_name=?", (container_name,)).fetchone()
        if row: return to_dict(row)["username"]
        return "Unbekannt"

def db_search_session_log(
    page: int = 1,
    limit: int = 50,
    search_query: str = "",
    year: int = None,
    month: int = None,
    day: int = None,
    team_id: int = None
):
    offset = (page - 1) * limit
    cond = []
    p = []

    if search_query:
        cond.append("(sl.username LIKE ? OR sl.container_name LIKE ? OR sl.container_ip LIKE ?)")
        p.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

    if year:
        cond.append("strftime('%Y', datetime(sl.started_at, 'unixepoch')) = ?")
        p.append(str(year))
    if month:
        cond.append("strftime('%m', datetime(sl.started_at, 'unixepoch')) = ?")
        p.append(f"{month:02d}")
    if day:
        cond.append("strftime('%d', datetime(sl.started_at, 'unixepoch')) = ?")
        p.append(f"{day:02d}")

    join_clause = ""
    if team_id:
        join_clause = " LEFT JOIN users u ON sl.user_id = u.id "
        cond.append("u.team_id = ?")
        p.append(team_id)

    where_clause = ""
    if cond:
        where_clause = "WHERE " + " AND ".join(cond)

    q = f"""
        SELECT sl.* FROM session_log sl
        {join_clause}
        {where_clause}
        ORDER BY sl.id DESC
        LIMIT ? OFFSET ?
    """
    count_q = f"""
        SELECT COUNT(*) FROM session_log sl
        {join_clause}
        {where_clause}
    """

    p_full = p + [limit, offset]
    with get_conn() as conn:
        rows = conn.execute(q, p_full).fetchall()
        total = conn.execute(count_q, p).fetchone()[0]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "logs": [to_dict(r) for r in rows]
    }

def db_team_ranking(period="all", year=None, month=None, week=None, day=None):
    with get_conn() as conn:
        q = """
            SELECT t.id as team_id, t.name as team_name, SUM(sl.duration) as total_time
            FROM session_log sl
            JOIN users u ON sl.user_id = u.id
            JOIN teams t ON u.team_id = t.id
        """
        cond = []
        p = []
        if period == "month" and year and month:
            cond.append("strftime('%Y', datetime(sl.started_at, 'unixepoch')) = ?")
            cond.append("strftime('%m', datetime(sl.started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{month:02d}"])
        elif period == "week" and year and week:
            cond.append("strftime('%Y', datetime(sl.started_at, 'unixepoch')) = ?")
            cond.append("strftime('%W', datetime(sl.started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{week:02d}"])
        elif period == "day" and year and month and day:
            cond.append("strftime('%Y', datetime(sl.started_at, 'unixepoch')) = ?")
            cond.append("strftime('%m', datetime(sl.started_at, 'unixepoch')) = ?")
            cond.append("strftime('%d', datetime(sl.started_at, 'unixepoch')) = ?")
            p.extend([str(year), f"{month:02d}", f"{day:02d}"])

        if cond:
            q += " WHERE " + " AND ".join(cond)

        q += " GROUP BY t.id, t.name ORDER BY total_time DESC"
        rows = conn.execute(q, p).fetchall()
        return [to_dict(r) for r in rows]

# ---------------------------------------------------------
# CONTAINER DEFINITIONS
# ---------------------------------------------------------
def db_list_container_defs(team_id: Optional[int] = None):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM container_defs").fetchall()
        result = []
        for r in rows:
            d = to_dict(r)
            d["team_ids"] = json.loads(d["team_ids"]) if d.get("team_ids") else []
            d["env_vars"] = json.loads(d["env_vars"]) if d.get("env_vars") else []
            if team_id is not None:
                if d["team_ids"] and team_id not in d["team_ids"]:
                    continue
            result.append(d)
        return result

def db_get_container_def(def_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM container_defs WHERE id=?", (def_id,)).fetchone()
        if not row: return None
        d = to_dict(row)
        d["team_ids"] = json.loads(d["team_ids"]) if d.get("team_ids") else []
        d["env_vars"] = json.loads(d["env_vars"]) if d.get("env_vars") else []
        return d

def db_get_default_container_def():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM container_defs WHERE is_default=1 LIMIT 1").fetchone()
        if not row:
            row = conn.execute("SELECT * FROM container_defs LIMIT 1").fetchone()
        if not row: return None
        d = to_dict(row)
        d["team_ids"] = json.loads(d["team_ids"]) if d.get("team_ids") else []
        d["env_vars"] = json.loads(d["env_vars"]) if d.get("env_vars") else []
        return d

def db_create_container_def(data: dict):
    with get_conn() as conn:
        if data.get("is_default"):
            conn.execute("UPDATE container_defs SET is_default=0")
        team_ids_str = json.dumps(data.get("team_ids", []))
        env_vars_str = json.dumps(data.get("env_vars", []))
        cur = conn.execute("""
            INSERT INTO container_defs
            (name, image, tag, is_default, team_ids, internal_port, env_vars,
             cpu_limit, mem_limit, shm_size, restart_policy,
             session_timeout, max_session_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["name"], data["image"], data.get("tag", "latest"),
            1 if data.get("is_default") else 0, team_ids_str,
            data.get("internal_port", 5800), env_vars_str,
            data.get("cpu_limit"), data.get("mem_limit"),
            data.get("shm_size", "2g"), data.get("restart_policy", "no"),
            data.get("session_timeout"),
            data.get("max_session_duration"),
        ))
        conn.commit()
        return cur.lastrowid

def db_update_container_def(def_id: int, data: dict):
    with get_conn() as conn:
        if data.get("is_default"):
            conn.execute("UPDATE container_defs SET is_default=0")
        team_ids_str = json.dumps(data.get("team_ids", []))
        env_vars_str = json.dumps(data.get("env_vars", []))
        conn.execute("""
            UPDATE container_defs
            SET name=?, image=?, tag=?, is_default=?, team_ids=?, internal_port=?, env_vars=?,
                cpu_limit=?, mem_limit=?, shm_size=?, restart_policy=?,
                session_timeout=?, max_session_duration=?
            WHERE id=?
        """, (
            data["name"], data["image"], data.get("tag", "latest"),
            1 if data.get("is_default") else 0, team_ids_str,
            data.get("internal_port", 5800), env_vars_str,
            data.get("cpu_limit"), data.get("mem_limit"),
            data.get("shm_size", "2g"), data.get("restart_policy", "no"),
            data.get("session_timeout"),
            data.get("max_session_duration"),
            def_id
        ))
        conn.commit()

def db_delete_container_def(def_id: int) -> bool:
    with get_conn() as conn:
        conn.execute("DELETE FROM container_defs WHERE id=?", (def_id,))
        conn.commit()
        return True

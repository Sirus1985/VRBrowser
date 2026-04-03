import os
import sqlite3
import time
import json
from typing import Optional
from config import DBPATH, SECRETKEY

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
            PRIMARY KEY (user_id, team_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
        )
    """)

    # NEU: Spalte 'image' für Docker-Image
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
            image TEXT
        )
    """)

    # NEU: Spalte 'image' für Docker-Image in den Logs
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
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            admin_username TEXT NOT NULL,
            action TEXT NOT NULL,
            target_user TEXT,
            details TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            settings TEXT NOT NULL
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

    # --- KORREKTUR: Verwende SECRETKEY für das admin-Passwort ---
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password, isadmin) VALUES (?, ?, ?)",
        ("admin", SECRETKEY, 1),
    )
    conn.commit()

    # --- Migration: Falls die 'image'-Spalte in bestehenden DBs fehlt ---
    try:
        cur.execute("ALTER TABLE sessions ADD COLUMN image TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE session_log ADD COLUMN image TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    # Neu für Admin-Logs
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                admin_username TEXT NOT NULL,
                action TEXT NOT NULL,
                target_user TEXT,
                details TEXT
            )
        """)
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Migration Container-Defs
    try:
        cur.execute("ALTER TABLE container_defs ADD COLUMN env_vars TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE container_defs ADD COLUMN internal_port INTEGER DEFAULT 5800")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE container_defs ADD COLUMN cpu_limit TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE container_defs ADD COLUMN mem_limit TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE container_defs ADD COLUMN shm_size TEXT DEFAULT '2g'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE container_defs ADD COLUMN restart_policy TEXT DEFAULT 'no'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Wenn noch keine Container-Definition existiert, legen wir den Standard-Firefox an
    if cur.execute("SELECT COUNT(*) FROM container_defs").fetchone()[0] == 0:
        default_env = json.dumps([
            {"key": "KEEP_APP_RUNNING", "value": "1"},
            {"key": "FF_PREF_network.trr.mode", "value": "5"}
        ])
        cur.execute("""
            INSERT INTO container_defs (name, image, tag, is_default, internal_port, env_vars, shm_size, restart_policy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Firefox (Default)", "jlesage/firefox", "latest", 1, 5800, default_env, "2g", "no"))
        conn.commit()

    conn.close()


# ---------------------------------------------------------
# USERS
# ---------------------------------------------------------

def db_create_user(username: str, password_hash: str, isadmin: int = 0, team_id: int = None):
    with get_conn() as conn:
        try:
            if team_id is not None:
                conn.execute(
                    "INSERT INTO users (username, password, isadmin, team_id) VALUES (?, ?, ?, ?)",
                    (username, password_hash, isadmin, team_id),
                )
            else:
                conn.execute(
                    "INSERT INTO users (username, password, isadmin) VALUES (?, ?, ?)",
                    (username, password_hash, isadmin),
                )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def db_get_user_by_name(username: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

def db_get_user_by_id(uid: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

def db_update_user_password(uid: int, new_hash: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET password=? WHERE id=?", (new_hash, uid))
        conn.commit()

def db_delete_user(uid: int):
    with get_conn() as conn:
        user = conn.execute("SELECT isadmin FROM users WHERE id=?", (uid,)).fetchone()
        if user and user["isadmin"]:
            admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE isadmin=1").fetchone()[0]
            if admin_count <= 1:
                return False
        conn.execute("DELETE FROM users WHERE id=?", (uid,))
        conn.commit()
        return True

def db_update_user_admin(uid: int, isadmin: int):
    with get_conn() as conn:
        if not isadmin:
            admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE isadmin=1").fetchone()[0]
            if admin_count <= 1:
                return False
        conn.execute("UPDATE users SET isadmin=? WHERE id=?", (isadmin, uid))
        conn.commit()
        return True

def db_update_user_team(uid: int, team_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET team_id=? WHERE id=?", (team_id, uid))
        conn.commit()
        return True

def db_list_users():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT u.id, u.username, u.isadmin, u.team_id, t.name as team_name
            FROM users u
            LEFT JOIN teams t ON u.team_id = t.id
        """).fetchall()
        return [dict(r) for r in rows]

# ---------------------------------------------------------
# TEAMS
# ---------------------------------------------------------

def db_create_team(name: str):
    with get_conn() as conn:
        try:
            cur = conn.execute("INSERT INTO teams (name) VALUES (?)", (name,))
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

def db_list_teams():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM teams").fetchall()
        teams = []
        for r in rows:
            d = dict(r)
            users_count = conn.execute("SELECT COUNT(*) FROM users WHERE team_id=?", (d["id"],)).fetchone()[0]
            d["users_count"] = users_count
            admins = conn.execute("SELECT user_id FROM team_admins WHERE team_id=?", (d["id"],)).fetchall()
            d["admin_ids"] = [a["user_id"] for a in admins]
            teams.append(d)
        return teams

def db_get_team_by_id(team_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM teams WHERE id=?", (team_id,)).fetchone()

def db_update_team(team_id: int, name: str):
    with get_conn() as conn:
        try:
            conn.execute("UPDATE teams SET name=? WHERE id=?", (name, team_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def db_delete_team(team_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET team_id=NULL WHERE team_id=?", (team_id,))
        conn.execute("DELETE FROM teams WHERE id=?", (team_id,))
        conn.commit()
        return True

def db_add_team_admin(team_id: int, user_id: int):
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO team_admins (user_id, team_id) VALUES (?, ?)", (user_id, team_id)
            )
            conn.commit()
            return True
        except Exception:
            return False

def db_remove_team_admin(team_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM team_admins WHERE user_id=? AND team_id=?", (user_id, team_id))
        conn.commit()
        return True

def db_get_admin_teams(user_id: int):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT t.* FROM teams t
            JOIN team_admins ta ON t.id = ta.team_id
            WHERE ta.user_id=?
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------
def db_get_user_settings(user_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT settings FROM user_settings WHERE user_id=?", (user_id,)).fetchone()
        if row:
            try:
                return json.loads(row["settings"])
            except json.JSONDecodeError:
                return {}
        return {}

def db_update_user_settings(user_id: int, settings: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_settings (user_id, settings) VALUES (?, ?)",
            (user_id, json.dumps(settings)),
        )
        conn.commit()

# ---------------------------------------------------------
# SESSIONS
# ---------------------------------------------------------

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

def db_get_session_by_token(token: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()

def db_get_session_by_user(user_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM sessions WHERE user_id=?", (user_id,)).fetchone()

def db_get_timed_out_sessions(timeout_sec: int):
    cutoff = time.time() - timeout_sec
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM sessions WHERE last_seen < ?", (cutoff,)).fetchall()
        return [dict(r) for r in rows]

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
                 row["created_at"], ended_at, duration, row["image"])  # <--- HIER IST DIE KORREKTUR
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
                   LEFT JOIN users u ON s.user_id = u.id
                   WHERE s.user_id = ?""",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT s.session_id, s.username, s.container_name, s.container_ip,
                          s.last_seen, s.created_at, u.team_id, s.image
                   FROM sessions s
                   LEFT JOIN users u ON s.user_id = u.id"""
            ).fetchall()
        return [dict(r) for r in rows]

# ---------------------------------------------------------
# SESSION LOGS
# ---------------------------------------------------------

def db_get_session_logs(limit: int = 100, offset: int = 0, username: str = None):
    with get_conn() as conn:
        if username:
            query = """
                SELECT id, username, container_name, container_ip, started_at, ended_at, duration, image
                FROM session_log
                WHERE username LIKE ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """
            rows = conn.execute(query, (f"%{username}%", limit, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM session_log WHERE username LIKE ?", (f"%{username}%",)).fetchone()[0]
        else:
            query = """
                SELECT id, username, container_name, container_ip, started_at, ended_at, duration, image
                FROM session_log
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """
            rows = conn.execute(query, (limit, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM session_log").fetchone()[0]
        
        return {
            "total": total,
            "logs": [dict(r) for r in rows]
        }

# ---------------------------------------------------------
# ADMIN LOGS (NEU)
# ---------------------------------------------------------
def db_create_admin_log(admin_username: str, action: str, details: str, target_user: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO admin_logs (timestamp, admin_username, action, target_user, details) VALUES (?, ?, ?, ?, ?)",
            (time.time(), admin_username, action, target_user, details)
        )
        conn.commit()

def db_get_admin_logs(limit: int = 100, offset: int = 0):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM admin_logs ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM admin_logs").fetchone()[0]
        return {"total": total, "logs": [dict(r) for r in rows]}


# ---------------------------------------------------------
# CONTAINER DEFINITIONS
# ---------------------------------------------------------

def db_list_container_defs():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM container_defs").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("team_ids"):
                try:
                    d["team_ids"] = json.loads(d["team_ids"])
                except Exception:
                    d["team_ids"] = []
            else:
                d["team_ids"] = []

            if d.get("env_vars"):
                try:
                    d["env_vars"] = json.loads(d["env_vars"])
                except Exception:
                    d["env_vars"] = []
            else:
                d["env_vars"] = []
            result.append(d)
        return result

def db_get_container_def(def_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM container_defs WHERE id=?", (def_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["team_ids"] = json.loads(d["team_ids"]) if d.get("team_ids") else []
        d["env_vars"] = json.loads(d["env_vars"]) if d.get("env_vars") else []
        return d

def db_get_default_container_def():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM container_defs WHERE is_default=1 LIMIT 1").fetchone()
        if not row:
            row = conn.execute("SELECT * FROM container_defs LIMIT 1").fetchone()
        if not row:
            return None
        d = dict(row)
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
            (name, image, tag, is_default, team_ids, internal_port, env_vars, cpu_limit, mem_limit, shm_size, restart_policy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["name"],
            data["image"],
            data["tag"],
            1 if data.get("is_default") else 0,
            team_ids_str,
            data.get("internal_port", 5800),
            env_vars_str,
            data.get("cpu_limit"),
            data.get("mem_limit"),
            data.get("shm_size", "2g"),
            data.get("restart_policy", "no")
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
            SET name=?, image=?, tag=?, is_default=?, team_ids=?, internal_port=?, env_vars=?, cpu_limit=?, mem_limit=?, shm_size=?, restart_policy=?
            WHERE id=?
        """, (
            data["name"],
            data["image"],
            data["tag"],
            1 if data.get("is_default") else 0,
            team_ids_str,
            data.get("internal_port", 5800),
            env_vars_str,
            data.get("cpu_limit"),
            data.get("mem_limit"),
            data.get("shm_size", "2g"),
            data.get("restart_policy", "no"),
            def_id
        ))
        conn.commit()

def db_delete_container_def(def_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM container_defs WHERE id=?", (def_id,))
        conn.commit()

def db_set_default_container_def(def_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE container_defs SET is_default=0")
        conn.execute("UPDATE container_defs SET is_default=1 WHERE id=?", (def_id,))
        conn.commit()

def db_get_allowed_container_defs(user_team_id: int = None):
    all_defs = db_list_container_defs()
    allowed = []
    for d in all_defs:
        if not d.get("team_ids"):
            allowed.append(d)
        else:
            if user_team_id and user_team_id in d["team_ids"]:
                allowed.append(d)
    return allowed
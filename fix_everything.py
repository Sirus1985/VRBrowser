import urllib.request
import re

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8")

print("Repariere database.py...")
db = fetch("https://raw.githubusercontent.com/Sirus1985/VRBrowser/multiversion/database.py")
db = db.replace(
    '    try:\n        cur.execute("ALTER TABLE sessions ADD COLUMN container_ip TEXT")\n    except sqlite3.OperationalError:\n        pass',
    '    try:\n        cur.execute("ALTER TABLE sessions ADD COLUMN container_ip TEXT")\n    except sqlite3.OperationalError:\n        pass\n    try:\n        cur.execute("ALTER TABLE sessions ADD COLUMN image TEXT")\n    except sqlite3.OperationalError:\n        pass'
)
db = db.replace(
    '        CREATE TABLE IF NOT EXISTS session_log (\n            id             INTEGER PRIMARY KEY AUTOINCREMENT,\n            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n            username       TEXT NOT NULL,\n            container_name TEXT NOT NULL,\n            container_ip   TEXT,\n            started_at     REAL NOT NULL,\n            ended_at       REAL NOT NULL,\n            duration       REAL NOT NULL\n        )\n    """',
    '        CREATE TABLE IF NOT EXISTS session_log (\n            id             INTEGER PRIMARY KEY AUTOINCREMENT,\n            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n            username       TEXT NOT NULL,\n            container_name TEXT NOT NULL,\n            container_ip   TEXT,\n            started_at     REAL NOT NULL,\n            ended_at       REAL NOT NULL,\n            duration       REAL NOT NULL,\n            image          TEXT\n        )\n    """\n    try:\n        cur.execute("ALTER TABLE session_log ADD COLUMN image TEXT")\n    except sqlite3.OperationalError:\n        pass'
)
db = db.replace(
    'def db_create_session(session_id: str, user_id: int, username: str,\n                      container_name: str, token: str, container_ip: str = None):\n    now = time.time()\n    with get_conn() as conn:\n        conn.execute(\n            """INSERT OR REPLACE INTO sessions\n               (session_id, user_id, username, container_name, container_ip, token, last_seen, created_at)\n               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",\n            (session_id, user_id, username, container_name, container_ip, token, now, now)\n        )',
    'def db_create_session(session_id: str, user_id: int, username: str,\n                      container_name: str, token: str, container_ip: str = None, image: str = None):\n    now = time.time()\n    with get_conn() as conn:\n        conn.execute(\n            """INSERT OR REPLACE INTO sessions\n               (session_id, user_id, username, container_name, container_ip, token, last_seen, created_at, image)\n               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",\n            (session_id, user_id, username, container_name, container_ip, token, now, now, image)\n        )'
)
db = db.replace(
    'def db_close_session(session_id: str):\n    """Archiviert eine Sitzung in session_log und löscht sie aus der aktiven Tabelle."""\n    with get_conn() as conn:\n        row = conn.execute(\n            "SELECT user_id, username, container_name, container_ip, created_at FROM sessions WHERE session_id=?",\n            (session_id,)\n        ).fetchone()\n        if row:\n            ended_at = time.time()\n            duration = ended_at - row["created_at"]\n            conn.execute(\n                """INSERT INTO session_log\n                   (user_id, username, container_name, container_ip, started_at, ended_at, duration)\n                   VALUES (?, ?, ?, ?, ?, ?, ?)""",\n                (row["user_id"], row["username"], row["container_name"], row["container_ip"],\n                 row["created_at"], ended_at, duration)\n            )',
    'def db_close_session(session_id: str):\n    """Archiviert eine Sitzung in session_log und löscht sie aus der aktiven Tabelle."""\n    with get_conn() as conn:\n        row = conn.execute(\n            "SELECT user_id, username, container_name, container_ip, created_at, image FROM sessions WHERE session_id=?",\n            (session_id,)\n        ).fetchone()\n        if row:\n            ended_at = time.time()\n            duration = ended_at - row["created_at"]\n            conn.execute(\n                """INSERT INTO session_log\n                   (user_id, username, container_name, container_ip, started_at, ended_at, duration, image)\n                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",\n                (row["user_id"], row["username"], row["container_name"], row["container_ip"],\n                 row["created_at"], ended_at, duration, row["image"])\n            )'
)
db = re.sub(r"(SELECT s\.session_id, s\.username, s\.container_name, s\.container_ip,\n\s+s\.last_seen, s\.created_at, u\.team_id)", r"SELECT s.session_id, s.username, s.container_name, s.container_ip,\n                      s.last_seen, s.created_at, u.team_id, s.image", db)
db = db.replace("SELECT id, container_name, container_ip, started_at, ended_at, duration", "SELECT id, container_name, container_ip, started_at, ended_at, duration, image")
db = db.replace("SELECT id, username, user_id, container_name, container_ip,\n                   started_at, ended_at, duration", "SELECT id, username, user_id, container_name, container_ip,\n                   started_at, ended_at, duration, image")
with open("database.py", "w", encoding="utf-8") as f: f.write(db)

print("Repariere session_manager.py...")
sm = fetch("https://raw.githubusercontent.com/Sirus1985/VRBrowser/multiversion/session_manager.py")
sm = sm.replace(
    'def register_session(session_id: str, user_id: int, username: str, container_name: str, token: str, container_ip: str = None): \n    db_create_session(session_id, user_id, username, container_name, token, container_ip)',
    'def register_session(session_id: str, user_id: int, username: str, container_name: str, token: str, container_ip: str = None, image: str = None): \n    db_create_session(session_id, user_id, username, container_name, token, container_ip, image)'
)
with open("session_manager.py", "w", encoding="utf-8") as f: f.write(sm)

print("Repariere routes/sessions.py...")
rs = fetch("https://raw.githubusercontent.com/Sirus1985/VRBrowser/multiversion/routes/sessions.py")
rs = rs.replace(
    '        host_id = existing["container_name"].replace("vbrowser-", "")\n        url = f"https://{host_id}.{BASE_DOMAIN}/"\n        response = JSONResponse({\n            "status": "resumed",\n            "url": url,\n            "session_id": existing["session_id"],\n            "container_name": existing["container_name"],',
    '        host_id = existing["container_name"].replace("vbrowser-", "")\n        url = f"https://{host_id}.{BASE_DOMAIN}/" if BASE_DOMAIN else f"http://{host_id}.localhost/"\n        response = JSONResponse({\n            "status": "resumed",\n            "url": url,\n            "session_id": existing["session_id"],\n            "container_name": existing["container_name"],'
)
rs = rs.replace(
    '    register_session(session_id, user_id, username, container.name, token, container_ip)\n\n    # Wir basteln uns eine fiktive URL als Response. Das Frontend braucht eigentlich nur Token & Session-ID.',
    '    register_session(session_id, user_id, username, container.name, token, container_ip, container_def.get("image"))\n\n    host_id = container.name.replace("vbrowser-", "")\n    url = f"https://{host_id}.{BASE_DOMAIN}/" if BASE_DOMAIN else f"http://{host_id}.localhost/"'
)
rs = rs.replace(
    '        "url": f"https://{BASE_DOMAIN}/browser/{session_id}/",',
    '        "url": url,'
)

rs = rs.replace('current_user.get("username", "unknown")', 'current_user.get("sub", "unknown")')
rs = rs.replace('current_user.get("id", 0)', 'current_user.get("uid", 0)')

os.makedirs("routes", exist_ok=True)
with open("routes/sessions.py", "w", encoding="utf-8") as f: f.write(rs)
print("Fertig!")

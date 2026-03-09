#!/usr/bin/env python3
import logging
import os
import sqlite3
import time
from typing import Optional
from docker import DockerClient
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn

# ----------------------------- Config -----------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))

# IMPORTANT: In production set this via env var and rotate it.
SECRETKEY = os.getenv("SECRETKEY", "super-secret-key-change-me")

# IMPORTANT: For persistence, set this to a mounted path
DBPATH = os.getenv("DBPATH", ".data/browser.db")

DOCKERHOST = os.getenv("DOCKERHOST", "unix:///var/run/docker.sock")
DOCKERIMAGE = os.getenv("DOCKERIMAGE", "jlesage/firefox:latest")

# NEU: Traefik/Reverse Proxy Config
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "vbrowser.localhost")
PROXY_NETWORK = os.getenv("PROXY_NETWORK", "vbrowser_proxy")
TRAEFIK_ENTRYPOINT = os.getenv("TRAEFIK_ENTRYPOINT", "websecure")
USE_TLS = os.getenv("USE_TLS", "false").lower() == "true"
CERT_RESOLVER = os.getenv("CERT_RESOLVER", "")  # z.B. "letsencrypt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vbrowser")

app = FastAPI()
security = HTTPBearer()

# ----------------------------- Models -----------------------------
class UserLogin(BaseModel):
    username: str
    password: str

class NewUser(BaseModel):
    username: str
    password: str
    isadmin: bool = False

# ----------------------------- DB -----------------------------
def ensuredirfordb():
    dbdir = os.path.dirname(DBPATH)
    if dbdir:
        os.makedirs(dbdir, exist_ok=True)

def initdb():
    ensuredirfordb()
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    
    # Base table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Migration: add isadmin if missing
    try:
        cur.execute("ALTER TABLE users ADD COLUMN isadmin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    # Bootstrap: ensure first admin exists
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password, isadmin) VALUES (?, ?, ?)",
        ("testuser", "testpass", 1),
    )
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password, isadmin) VALUES (?, ?, ?)",
        ("user2", "pass2", 0),
    )
    
    conn.commit()
    conn.close()
    logger.info(f"DB initialized at {DBPATH}")

def dbgetuser(username: str, password: str):
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, isadmin FROM users WHERE username=? AND password=?",
        (username, password),
    )
    row = cur.fetchone()
    conn.close()
    return row

def dblistusers():
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, isadmin FROM users ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "isadmin": bool(r[2])} for r in rows]

def dbadduser(username: str, password: str, isadmin: bool):
    conn = sqlite3.connect(DBPATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, isadmin) VALUES (?, ?, ?)",
            (username, password, 1 if isadmin else 0),
        )
        conn.commit()
    finally:
        conn.close()

def dbdeleteuser(userid: int):
    conn = sqlite3.connect(DBPATH)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=?", (userid,))
        conn.commit()
    finally:
        conn.close()

def dbgetuserbyid(userid: int):
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, isadmin FROM users WHERE id=?", (userid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "username": row[1], "isadmin": bool(row[2])}

# ----------------------------- Auth (JWT) -----------------------------
def createtoken(uid: int, username: str, isadmin: bool) -> str:
    import jwt
    payload = {
        "uid": uid,
        "sub": username,
        "admin": bool(isadmin),
        "exp": time.time() + 3600,
    }
    return jwt.encode(payload, SECRETKEY, algorithm="HS256")

def getcurrentuser(creds: HTTPAuthorizationCredentials = Depends(security)):
    import jwt
    try:
        return jwt.decode(creds.credentials, SECRETKEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(401, "Invalid token")

def requireadmin(user: dict = Depends(getcurrentuser)):
    if not user.get("admin"):
        raise HTTPException(403, "Admin only")
    return user

# ----------------------------- Docker manager -----------------------------
class DockerManager:
    def __init__(self):
        self.client = DockerClient(base_url=DOCKERHOST)

    def containername(self, username: str) -> str:
        return f"vbrowser-{username}"

    def stopcontainer(self, username: str):
        name = self.containername(username)
        try:
            c = self.client.containers.get(name)
            c.remove(force=True)
            logger.info(f"Removed container {name}")
        except Exception:
            pass

    def createcontainer(self, userid: int, username: str) -> str:
        """
        NEU: Container ohne Host-Port, nur im Proxy-Netzwerk mit Traefik-Labels.
        Gibt die Browser-URL zurück (kein Port mehr).
        """
        name = self.containername(username)
        
        # Stoppe alte Container falls vorhanden
        self.stopcontainer(username)
        
        # Subdomain für diesen User
        host = f"{username}.{BASE_DOMAIN}"
        
        # Traefik Router/Service Namen (müssen unique sein)
        router = f"vbrowser-user-{userid}"
        service = f"vbrowser-user-{userid}"
        
        # Traefik Labels
        labels = {
            "traefik.enable": "true",
            f"traefik.http.routers.{router}.rule": f"Host(`{host}`)",
            f"traefik.http.routers.{router}.entrypoints": TRAEFIK_ENTRYPOINT,
            f"traefik.http.services.{service}.loadbalancer.server.port": "5800",
        }
        
        # TLS aktivieren (falls USE_TLS=true)
        if USE_TLS:
            labels[f"traefik.http.routers.{router}.tls"] = "true"
            if CERT_RESOLVER:
                labels[f"traefik.http.routers.{router}.tls.certresolver"] = CERT_RESOLVER
        
        try:
            logger.info(f"Starting container {name} for {host}")
            self.client.containers.run(
                DOCKERIMAGE,
                name=name,
                detach=True,
                shm_size="2g",
                network=PROXY_NETWORK,
                labels=labels,
                environment={
                    "KEEP_APP_RUNNING": "1",
                    "FF_OPEN_URL": "https://google.com",
                },
            )
            
            # Gebe die Browser-URL zurück (mit/ohne TLS)
            protocol = "https" if USE_TLS else "http"
            url = f"{protocol}://{host}/"
            
            logger.info(f"Container {name} started successfully at {url}")
            return url
            
        except Exception as e:
            logger.error(f"Container start failed: {e}")
            raise HTTPException(500, f"Container start failed: {e}")

dockermgr = DockerManager()

# ----------------------------- API -----------------------------
@app.on_event("startup")
def startup():
    initdb()

@app.post("/api/login")
def login(u: UserLogin):
    row = dbgetuser(u.username, u.password)
    if not row:
        raise HTTPException(401, "Login failed")
    uid, username, isadmin = row
    return {
        "token": createtoken(uid, username, bool(isadmin)),
        "isadmin": bool(isadmin),
    }

@app.get("/api/users")
def listusers(admin: dict = Depends(requireadmin)):
    return dblistusers()

@app.post("/api/users")
def adduser(n: NewUser, admin: dict = Depends(requireadmin)):
    try:
        dbadduser(n.username, n.password, n.isadmin)
    except sqlite3.IntegrityError:
        raise HTTPException(400, "User exists")
    return {"status": "ok"}

@app.delete("/api/users/{userid}")
def deleteuser(userid: int, admin: dict = Depends(requireadmin)):
    u = dbgetuserbyid(userid)
    if not u:
        return {"status": "ok"}
    
    # Protect built-in admin
    if u["username"] == "testuser":
        raise HTTPException(400, "Default admin cannot be deleted")
    
    # Stop container if running
    dockermgr.stopcontainer(u["username"])
    
    dbdeleteuser(userid)
    return {"status": "ok"}

@app.post("/api/session/start")
def startsession(user: dict = Depends(getcurrentuser)):
    url = dockermgr.createcontainer(user["uid"], user["sub"])
    return {"status": "started", "url": url}

@app.post("/api/session/stop")
def stopsession(user: dict = Depends(getcurrentuser)):
    dockermgr.stopcontainer(user["sub"])
    return {"status": "stopped"}

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "dbpath": DBPATH,
        "dockerimage": DOCKERIMAGE,
        "base_domain": BASE_DOMAIN,
        "proxy_network": PROXY_NETWORK,
    }

# ----------------------------- Frontend -----------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>VBrowser</title>
    <style>
        :root {
            --bg: #1e1e1e;
            --panel: #252526;
            --border: #333;
            --accent: #0e639c;
            --text: #ccc;
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, system-ui, sans-serif;
            display: flex;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        
        #sidebar {
            width: 280px;
            background: var(--panel);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            border-right: 1px solid var(--border);
        }
        
        h3 {
            margin: 0 0 6px 0;
            color: #fff;
            font-weight: 600;
        }
        
        input {
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #555;
            background: #3c3c3c;
            color: #fff;
            width: 100%;
        }
        
        button {
            padding: 10px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            background: var(--accent);
            color: #fff;
            width: 100%;
            font-size: 14px;
            transition: opacity 0.2s;
        }
        
        button:hover {
            opacity: 0.9;
        }
        
        button.secondary {
            background: #3a3d41;
            border: 1px solid #555;
        }
        
        button.danger {
            background: #8b2010;
        }
        
        .hidden {
            display: none !important;
        }
        
        #content {
            flex: 1;
            position: relative;
            background: #111;
        }
        
        iframe {
            width: 100%;
            height: 100%;
            border: none;
            display: none;
        }
        
        #placeholder {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #555;
            font-size: 16px;
        }
        
        .admin-panel {
            background: #2d2d2d;
            padding: 12px;
            border: 1px solid #444;
            border-radius: 8px;
            margin-top: 8px;
        }
        
        .user-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #333;
            padding: 8px;
            border-radius: 6px;
            margin-bottom: 6px;
        }
        
        .badge {
            background: #dda108;
            color: #000;
            padding: 2px 6px;
            border-radius: 999px;
            font-size: 12px;
            margin-left: 6px;
        }
        
        #status {
            margin-top: auto;
            font-size: 13px;
            color: #888;
            border-top: 1px solid var(--border);
            padding-top: 10px;
        }
        
        label {
            display: flex;
            gap: 8px;
            align-items: center;
            font-size: 13px;
            margin-bottom: 10px;
        }
        
        input[type="checkbox"] {
            width: auto;
        }
        
        hr {
            border: none;
            border-top: 1px solid #444;
            margin: 14px 0;
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <h3>VBrowser</h3>
        
        <!-- Login Form -->
        <div id="loginForm">
            <input id="username" placeholder="Benutzername" autocomplete="username">
            <input id="password" placeholder="Passwort" type="password" autocomplete="current-password">
            <button onclick="doLogin()">Einloggen</button>
        </div>
        
        <!-- Session Controls -->
        <div id="sessionControls" class="hidden">
            <button onclick="startSession()" style="background: #2da44e">Session starten</button>
            <button onclick="stopSession()" class="danger">Session beenden</button>
        </div>
        
        <!-- Admin Toggle -->
        <div id="adminToggle" class="hidden">
            <hr>
            <button class="secondary" onclick="toggleAdmin()">Benutzerverwaltung</button>
            
            <div id="adminArea" class="hidden admin-panel">
                <div id="userList"></div>
                <hr>
                <input id="newUsername" placeholder="Neuer Benutzer">
                <input id="newPassword" placeholder="Passwort" type="password">
                <label>
                    <input id="newIsAdmin" type="checkbox">
                    Admin
                </label>
                <button class="secondary" onclick="addUser()">User anlegen</button>
            </div>
        </div>
        
        <button class="secondary" onclick="logout()">Logout</button>
        
        <div id="status">Bereit</div>
    </div>
    
    <div id="content">
        <div id="placeholder">Bitte einloggen...</div>
        <iframe id="browserFrame"></iframe>
    </div>
    
    <script>
        let token = localStorage.getItem("token");
        let isAdmin = localStorage.getItem("isAdmin") === "true";
        
        if (token) {
            showSessionUI();
        }
        
        function setStatus(msg, isError = false) {
            const el = document.getElementById("status");
            el.textContent = msg;
            el.style.color = isError ? "#f66" : "#888";
        }
        
        async function doLogin() {
            const u = document.getElementById("username").value;
            const p = document.getElementById("password").value;
            
            setStatus("Logge ein...");
            
            try {
                const res = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username: u, password: p })
                });
                
                if (!res.ok) throw new Error("Login fehlgeschlagen");
                
                const data = await res.json();
                token = data.token;
                isAdmin = data.isadmin;
                
                localStorage.setItem("token", token);
                localStorage.setItem("isAdmin", String(isAdmin));
                
                showSessionUI();
                setStatus("Eingeloggt");
            } catch (e) {
                setStatus(e.message, true);
            }
        }
        
        function showSessionUI() {
            document.getElementById("loginForm").classList.add("hidden");
            document.getElementById("sessionControls").classList.remove("hidden");
            document.getElementById("placeholder").textContent = "Bereit zum Starten...";
            
            if (isAdmin) {
                document.getElementById("adminToggle").classList.remove("hidden");
            }
        }
        
        async function startSession() {
            setStatus("Starte Container...");
            
            try {
                const res = await fetch("/api/session/start", {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${token}` }
                });
                
                if (!res.ok) throw new Error("Session Start fehlgeschlagen");
                
                const data = await res.json();
                setStatus(`Lade Browser von ${data.url} ...`);
                
                // Warte kurz, damit Container Zeit hat hochzufahren
                setTimeout(() => {
                    const frame = document.getElementById("browserFrame");
                    frame.src = data.url;
                    frame.style.display = "block";
                    document.getElementById("placeholder").style.display = "none";
                    setStatus("Browser läuft");
                }, 3000);
            } catch (e) {
                setStatus(e.message, true);
            }
        }
        
        async function stopSession() {
            await fetch("/api/session/stop", {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });
            
            document.getElementById("browserFrame").src = "";
            document.getElementById("browserFrame").style.display = "none";
            document.getElementById("placeholder").style.display = "flex";
            document.getElementById("placeholder").textContent = "Session beendet";
            
            setStatus("Session gestoppt");
        }
        
        function toggleAdmin() {
            const area = document.getElementById("adminArea");
            area.classList.toggle("hidden");
            
            if (!area.classList.contains("hidden")) {
                loadUsers();
            }
        }
        
        async function loadUsers() {
            const res = await fetch("/api/users", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const users = await res.json();
            
            document.getElementById("userList").innerHTML = users.map(u => `
                <div class="user-item">
                    <span>
                        ${u.username}
                        ${u.isadmin ? '<span class="badge">ADMIN</span>' : ''}
                    </span>
                    ${u.username !== "testuser" ? 
                        `<button class="danger" style="width:auto; padding:6px 10px" onclick="deleteUser(${u.id})">X</button>` 
                        : ''}
                </div>
            `).join("");
        }
        
        async function addUser() {
            const u = document.getElementById("newUsername").value;
            const p = document.getElementById("newPassword").value;
            const a = document.getElementById("newIsAdmin").checked;
            
            if (!u || !p) {
                return setStatus("Bitte Benutzer/Passwort eingeben", true);
            }
            
            const res = await fetch("/api/users", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ username: u, password: p, isadmin: a })
            });
            
            if (!res.ok) {
                return setStatus("User konnte nicht angelegt werden", true);
            }
            
            document.getElementById("newUsername").value = "";
            document.getElementById("newPassword").value = "";
            document.getElementById("newIsAdmin").checked = false;
            
            loadUsers();
        }
        
        async function deleteUser(id) {
            if (!confirm("User wirklich löschen?")) return;
            
            const res = await fetch(`/api/users/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });
            
            if (!res.ok) {
                return setStatus("User konnte nicht gelöscht werden", true);
            }
            
            loadUsers();
        }
        
        function logout() {
            localStorage.clear();
            location.reload();
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

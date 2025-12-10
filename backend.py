#!/usr/bin/env python3
"""
Virtual Browser Server - FastAPI Backend
Sichere Browser-Virtualisierung für Intranet-Nutzer
"""

import os
import json
import sqlite3
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import asyncio
import subprocess

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
import docker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-" + secrets.token_hex(16))
DB_PATH = os.getenv("DB_PATH", "./data/browser.db")
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "virtual-browser:latest")
LOG_DIR = os.getenv("LOG_DIR", "./data/logs")
NOVNC_PORT_START = int(os.getenv("NOVNC_PORT_START", "6080"))
CONTAINER_RAM = os.getenv("CONTAINER_RAM", "768m")
CONTAINER_CPUS = os.getenv("CONTAINER_CPUS", "0.5")
LOGS_DIR = Path(LOG_DIR)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

def init_db():
    """Initialize SQLite database"""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            container_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # URL logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# ============================================================================
# MODELS
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    vnc_url: str
    expires_in: int

class UserCreate(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    created_at: str

# ============================================================================
# DOCKER CLIENT
# ============================================================================

class DockerManager:
    def __init__(self):
        """Initialize Docker client with explicit socket path"""
        try:
            # Method 1: Direct socket path (für Docker-in-Docker)
            self.client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
            
            # Teste ob Verbindung funktioniert
            self.client.ping()
            print("✓ Docker client initialized via socket")
            
        except Exception as e:
            print(f"⚠️  Docker socket failed: {e}")
            try:
                # Method 2: Fallback - from_env() 
                self.client = docker.from_env()
                print("✓ Docker client initialized via from_env()")
            except Exception as e2:
                print(f"✗ Docker connection failed: {e2}")
                self.client = None

    def is_available(self):
        """Check if Docker is available"""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

    
    async def start_browser_container(self, user_id: int, username: str, port: int) -> str:
        """Start a new browser container for user"""
        container_name = f"vbrowser-{user_id}-{username}"
        
        try:
            # Check if container already exists
            try:
                existing = self.client.containers.get(container_name)
                existing.stop()
                existing.remove()
                logger.info(f"Removed existing container: {container_name}")
            except docker.errors.NotFound:
                pass
            
            # Start new container
            container = self.client.containers.run(
                DOCKER_IMAGE,
                name=container_name,
                detach=True,
                ports={'6080/tcp': port},
                environment={
                    'USER_ID': str(user_id),
                    'USERNAME': username,
                },
                volumes={
                    LOGS_DIR: {'bind': '/app/logs', 'mode': 'rw'}
                },
                mem_limit=CONTAINER_RAM,
                cpus=float(CONTAINER_CPUS),
                network_mode='bridge',
                remove=False
            )
            
            logger.info(f"Started container {container_name} on port {port}")
            return container.id
        
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise HTTPException(status_code=500, detail=f"Container start failed: {str(e)}")
    
    async def stop_container(self, container_id: str):
        """Stop and remove a container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            logger.info(f"Stopped container: {container_id}")
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")

docker_manager = DockerManager()

# ============================================================================
# AUTH UTILITIES
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_jwt_token(user_id: int, username: str, expires_in_hours: int = 24) -> tuple[str, datetime]:
    """Create JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    return token, expires_at

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Virtual Browser Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    init_db()
    # Create default user (testuser / testpass)
    try:
        create_user("testuser", "testpass")
    except:
        pass
    logger.info("Virtual Browser Server started")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Virtual Browser Server stopped")

# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

def create_user(username: str, password: str) -> int:
    """Create a new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        logger.info(f"Created user: {username}")
        return user_id
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

@app.post("/api/register")
async def register(request: UserCreate):
    """Register a new user"""
    if len(request.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    user_id = create_user(request.username, request.password)
    return {"message": "User created successfully", "user_id": user_id}

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login user and create session"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify credentials
    password_hash = hash_password(request.password)
    cursor.execute(
        "SELECT id FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
        (request.username, password_hash)
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = user[0]
    
    # Check for existing active session
    cursor.execute(
        "SELECT id, container_id FROM sessions WHERE user_id = ? AND is_active = 1 AND expires_at > datetime('now')",
        (user_id,)
    )
    existing_session = cursor.fetchone()
    
    if existing_session:
        # Reuse existing session
        session_id = existing_session[0]
        cursor.execute("SELECT token FROM sessions WHERE id = ?", (session_id,))
        token = cursor.fetchone()[0]
        conn.close()
        
        vnc_port = NOVNC_PORT_START + user_id
        vnc_url = f"http://{os.getenv('HOST_IP', 'localhost')}:{vnc_port}/vnc.html"
        
        return LoginResponse(
            token=token,
            vnc_url=vnc_url,
            expires_in=86400
        )
    
    # Create new token and session
    token, expires_at = create_jwt_token(user_id, request.username)
    
    # Allocate VNC port
    vnc_port = NOVNC_PORT_START + user_id
    
    # Start container
    try:
        container_id = await docker_manager.start_browser_container(user_id, request.username, vnc_port)
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to start browser: {str(e)}")
    
    # Store session
    cursor.execute(
        """INSERT INTO sessions (user_id, token, container_id, expires_at, is_active)
           VALUES (?, ?, ?, ?, 1)""",
        (user_id, token, container_id, expires_at)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"User {request.username} logged in, container {container_id[:12]} started")
    
    vnc_url = f"http://{os.getenv('HOST_IP', 'localhost')}:{vnc_port}/vnc.html"
    
    return LoginResponse(
        token=token,
        vnc_url=vnc_url,
        expires_in=86400
    )

@app.post("/api/logout")
async def logout(token: str):
    """Logout user and stop container"""
    try:
        payload = verify_jwt_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    # Get session
    cursor.execute(
        "SELECT id, container_id FROM sessions WHERE user_id = ? AND is_active = 1",
        (user_id,)
    )
    session = cursor.fetchone()
    
    if session:
        container_id = session[1]
        # Stop container
        if container_id:
            await docker_manager.stop_container(container_id)
        
        # Mark session as inactive
        cursor.execute(
            "UPDATE sessions SET is_active = 0 WHERE id = ?",
            (session[0],)
        )
        conn.commit()
    
    conn.close()
    logger.info(f"User {user_id} logged out")
    
    return {"message": "Logged out successfully"}

@app.get("/api/user")
async def get_user(token: str):
    """Get current user info"""
    try:
        payload = verify_jwt_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user[0],
        "username": user[1],
        "created_at": user[2]
    }

# ============================================================================
# LOGGING ENDPOINTS
# ============================================================================

@app.get("/api/logs/{user_id}")
async def get_user_logs(user_id: int, token: str, days: int = 1):
    """Get URL logs for user"""
    try:
        payload = verify_jwt_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Only allow users to view their own logs
    if payload['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get logs from last N days
    cursor.execute(
        """SELECT url, timestamp FROM url_logs 
           WHERE user_id = ? AND timestamp > datetime('now', '-' || ? || ' days')
           ORDER BY timestamp DESC""",
        (user_id, days)
    )
    logs = cursor.fetchall()
    conn.close()
    
    return {
        "user_id": user_id,
        "logs": [{"url": log[0], "timestamp": log[1]} for log in logs]
    }

# ============================================================================
# STATIC FILES & FRONTEND
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve login page"""
    try:
        with open("frontend/index.html", "r") as f:
            return f.read()
    except:
        return """
        <html>
        <body>
            <h1>Virtual Browser Server</h1>
            <p>Frontend not found. Make sure frontend/index.html exists.</p>
        </body>
        </html>
        """

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "ok"}

# ============================================================================
# CLEANUP TASK (runs every hour)
# ============================================================================

async def cleanup_expired_sessions():
    """Remove expired sessions and stop containers"""
    while True:
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Find expired sessions
            cursor.execute(
                """SELECT id, container_id FROM sessions 
                   WHERE is_active = 1 AND expires_at < datetime('now')"""
            )
            expired = cursor.fetchall()
            
            for session_id, container_id in expired:
                if container_id:
                    await docker_manager.stop_container(container_id)
                cursor.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (session_id,))
                logger.info(f"Cleaned up expired session {session_id}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        # Run every hour
        await asyncio.sleep(3600)

# Start cleanup task
@app.on_event("startup")
async def start_cleanup():
    asyncio.create_task(cleanup_expired_sessions())

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)

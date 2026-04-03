import logging
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from config import HOST, PORT
from database import initdb
from routes.login import router as login_router
from routes.users import router as users_router
from routes.teams import router as teams_router
from routes.sessions import router as sessions_router
from routes.admin_logging import router as admin_logging_router
from routes.containers import router as containers_admin_router
from routes.containers import user_router as containers_user_router
from session_manager import cleanup_loop
from frontend import get_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="VBrowser")

app.include_router(login_router)
app.include_router(users_router)
app.include_router(teams_router)
app.include_router(sessions_router)
app.include_router(admin_logging_router)
app.include_router(containers_admin_router)
app.include_router(containers_user_router)


@app.on_event("startup")
def startup():
    initdb()
    threading.Thread(target=cleanup_loop, daemon=True).start()


@app.get("/", response_class=HTMLResponse)
def index():
    return get_html()


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
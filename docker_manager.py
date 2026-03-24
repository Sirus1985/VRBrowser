import logging
import os
import shutil
from fastapi import HTTPException
from docker import DockerClient
from config import (
    DOCKERHOST, DOCKERIMAGE, BASE_DOMAIN, PROXY_NETWORK,
    TRAEFIK_ENTRYPOINT, USE_TLS, CERT_RESOLVER, PROFILES_BASE, BROWSER_DNS 
)

logger = logging.getLogger("vbrowser")


# ──────────────────────────────────────────────
# Seccomp-Hilfsfunktionen
# ──────────────────────────────────────────────

def _parse_csv(value: str) -> list[str]:
    return [item.strip().lower() for item in str(value).split(",") if item.strip()]

def _env_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

def build_security_opt(image_name: str) -> list[str] | None:
    mode    = os.getenv("BROWSER_SECCOMP_MODE", "off").strip().lower()
    profile = os.getenv("BROWSER_SECCOMP_PROFILE", "/opt/vbrowser/seccomp_profile.json").strip()
    allowed = _parse_csv(os.getenv("BROWSER_SECCOMP_IMAGES", "jlesage/firefox"))
    all_img = _env_bool(os.getenv("BROWSER_SECCOMP_ALL_IMAGES", "false"))

    image_base = image_name.strip().lower().split(":")[0]
    if not all_img and image_base not in allowed:
        return None

    if mode in {"", "off", "none", "false", "0"}:
        return None

    if mode == "unconfined":
        return ["seccomp:unconfined"]

    if mode == "profile":
        if not os.path.isfile(profile):
            logger.warning(f"Seccomp-Profil nicht gefunden: {profile}")
            return None
        return [f"seccomp:{profile}"]  # ← : statt =

    raise ValueError(f"Ungültiger BROWSER_SECCOMP_MODE: '{mode}'")



# ──────────────────────────────────────────────
# DockerManager
# ──────────────────────────────────────────────

class DockerManager:
    def __init__(self):
        self.client = DockerClient(base_url=DOCKERHOST)

    def get_profile_path(self, username: str) -> str:
        path = os.path.join(PROFILES_BASE, username)
        os.makedirs(path, exist_ok=True)
        return path

    def reset_profile(self, username: str):
        path = os.path.join(PROFILES_BASE, username)
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.info(f"Profile reset for user {username}")
        else:
            logger.info(f"No profile found for user {username}, nothing to reset")

    def stop_container(self, container_name: str):
        try:
            c = self.client.containers.get(container_name)
            c.remove(force=True)
            logger.info(f"Removed container {container_name}")
        except Exception as e:
            logger.warning(f"Could not remove container {container_name}: {e}")

    def is_container_running(self, container_name: str) -> bool:
        try:
            c = self.client.containers.get(container_name)
            return c.status == "running"
        except Exception:
            return False


    def create_container(self, userid: int, username: str, container_name: str, host_id: str) -> str:
        self.stop_container(container_name)
        profile_path = self.get_profile_path(username)
        host    = f"{host_id}.{BASE_DOMAIN}"
        router  = f"vbrowser-user-{userid}"
        service = f"vbrowser-user-{userid}"

        labels = {
            "traefik.enable": "true",
            f"traefik.http.routers.{router}.rule": f"Host(`{host}`)",
            f"traefik.http.routers.{router}.entrypoints": TRAEFIK_ENTRYPOINT,
            f"traefik.http.routers.{router}.middlewares": "vbrowser-auth@file",
            f"traefik.http.routers.{router}.priority": "10",
            f"traefik.http.services.{service}.loadbalancer.server.port": "5800",
            f"traefik.http.routers.{router}-setcookie.rule": f"Host(`{host}`) && Path(`/auth/set-cookie`)",
            f"traefik.http.routers.{router}-setcookie.entrypoints": TRAEFIK_ENTRYPOINT,
            f"traefik.http.routers.{router}-setcookie.service": "vbrowser-backend@docker",
            f"traefik.http.routers.{router}-setcookie.priority": "20",
        }

        # Run-Parameter zusammenbauen
        run_kwargs = {
            "image":        DOCKERIMAGE,
            "name":         container_name,
            "detach":       True,
            "shm_size":     "2g",
            "network":      PROXY_NETWORK,
            "labels":       labels,
            "volumes":      {profile_path: {"bind": "/config", "mode": "rw"}},
            "environment":  {"KEEP_APP_RUNNING": "1", "FF_PREF_network.trr.mode": "5", "FF_OPEN_URL": "https://google.com"},
        }

        # Seccomp nur setzen wenn konfiguriert und Image passt
        security_opt = build_security_opt(DOCKERIMAGE)
        if security_opt:
            run_kwargs["security_opt"] = security_opt
            logger.info(f"Seccomp gesetzt für {DOCKERIMAGE}: {security_opt}")

        # DNS nur setzen wenn BROWSER_DNS in .env konfiguriert  ← NEU
        if BROWSER_DNS:
            run_kwargs["dns"] = BROWSER_DNS
            logger.info(f"Custom DNS für Browser-Container: {BROWSER_DNS}")     

        try:
            self.client.containers.run(**run_kwargs)
            # Container-IP ermitteln und zurückgeben
            c = self.client.containers.get(container_name)
            ip = c.attrs["NetworkSettings"]["Networks"].get(PROXY_NETWORK, {}).get("IPAddress")
            return f"https://{host}/", ip   # ← IP mitgeben
        except Exception as e:
            logger.error(f"Container start failed: {e}")
            raise HTTPException(500, f"Container start failed: {e}")

   

docker_manager = DockerManager()

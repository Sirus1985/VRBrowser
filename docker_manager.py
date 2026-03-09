import logging
from fastapi import HTTPException
from docker import DockerClient
from config import DOCKERHOST, DOCKERIMAGE, BASE_DOMAIN, PROXY_NETWORK, TRAEFIK_ENTRYPOINT, USE_TLS, CERT_RESOLVER


logger = logging.getLogger("vbrowser")



class DockerManager:
    def __init__(self):
        self.client = DockerClient(base_url=DOCKERHOST)


    def container_name(self, username: str) -> str:
        return f"vbrowser-{username}"


    def stop_container(self, username: str):
        name = self.container_name(username)
        try:
            c = self.client.containers.get(name)
            c.remove(force=True)
            logger.info(f"Removed container {name}")
        except Exception:
            pass


    def create_container(self, userid: int, username: str) -> str:
        name = self.container_name(username)
        self.stop_container(username)
        host = f"{username}.{BASE_DOMAIN}"
        router = f"vbrowser-user-{userid}"
        service = f"vbrowser-user-{userid}"

        labels = {
            "traefik.enable": "true",

            # Haupt-Router mit Auth-Middleware
            f"traefik.http.routers.{router}.rule": f"Host(`{host}`)",
            f"traefik.http.routers.{router}.entrypoints": TRAEFIK_ENTRYPOINT,
            f"traefik.http.routers.{router}.middlewares": "vbrowser-auth@file",
            f"traefik.http.routers.{router}.priority": "10",
            f"traefik.http.services.{service}.loadbalancer.server.port": "5800",

            # Separater Router für /auth/set-cookie → direkt ans Backend, OHNE Auth-Middleware
            f"traefik.http.routers.{router}-setcookie.rule": f"Host(`{host}`) && Path(`/auth/set-cookie`)",
            f"traefik.http.routers.{router}-setcookie.entrypoints": TRAEFIK_ENTRYPOINT,
            f"traefik.http.routers.{router}-setcookie.service": "vbrowser-backend@docker",
            f"traefik.http.routers.{router}-setcookie.priority": "20",
        }

        if USE_TLS:
            labels[f"traefik.http.routers.{router}.tls"] = "true"
            labels[f"traefik.http.routers.{router}-setcookie.tls"] = "true"
            if CERT_RESOLVER:
                labels[f"traefik.http.routers.{router}.tls.certresolver"] = CERT_RESOLVER
                labels[f"traefik.http.routers.{router}-setcookie.tls.certresolver"] = CERT_RESOLVER

        try:
            self.client.containers.run(
                DOCKERIMAGE, name=name, detach=True, shm_size="2g",
                network=PROXY_NETWORK, labels=labels,
                environment={"KEEP_APP_RUNNING": "1", "FF_OPEN_URL": "https://google.com"},
            )
            protocol = "https" if USE_TLS else "http"
            return f"{protocol}://{host}/"
        except Exception as e:
            logger.error(f"Container start failed: {e}")
            raise HTTPException(500, f"Container start failed: {e}")



docker_manager = DockerManager()

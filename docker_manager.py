import logging
from fastapi import HTTPException
from docker import DockerClient
from config import DOCKERHOST, DOCKERIMAGE, BASE_DOMAIN, PROXY_NETWORK, TRAEFIK_ENTRYPOINT, USE_TLS, CERT_RESOLVER

logger = logging.getLogger("vbrowser")


class DockerManager:
    def __init__(self):
        self.client = DockerClient(base_url=DOCKERHOST)

    def stop_container(self, container_name: str):
        try:
            c = self.client.containers.get(container_name)
            c.remove(force=True)
            logger.info(f"Removed container {container_name}")
        except Exception as e:
            logger.warning(f"Could not remove container {container_name}: {e}")

    def create_container(self, userid: int, username: str, container_name: str, host_id: str) -> str:
        self.stop_container(container_name)
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



        try:
            self.client.containers.run(
                DOCKERIMAGE, name=container_name, detach=True, shm_size="2g",
                network=PROXY_NETWORK, labels=labels,
                environment={"KEEP_APP_RUNNING": "1", "FF_OPEN_URL": "https://google.com"},

            )
            return f"https://{host}/"
        except Exception as e:
            logger.error(f"Container start failed: {e}")
            raise HTTPException(500, f"Container start failed: {e}")


docker_manager = DockerManager()

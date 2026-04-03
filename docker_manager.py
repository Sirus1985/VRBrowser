import docker
import logging
import os
from config import PROFILES_BASE, PROXY_NETWORK, DOCKERHOST, BASE_DOMAIN

logger = logging.getLogger(__name__)

try:
    client = docker.DockerClient(base_url=DOCKERHOST)
except Exception as e:
    logger.warning("Docker-Client-Init fehlgeschlagen: %s", e)
    client = docker.from_env()


def get_profile_path(username: str, container_def_id: int = None) -> str:
    suffix = f"_{container_def_id}" if container_def_id else "_default"
    path = os.path.join(PROFILES_BASE, f"{username}{suffix}")
    os.makedirs(path, exist_ok=True)
    return path


def create_container(username: str, session_id: str, token: str, container_def: dict):
    safe_username = "".join(c for c in username if c.isalnum())
    container_name = f"vbrowser-{safe_username}-{session_id[:8]}"

    internal_port = int(container_def.get("internal_port", 5800))
    def_id = container_def.get("id")
    profile_path = get_profile_path(username, def_id)

    env = {"TOKEN": token}
    for ev in container_def.get("env_vars", []):
        env[ev["key"]] = ev["value"]

    host = f"{session_id[:8]}.{BASE_DOMAIN}" if BASE_DOMAIN else f"{session_id[:8]}.localhost"
    router = f"vbrowser-{session_id[:8]}"
    service = f"vbrowser-{session_id[:8]}"

    labels = {
        "traefik.enable": "true",
        "traefik.docker.network": PROXY_NETWORK,

        f"traefik.http.routers.{router}.rule": f"Host(`{host}`)",
        f"traefik.http.routers.{router}.entrypoints": "web",
        f"traefik.http.routers.{router}.service": service,
        f"traefik.http.routers.{router}.priority": "10",

        f"traefik.http.services.{service}.loadbalancer.server.port": str(internal_port),

        f"traefik.http.routers.{router}-setcookie.rule": f"Host(`{host}`) && Path(`/auth/set-cookie`)",
        f"traefik.http.routers.{router}-setcookie.entrypoints": "web",
        f"traefik.http.routers.{router}-setcookie.service": "vbrowser-backend@docker",
        f"traefik.http.routers.{router}-setcookie.priority": "20",
    }

    kwargs = {
        "image": container_def["image"],
        "name": container_name,
        "detach": True,
        "environment": env,
        "volumes": {profile_path: {"bind": "/config", "mode": "rw"}},
        "shm_size": container_def.get("shm_size", "2g"),
        "network": PROXY_NETWORK,
        "restart_policy": {"Name": container_def.get("restart_policy", "no")},
        "labels": labels,
    }

    cpu_limit = container_def.get("cpu_limit")
    if cpu_limit:
        kwargs["nano_cpus"] = int(float(cpu_limit) * 1e9)

    mem_limit = container_def.get("mem_limit")
    if mem_limit:
        kwargs["mem_limit"] = mem_limit

    logger.info("Starte Container '%s' mit Image '%s'", container_name, container_def["image"])
    return client.containers.run(**kwargs)


def get_container_ip(container):
    try:
        container.reload()
        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        if PROXY_NETWORK in networks:
            return networks[PROXY_NETWORK].get("IPAddress")
        for net_info in networks.values():
            ip = net_info.get("IPAddress")
            if ip:
                return ip
    except Exception as e:
        logger.warning("Fehler beim Abrufen der Container-IP: %s", e)
    return None


def stop_container(container_name: str):
    try:
        c = client.containers.get(container_name)
        c.remove(force=True)
        logger.info("Container %s gestoppt und entfernt.", container_name)
    except docker.errors.NotFound:
        pass
    except Exception as e:
        logger.warning("Konnte Container %s nicht entfernen: %s", container_name, e)


def container_exists(container_name: str) -> bool:
    try:
        client.containers.get(container_name)
        return True
    except Exception:
        return False
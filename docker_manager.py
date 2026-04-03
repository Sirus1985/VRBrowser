import docker
import logging
import os
from config import PROFILES_BASE, PROXY_NETWORK, DOCKERHOST

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


def create_container(username: str, session_id: str, token: str,
                     container_def: dict) -> docker.models.containers.Container:
    container_name = f"vbrowser_{username}_{session_id[:8]}"
    internal_port  = container_def.get("internal_port", 5800)
    def_id         = container_def.get("id")
    profile_path   = get_profile_path(username, def_id)

    env = {"TOKEN": token}
    for ev in container_def.get("env_vars", []):
        env[ev["key"]] = ev["value"]

    kwargs = {
        "image":          container_def["image"],
        "name":           container_name,
        "detach":         True,
        "environment":    env,
        "volumes":        {profile_path: {"bind": "/config", "mode": "rw"}},
        "shm_size":       container_def.get("shm_size", "2g"),
        "network":        PROXY_NETWORK,
        "restart_policy": {"Name": container_def.get("restart_policy", "no")},
        "labels": {
            "traefik.enable": "true",
            f"traefik.http.routers.{container_name}.rule":
                f"PathPrefix(`/browser/{session_id}`)",
            f"traefik.http.routers.{container_name}.middlewares":
                f"{container_name}-strip",
            f"traefik.http.middlewares.{container_name}-strip.stripprefix.prefixes":
                f"/browser/{session_id}",
            f"traefik.http.services.{container_name}.loadbalancer.server.port":
                str(internal_port),
        },
    }

    cpu_limit = container_def.get("cpu_limit")
    if cpu_limit:
        kwargs["nano_cpus"] = int(float(cpu_limit) * 1e9)

    mem_limit = container_def.get("mem_limit")
    if mem_limit:
        kwargs["mem_limit"] = mem_limit

    logger.info("Starte Container '%s' mit Image '%s'", container_name, container_def["image"])
    return client.containers.run(**kwargs)


def get_container_ip(container: docker.models.containers.Container) -> str | None:
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
        container = client.containers.get(container_name)
        container.stop(timeout=10)
        container.remove()
        logger.info("Container '%s' gestoppt und entfernt.", container_name)
    except docker.errors.NotFound:
        logger.warning("Container '%s' nicht gefunden (bereits entfernt?).", container_name)
    except Exception as e:
        logger.error("Fehler beim Stoppen von '%s': %s", container_name, e)


def container_exists(container_name: str) -> bool:
    try:
        client.containers.get(container_name)
        return True
    except docker.errors.NotFound:
        return False


def get_container_stats(container_name: str) -> dict | None:
    try:
        container = client.containers.get(container_name)
        stats      = container.stats(stream=False)
        cpu_delta  = (stats["cpu_stats"]["cpu_usage"]["total_usage"]
                      - stats["precpu_stats"]["cpu_usage"]["total_usage"])
        sys_delta  = (stats["cpu_stats"]["system_cpu_usage"]
                      - stats["precpu_stats"]["system_cpu_usage"])
        num_cpus   = stats["cpu_stats"].get("online_cpus", 1)
        cpu_pct    = (cpu_delta / sys_delta) * num_cpus * 100.0 if sys_delta > 0 else 0.0
        mem_usage  = stats["memory_stats"].get("usage", 0)
        mem_limit  = stats["memory_stats"].get("limit", 1)
        return {
            "cpu_percent":   round(cpu_pct, 1),
            "mem_usage_mb":  round(mem_usage / 1024 / 1024, 1),
            "mem_limit_mb":  round(mem_limit / 1024 / 1024, 1),
            "mem_percent":   round((mem_usage / mem_limit) * 100.0, 1),
        }
    except Exception as e:
        logger.warning("Stats für '%s' nicht verfügbar: %s", container_name, e)
        return None
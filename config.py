import os

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))
SECRETKEY = os.getenv("SECRETKEY", "super-secret-key-change-me")
DBPATH = os.getenv("DBPATH", ".data/browser.db")
DOCKERHOST = os.getenv("DOCKERHOST", "unix:///var/run/docker.sock")
DOCKERIMAGE = os.getenv("DOCKERIMAGE", "jlesage/firefox:latest")
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "vbrowser.home")
PROXY_NETWORK = os.getenv("PROXY_NETWORK", "vbrowser_proxy")
TRAEFIK_ENTRYPOINT = os.getenv("TRAEFIK_ENTRYPOINT", "websecure")
USE_TLS = os.getenv("USE_TLS", "false").lower() == "true"
CERT_RESOLVER = os.getenv("CERT_RESOLVER", "")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "300"))
PROFILES_BASE = os.getenv("PROFILES_BASE", "/opt/vbrowser/profiles")  # NEU

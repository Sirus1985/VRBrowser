# VBrowser

Ein selbst gehostetes Browser-as-a-Service-System. Jeder Nutzer startet auf Knopfdruck einen isolierten Firefox-Container, der über Traefik per HTTPS erreichbar ist. Die Verwaltung erfolgt über ein eingebautes Admin-Panel mit Benutzern, Teams, Session-Logging und Nutzungsstatistiken.

---

## Features

- 🦊 Isolierter Firefox pro Nutzer (via Docker)
- 🔐 Login mit JWT-Token, persistente Sessions
- 👥 Benutzerverwaltung mit Teams und Team-Admins
- 📊 Nutzungsrangliste nach Nutzer und Team mit Zeitfiltern
- 🗂️ Persistente Firefox-Profile pro Nutzer
- 🌙 Dark / Light / Auto Theme
- 🔒 Traefik-Integration mit optionalem TLS

---

## Voraussetzungen

- Docker & Docker Compose
- Traefik als Reverse Proxy (im selben Docker-Netzwerk)
- Python 3.11+ (bei Betrieb ohne Docker)

---

## Schnellstart

```bash
git clone https://github.com/Sirus1985/VRBrowser.git
cd VRBrowser
cp .env.example .env
# .env anpassen (siehe unten)
docker compose up -d


Die Oberfläche ist danach unter https://<BASE_DOMAIN> erreichbar.
Standard-Login: admin / adminpass — bitte sofort im Admin-Panel ändern.

---

## Projektstruktur


text
VRBrowser/
├── main.py                  # FastAPI-Einstiegspunkt
├── config.py                # Konfiguration aus Umgebungsvariablen
├── database.py              # SQLite-Datenbanklogik
├── auth.py                  # JWT-Authentifizierung
├── docker_manager.py        # Docker-Container-Steuerung
├── session_manager.py       # Session-Lifecycle & Timeout
├── frontend.py              # Eingebettetes HTML/JS-Frontend
├── models.py                # Pydantic-Modelle
├── routes/
│   ├── admin_logging.py     # Logging- & Ranking-Endpunkte
│   └── ...                  # weitere API-Routen
├── docker-compose.yml
├── Dockerfile
├── install.sh               # Installations-Hilfsskript
├── browser-start.sh         # Startskript für Browser-Container
├── traefik-dynamic.yml      # Traefik Middleware-Konfiguration
└── .data/                   # SQLite-Datenbank (wird automatisch erstellt)


---

## Umgebungsvariablen

Umgebungsvariablen (.env)
Alle Variablen haben sinnvolle Standardwerte. Für den Produktionsbetrieb müssen mindestens SECRETKEY, BASE_DOMAIN und PROXY_NETWORK angepasst werden.

Server

Variable	Standard	Beschreibung
HOST	0.0.0.0	Bind-Adresse des FastAPI-Servers
PORT	8080	Port des FastAPI-Servers
SECRETKEY	super-secret-key-change-me	JWT-Signing-Secret — unbedingt ändern!
DBPATH	.data/browser.db	Pfad zur SQLite-Datenbank
Docker

Variable	Standard	Beschreibung
DOCKERHOST	unix:///var/run/docker.sock	Docker-Socket oder TCP-Adresse (tcp://host:2375)
DOCKERIMAGE	jlesage/firefox:latest	Docker-Image für Browser-Container
PROXY_NETWORK	vbrowser_proxy	Docker-Netzwerk, in dem Traefik und Container laufen
Netzwerk & TLS

Variable	Standard	Beschreibung
BASE_DOMAIN	vbrowser.home	Basis-Domain für Container-URLs (z.B. browser.example.com)
TRAEFIK_ENTRYPOINT	websecure	Traefik Entrypoint (web für HTTP, websecure für HTTPS)
USE_TLS	false	TLS via Traefik aktivieren (true / false)
CERT_RESOLVER	(leer)	Traefik CertResolver-Name (z.B. letsencrypt)
Sessions & Profile

Variable	Standard	Beschreibung
SESSION_TIMEOUT	300	Sekunden bis eine inaktive Session automatisch beendet wird
PROFILES_BASE	/opt/vbrowser/profiles	Verzeichnis für persistente Firefox-Profile
Browser-Container

Variable	Standard	Beschreibung
BROWSER_DNS	(leer)	Kommagetrennte DNS-Server für Browser-Container (z.B. 1.1.1.1,8.8.8.8)
BROWSER_SECCOMP_MODE	off	Seccomp-Modus: off, unconfined oder profile
BROWSER_SECCOMP_PROFILE	/opt/vbrowser/seccomp_profile.json	Pfad zum Seccomp-JSON-Profil (nur bei BROWSER_SECCOMP_MODE=profile)
BROWSER_SECCOMP_IMAGES	jlesage/firefox	Kommagetrennte Liste von Images, auf die Seccomp angewendet wird
BROWSER_SECCOMP_ALL_IMAGES	false	Seccomp auf alle Images anwenden, unabhängig von BROWSER_SECCOMP_IMAGES

# Beispiel .env

text
# Server
HOST=0.0.0.0
PORT=8080
SECRETKEY=mein-sehr-sicherer-schluessel-hier

# Datenbank
DBPATH=.data/browser.db

# Docker
DOCKERHOST=unix:///var/run/docker.sock
DOCKERIMAGE=jlesage/firefox:latest
PROXY_NETWORK=vbrowser_proxy

# Domain & TLS
BASE_DOMAIN=browser.example.com
TRAEFIK_ENTRYPOINT=websecure
USE_TLS=true
CERT_RESOLVER=letsencrypt

# Sessions
SESSION_TIMEOUT=300
PROFILES_BASE=/opt/vbrowser/profiles

# Browser-Container (optional)
BROWSER_DNS=1.1.1.1,8.8.8.8
BROWSER_SECCOMP_MODE=off
Rollen & Berechtigungen
Rolle	Beschreibung
Superadmin	Voller Zugriff: Nutzer, Teams, Sessions, Logging, Ranglisten
Team-Admin	Kann Nutzer des eigenen Teams verwalten
Nutzer	Kann eigene Session starten/stoppen, Profil zurücksetzen
API-Endpunkte (Auszug)
Methode	Pfad	Beschreibung
Methode	Pfad	Beschreibung
POST	/api/login	Login, gibt JWT zurück
POST	/api/session/start	Browser-Container starten
POST	/api/session/stop	Container stoppen & Session loggen
GET	/api/session/status	Aktiven Container prüfen
GET	/api/users	Alle Nutzer (Admin)
POST	/api/users	Nutzer anlegen (Admin)
PATCH	/api/users/{id}	Nutzer bearbeiten (Passwort, Team)
DELETE	/api/users/{id}	Nutzer löschen (Admin)
GET	/api/teams	Alle Teams
POST	/api/teams	Team anlegen
GET	/api/admin/logging/ranking	Nutzungsrangliste (Nutzer)
GET	/api/admin/logging/ranking/teams	Nutzungsrangliste (Teams)
GET	/api/admin/logging/user/{id}	Sitzungsdetails eines Nutzers
GET	/api/admin/logging/container/{name}	Container → Nutzer Rückwärtssuche

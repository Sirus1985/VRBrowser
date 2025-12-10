# VRBrowser
VirtuelleBrowser


# 🌐 Virtual Browser Server - Komplette Installation

Alle notwendigen Dateien sind unten aufgelistet. Du kannst sie direkt kopieren und auf deiner Proxmox VM aufbauen.

---

## 📋 Datei #1: backend.py
**Speichern als:** `/opt/vbrowser/backend.py`

Dies ist der Kern-Server mit FastAPI, der alle Funktionen verwaltet:
- User Management
- JWT-Authentifizierung
- Docker Container Management
- URL Logging
- Session Handling

---

## 📋 Datei #2: frontend/index.html
**Speichern als:** `/opt/vbrowser/frontend/index.html`

Responsive Web-Interface mit:
- Login/Register Forms
- noVNC Browser Viewer
- URL Logs Anzeige
- Session Management

---

## 🐳 Datei #3: Dockerfile
**Speichern als:** `/opt/vbrowser/Dockerfile`

Docker Image für Browser-Container mit:
- Chromium
- Xvfb Virtual Display
- Tinyproxy für URL-Logging
- noVNC Server

---

## 🐳 Datei #4: Dockerfile.backend
**Speichern als:** `/opt/vbrowser/Dockerfile.backend`

---

## 🚀 Datei #5: browser-start.sh
**Speichern als:** `/opt/vbrowser/browser-start.sh`

Startup-Script für Browser-Container:

---

## 🐳 Datei #6: docker-compose.yml
**Speichern als:** `/opt/vbrowser/docker-compose.yml`


---

## ⚙️ Datei #7: nginx.conf
**Speichern als:** `/opt/vbrowser/nginx.conf`

Reverse Proxy mit SSL und Rate Limiting:

---

## 📦 Datei #8: requirements.txt
**Speichern als:** `/opt/vbrowser/requirements.txt`

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
PyJWT==2.8.1
python-dotenv==1.0.0
docker==7.0.0
aiofiles==23.2.1
```

---

## 🔧 Datei #9: .env
**Speichern als:** `/opt/vbrowser/.env`


---

## 🚀 Datei #10: install.sh
**Speichern als:** `/opt/vbrowser/install.sh` (chmod +x)



---

## 🔐 Sicherheit

### SSL-Zertifikat erstellen (selbstsigniert):

### SECRET_KEY generieren:
---

## 📖 Nächste Schritte

1. **Dateien hochladen:** Alle Dateien auf Proxmox VM kopieren
2. **.env konfigurieren:** HOST_IP auf deine VM-IP setzen
3. **Starten:** `sudo bash install.sh`
4. **Zugriff:** https://192.168.x.x
5. **Login:** testuser / testpass

---

## ✨ Features

✅ 50+ gleichzeitige Benutzer
✅ Separate Browser-Container pro Nutzer
✅ URL-Logging pro Tag/Benutzer
✅ JWT-Authentifizierung
✅ HTTPS/TLS mit Let's Encrypt Support
✅ Responsive Web-UI
✅ Admin-Dashboard
✅ Automatische Session-Bereinigung
✅ Firewall-kompatibel
✅ Produktionsreife

---

**Version:** 1.0.0
**Letzte Aktualisierung:** 2024
**Status:** Produktionsreife ✓

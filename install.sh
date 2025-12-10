#!/bin/bash

# Virtual Browser Installation Script
# Automatisierte Installation auf Proxmox VM
# Verwendung: sudo bash install.sh

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Virtual Browser Server - Installation Script           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Fehler: Bitte führe das Script als root aus (sudo bash install.sh)"
    exit 1
fi

# Detect OS
if [ ! -f /etc/os-release ]; then
    echo "❌ Fehler: /etc/os-release nicht gefunden"
    exit 1
fi

source /etc/os-release

echo "📋 System-Informationen:"
echo "  OS: $PRETTY_NAME"
echo "  Version: $VERSION_ID"
echo ""

# ============================================================================
# STEP 1: Prerequisites
# ============================================================================

echo "📦 Schritt 1: Überprüfe Voraussetzungen..."
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker nicht gefunden. Installiere Docker..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $SUDO_USER
    echo "✓ Docker installiert"
else
    echo "✓ Docker bereits installiert"
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  Docker Compose nicht gefunden. Installiere Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✓ Docker Compose installiert"
else
    echo "✓ Docker Compose bereits installiert"
fi

# Check for OpenSSL
if ! command -v openssl &> /dev/null; then
    echo "⚠️  OpenSSL nicht gefunden. Installiere OpenSSL..."
    apt-get update > /dev/null
    apt-get install -y openssl > /dev/null
    echo "✓ OpenSSL installiert"
else
    echo "✓ OpenSSL bereits installiert"
fi

# Check for curl
if ! command -v curl &> /dev/null; then
    echo "⚠️  curl nicht gefunden. Installiere curl..."
    apt-get update > /dev/null
    apt-get install -y curl > /dev/null
    echo "✓ curl installiert"
else
    echo "✓ curl bereits installiert"
fi

echo ""

# ============================================================================
# STEP 2: Create directories
# ============================================================================

echo "📁 Schritt 2: Erstelle Verzeichnisse..."
echo ""

# Main directory
if [ ! -d "/opt/vbrowser" ]; then
    mkdir -p /opt/vbrowser
    echo "✓ /opt/vbrowser erstellt"
else
    echo "✓ /opt/vbrowser existiert bereits"
fi

# Subdirectories
mkdir -p /opt/vbrowser/data/logs
mkdir -p /opt/vbrowser/frontend
mkdir -p /opt/vbrowser/ssl
mkdir -p /opt/vbrowser/.docker

echo "✓ Unterverzeichnisse erstellt"
echo ""

# ============================================================================
# STEP 3: Copy files
# ============================================================================

echo "📋 Schritt 3: Kopiere Dateien..."
echo ""

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# List of required files
REQUIRED_FILES=(
    "backend.py"
    "Dockerfile"
    "Dockerfile.backend"
    "docker-compose.yml"
    "nginx.conf"
    "requirements.txt"
    "browser-start.sh"
    ".env"
)

# Copy files
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        cp "$SCRIPT_DIR/$file" "/opt/vbrowser/$file"
        echo "✓ $file kopiert"
    else
        echo "⚠️  $file nicht gefunden (ignoriert)"
    fi
done

# Copy frontend if exists
if [ -d "$SCRIPT_DIR/frontend" ]; then
    cp -r "$SCRIPT_DIR/frontend/"* "/opt/vbrowser/frontend/" 2>/dev/null || true
    echo "✓ Frontend-Dateien kopiert"
fi

# Copy vbrowser.service if exists
if [ -f "$SCRIPT_DIR/vbrowser.service" ]; then
    cp "$SCRIPT_DIR/vbrowser.service" "/opt/vbrowser/vbrowser.service"
    echo "✓ systemd Service kopiert"
fi

echo ""

# ============================================================================
# STEP 4: Permissions
# ============================================================================

echo "🔒 Schritt 4: Setze Berechtigungen..."
echo ""

chmod +x /opt/vbrowser/browser-start.sh
chmod 644 /opt/vbrowser/.env
chmod 755 /opt/vbrowser/data
chmod 755 /opt/vbrowser/data/logs

echo "✓ Berechtigungen gesetzt"
echo ""

# ============================================================================
# STEP 5: SSL Certificate
# ============================================================================

echo "🔐 Schritt 5: Erstelle SSL-Zertifikat..."
echo ""

if [ ! -f "/opt/vbrowser/ssl/cert.pem" ] || [ ! -f "/opt/vbrowser/ssl/key.pem" ]; then
    cd /opt/vbrowser/ssl
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
        -subj "/C=DE/ST=State/L=City/O=Organization/CN=localhost" > /dev/null 2>&1
    chmod 644 cert.pem key.pem
    echo "✓ Self-signed SSL-Zertifikat erstellt"
    echo "  ℹ️  Für Produktion: Let's Encrypt Zertifikat verwenden"
else
    echo "✓ SSL-Zertifikate existieren bereits"
fi

echo ""

# ============================================================================
# STEP 6: Build Docker Images
# ============================================================================

echo "🐳 Schritt 6: Baue Docker Images..."
echo ""

cd /opt/vbrowser

# Build browser image
echo "   Baue virtual-browser:latest..."
docker build -t virtual-browser:latest . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ virtual-browser:latest gebaut"
else
    echo "❌ Fehler beim Bauen von virtual-browser:latest"
    exit 1
fi

# Build backend image (via docker-compose)
echo "   Baue Backend-Image..."
docker-compose build backend > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Backend-Image gebaut"
else
    echo "❌ Fehler beim Bauen des Backend-Images"
    exit 1
fi

echo ""

# ============================================================================
# STEP 7: Create systemd service
# ============================================================================

echo "⚙️  Schritt 7: Erstelle systemd Service..."
echo ""

if [ -f "/opt/vbrowser/vbrowser.service" ]; then
    cp /opt/vbrowser/vbrowser.service /etc/systemd/system/vbrowser.service
    chmod 644 /etc/systemd/system/vbrowser.service
    systemctl daemon-reload
    echo "✓ systemd Service registriert"
else
    echo "ℹ️  vbrowser.service nicht gefunden (optional)"
fi

echo ""

# ============================================================================
# STEP 8: Start services
# ============================================================================

echo "🚀 Schritt 8: Starte Virtual Browser Server..."
echo ""

cd /opt/vbrowser

# Start docker-compose
docker-compose up -d
if [ $? -eq 0 ]; then
    echo "✓ Docker Compose Services gestartet"
else
    echo "❌ Fehler beim Starten der Services"
    exit 1
fi

# Wait for services to be ready
echo ""
echo "⏳ Warte auf Services (30 Sekunden)..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✓ Backend ist online"
        break
    fi
    sleep 1
done

echo ""

# ============================================================================
# STEP 9: Verification
# ============================================================================

echo "✓ Schritt 9: Überprüfe Installation..."
echo ""

# Check containers
BACKEND_STATUS=$(docker ps --filter "name=vbrowser-backend" --filter "status=running" | wc -l)
NGINX_STATUS=$(docker ps --filter "name=vbrowser-nginx" --filter "status=running" | wc -l)

if [ $BACKEND_STATUS -gt 1 ]; then
    echo "✓ Backend Container läuft"
else
    echo "⚠️  Backend Container nicht aktiv"
fi

if [ $NGINX_STATUS -gt 1 ]; then
    echo "✓ Nginx Container läuft"
else
    echo "⚠️  Nginx Container nicht aktiv"
fi

# Check database
if [ -f "/opt/vbrowser/data/browser.db" ]; then
    echo "✓ Datenbank erstellt"
else
    echo "⚠️  Datenbank nicht gefunden"
fi

echo ""

# ============================================================================
# STEP 10: Print summary
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           ✅ Installation erfolgreich abgeschlossen!       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📝 Nächste Schritte:"
echo ""
echo "1. Konfiguration anpassen:"
echo "   cd /opt/vbrowser"
echo "   nano .env"
echo ""
echo "   Wichtig:"
echo "   → HOST_IP = deine Proxmox-VM IP (z.B. 192.168.x.x)"
echo "   → SECRET_KEY = ändern für Produktion"
echo ""

echo "2. Docker-Compose neu starten (nach .env Änderungen):"
echo "   docker-compose restart backend"
echo ""

echo "3. Browser öffnen:"
echo "   https://192.168.x.x"
echo ""

echo "4. Mit Test-Credentials anmelden:"
echo "   Username: testuser"
echo "   Password: testpass"
echo ""

echo "📊 Wichtige Befehle:"
echo ""
echo "   Status prüfen:"
echo "   docker-compose ps"
echo "   docker stats"
echo ""
echo "   Logs ansehen:"
echo "   docker-compose logs -f backend"
echo ""
echo "   Services neu starten:"
echo "   docker-compose restart"
echo ""
echo "   Services stoppen:"
echo "   docker-compose down"
echo ""

echo "🔐 Sicherheit (WICHTIG!):"
echo ""
echo "1. Let's Encrypt Zertifikat für Produktion:"
echo "   sudo apt-get install certbot"
echo "   sudo certbot certonly --standalone -d your-domain.com"
echo "   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem"
echo "   cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem"
echo "   docker-compose restart nginx"
echo ""

echo "2. Firewall konfigurieren (nur Intranet):"
echo "   sudo ufw allow from 192.168.x.0/24 to any port 443"
echo "   sudo ufw allow from 192.168.x.0/24 to any port 80"
echo ""

echo "3. DNS Filterung einrichten (schädliche Seiten blocken)"
echo ""

echo "📂 Dateistruktur:"
echo ""
echo "   /opt/vbrowser/"
echo "   ├── backend.py"
echo "   ├── frontend/index.html"
echo "   ├── docker-compose.yml"
echo "   ├── .env"
echo "   ├── data/"
echo "   │   ├── browser.db"
echo "   │   └── logs/"
echo "   └── ssl/"
echo "       ├── cert.pem"
echo "       └── key.pem"
echo ""

echo "📖 Dokumentation:"
echo "   Siehe README.md für detaillierte Anleitung"
echo ""

echo "💡 Pro-Tipps:"
echo "   • Nutze systemd für Auto-Start: systemctl start vbrowser"
echo "   • Backups täglich erstellen: tar -czf vbrowser-backup.tar.gz /opt/vbrowser/data"
echo "   • Logs regelmäßig überprüfen"
echo "   • Ressourcenlimits in .env anpassen für 50+ User"
echo ""

echo "═════════════════════════════════════════════════════════════"
echo ""
echo "Support & Hilfe:"
echo "  • Logs: docker-compose logs backend"
echo "  • Health Check: curl https://192.168.x.x/api/health"
echo "  • Admin Panel: https://192.168.x.x/admin-panel.html"
echo ""
echo "═════════════════════════════════════════════════════════════"
echo ""

# Check if we can reach the service
echo "🔍 Finale Überprüfung..."
sleep 2

if curl -sk https://localhost/api/health > /dev/null 2>&1; then
    echo "✅ Virtual Browser Server ist erreichbar!"
    echo ""
    echo "👉 Öffne jetzt https://192.168.x.x in deinem Browser"
else
    echo "⚠️  Server nicht sofort erreichbar (kann noch starten)"
    echo "   Versuche in 30 Sekunden erneut: docker-compose logs"
fi

echo ""
echo "🎉 Installation abgeschlossen!"
echo ""

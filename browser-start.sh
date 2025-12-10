#!/bin/bash

set -e

DISPLAY=:99
SCREEN_WIDTH=1920
SCREEN_HEIGHT=1080
SCREEN_DEPTH=24
LOGS_DIR="/app/logs"
USER_ID="${USER_ID:-1000}"
USERNAME="${USERNAME:-user}"

echo "Starting Virtual Browser Container for User: $USERNAME"

if ! id -u "vbrowser" &>/dev/null; then
    useradd -m -u 1000 vbrowser
fi

echo "Starting X11 Virtual Frame Buffer..."
Xvfb $DISPLAY -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} &
XVFB_PID=$!
echo "Xvfb PID: $XVFB_PID"

sleep 2

echo "Starting window manager..."
DISPLAY=$DISPLAY fluxbox > /dev/null 2>&1 &
FLUXBOX_PID=$!

echo "Configuring Tinyproxy..."
cat > /etc/tinyproxy/tinyproxy.conf <<EOF
User tinyproxy
Group tinyproxy
Port 8888
Listen 127.0.0.1
ConnectPort 443
ConnectPort 80
Timeout 600
ErrorFile 404 "/usr/share/tinyproxy/404.html"
ErrorFile 400 "/usr/share/tinyproxy/400.html"
ErrorFile 503 "/usr/share/tinyproxy/503.html"
ErrorFile 403 "/usr/share/tinyproxy/403.html"
PidFile "/var/run/tinyproxy/tinyproxy.pid"
LogFile "/app/logs/tinyproxy-${USERNAME}.log"
LogLevel Connect
StartServers 10
MaxClients 100
EOF

mkdir -p /var/run/tinyproxy
chown tinyproxy:tinyproxy /var/run/tinyproxy

echo "Starting Tinyproxy..."
tinyproxy -c /etc/tinyproxy/tinyproxy.conf &
PROXY_PID=$!
echo "Tinyproxy PID: $PROXY_PID"

sleep 1

echo "Starting Chromium browser..."
DISPLAY=$DISPLAY chromium-browser \
    --new-instance \
    --no-sandbox \
    --disable-gpu \
    --disable-web-resources \
    --disable-client-side-phishing-detection \
    --no-default-browser-check \
    --no-first-run \
    --user-data-dir=/tmp/chromium-profile \
    --proxy-server="http://127.0.0.1:8888" \
    "about:blank" > /dev/null 2>&1 &
CHROME_PID=$!
echo "Chromium PID: $CHROME_PID"

sleep 3

echo "Starting VNC Server on port 5900..."
x11vnc \
    -display $DISPLAY \
    -forever \
    -nopw \
    -xkb \
    -noxrecord \
    -noxfixes \
    -noxdamage \
    -shared \
    -logfile "/app/logs/vnc-${USERNAME}.log" \
    -bg \
    -rfbport 5900 \
    -listen 0.0.0.0 &

NOVNC_PID=$!
echo "VNC PID: $NOVNC_PID"

echo "Starting noVNC proxy on port 6080..."
/usr/share/novnc/utils/novnc_proxy \
    --listen 6080 \
    --vnc localhost:5900 \
    > /app/logs/novnc-${USERNAME}.log 2>&1 &
NOVNC_PROXY_PID=$!
echo "noVNC Proxy PID: $NOVNC_PROXY_PID"

echo "All services started successfully"
echo "User: $USERNAME (ID: $USER_ID)"
echo "Display: $DISPLAY"
echo "VNC: localhost:5900"
echo "noVNC: localhost:6080/vnc.html"

tail -f /app/logs/tinyproxy-${USERNAME}.log &
TAIL_PID=$!

trap "kill $XVFB_PID $FLUXBOX_PID $CHROME_PID $PROXY_PID $NOVNC_PID $NOVNC_PROXY_PID $TAIL_PID 2>/dev/null; exit 0" SIGTERM SIGINT

wait

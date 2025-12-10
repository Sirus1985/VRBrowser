FROM debian:12-slim

RUN apt-get update && apt-get install -y \
    chromium \
    xvfb \
    x11vnc \
    novnc \
    python3-minimal \
    supervisor \
    tinyproxy \
    curl \
    ca-certificates \
    fonts-liberation \
    fonts-dejavu \
    fluxbox \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY browser-start.sh /app/browser-start.sh
RUN chmod +x /app/browser-start.sh

RUN mkdir -p /app/logs /tmp/.X11-unix /run/user/1000 && \
    chmod 777 /tmp/.X11-unix /app/logs

EXPOSE 6080 6081 5900 8888

ENV DISPLAY=:99 \
    SCREEN_WIDTH=1920 \
    SCREEN_HEIGHT=1080 \
    SCREEN_DEPTH=24

CMD ["/app/browser-start.sh"]

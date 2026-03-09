FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-jose[cryptography] \
    pyjwt \
    docker \
    pydantic

# Alle Dateien kopieren
COPY main.py config.py models.py database.py auth.py docker_manager.py frontend.py session_manager.py /app/
COPY routes/ /app/routes/

RUN mkdir -p /appdata

EXPOSE 8080

CMD ["python", "main.py"]

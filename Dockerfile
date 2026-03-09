FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-jose[cryptography] \
    pyjwt \
    docker \
    pydantic

# Copy application
COPY backend.py /app/backend.py

# Create data directory
RUN mkdir -p /appdata

EXPOSE 8080

CMD ["python", "backend.py"]

# Worker image. Shares the backend application package (models, queue, storage,
# processors) but its entrypoint runs the dequeue/process loop instead of the
# HTTP server. Build context: projects/renderflow/
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/storage && chown -R appuser:appuser /app /data
USER appuser

ENV RENDERFLOW_SERVICE_NAME=renderflow-worker \
    RENDERFLOW_STORAGE_LOCAL_DIR=/data/storage

# Liveness for orchestrators: the worker writes a heartbeat file each loop.
CMD ["python", "-m", "app.worker.runner"]

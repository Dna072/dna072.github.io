# Backend (API) image. ffmpeg is installed so the same image can also run the
# worker; the worker service overrides the command (see docker-compose.yml).
# Build context: projects/renderflow/
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/storage && chown -R appuser:appuser /app /data
USER appuser

ENV RENDERFLOW_STORAGE_LOCAL_DIR=/data/storage

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

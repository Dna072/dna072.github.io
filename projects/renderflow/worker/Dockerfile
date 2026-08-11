# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY common/ /app/common/
RUN pip install --no-cache-dir /app/common

COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

COPY worker/ /app/worker/
WORKDIR /app/worker

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD pgrep -f "python.*worker.main" > /dev/null || exit 1

CMD ["python", "-m", "worker.main"]

# ─── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: Runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="tu-usuario"
LABEL description="DevPulse — Real-time system monitor with WebSockets"
LABEL version="1.0.0"

WORKDIR /app

# psutil needs access to /proc — running as root inside container is acceptable
# for read-only system metrics. In production, use --pid=host carefully.
COPY --from=builder /install /usr/local
COPY main.py .
COPY static/ ./static/

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/snapshot')" || exit 1

CMD ["python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--no-access-log"]

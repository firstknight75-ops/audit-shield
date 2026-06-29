# ── Stage 1: builder ──────────────────────────────────────────
# Multi-stage build: only the compiled wheels and runtime deps in the
# final image. No compilers, no .pyc, no apt cache.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Runtime + OCR dependencies (Arabic tesseract language pack + poppler for PDF→image)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libmagic1 \
        tesseract-ocr \
        tesseract-ocr-ara \
        tesseract-ocr-ckb \
        poppler-utils \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# Install Python deps in a dedicated venv-style layout
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

# ── Stage 2: runtime ──────────────────────────────────────────
# Distroless-style minimal runtime: only what uvicorn needs at runtime.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/install/lib/python3.12/site-packages"

# Run as non-root user — required for production security
RUN groupadd --system --gid 1001 auditcore && \
    useradd --system --uid 1001 --gid auditcore --no-create-home --shell /sbin/nologin auditcore && \
    apt-get update && apt-get install -y --no-install-recommends \
        libmagic1 \
        tesseract-ocr \
        tesseract-ocr-ara \
        tesseract-ocr-ckb \
        poppler-utils \
        libpq5 \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /install

# Copy application code with the right ownership
COPY --from=builder --chown=auditcore:auditcore /app/app /app/app
COPY --from=builder --chown=auditcore:auditcore /app/alembic /app/alembic
COPY --from=builder --chown=auditcore:auditcore /app/alembic.ini /app/alembic.ini

WORKDIR /app
USER auditcore

# Health check (k8s probes consume this)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

EXPOSE 8000

# Production launch: uvicorn with 4 workers, tuned for prod.
# Workers = (2 * CPU) + 1; keep ≤ 8 to avoid GIL contention on hot paths.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*", \
     "--log-config", "/dev/null"]

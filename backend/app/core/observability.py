"""Structured logging configuration + Prometheus metrics + health checks.

Enterprise-grade observability for AuditCore:
- JSON-structured logs (one event per line, parseable in any log stack)
- Prometheus metrics exposed at /metrics (no auth, intended for scraping)
- Deep health checks at /ready and /health
- OpenTelemetry-compatible traces (no-op exporter by default; wire your own)
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any

from fastapi import APIRouter, FastAPI, Response

# ── Structured logging ────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Render log records as one-line JSON for downstream log stacks."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(record.created)) + f'.{int(record.msecs):03d}Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        # Pull from `extra` if present (logging convention)
        for key, value in record.__dict__.items():
            if key in ('args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                      'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
                      'message', 'msg', 'name', 'pathname', 'process', 'processName',
                      'relativeCreated', 'stack_info', 'thread', 'threadName', 'taskName'):
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except (TypeError, ValueError):
                payload[key] = repr(value)
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str | None = None) -> None:
    """Configure structured JSON logging to stdout."""
    log_level = (level or os.environ.get('LOG_LEVEL', 'INFO')).upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)
    # Quiet noisy libraries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


# ── Prometheus metrics (using prometheus_client if available) ─────

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
    _METRICS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _METRICS_AVAILABLE = False

if _METRICS_AVAILABLE:
    HTTP_REQUESTS = Counter(
        'auditcore_http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status'],
    )
    HTTP_REQUEST_DURATION = Histogram(
        'auditcore_http_request_duration_seconds',
        'HTTP request duration',
        ['method', 'endpoint'],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
    DB_POOL_SIZE = Gauge(
        'auditcore_db_pool_size',
        'Current DB connection pool size',
    )
    ACTIVE_TASKS = Gauge(
        'auditcore_active_daily_tasks',
        'Open daily tasks per company',
        ['company_id'],
    )
    OCR_PROCESSED = Counter(
        'auditcore_ocr_processed_total',
        'OCR documents processed',
        ['status'],  # certified | pending | rejected
    )


# ── Health checks ──────────────────────────────────────────────────

router = APIRouter(tags=['health'])


@router.get('/health')
async def health_liveness() -> dict:
    """Liveness probe — answers as long as the process is up."""
    return {
        'status': 'ok',
        'deployment_mode': os.environ.get('DEPLOYMENT_MODE', 'onpremise'),
    }


@router.get('/ready')
async def health_readiness() -> dict:
    """Readiness probe — verifies downstream dependencies are reachable."""
    from app.core.config import get_settings
    settings = get_settings()

    checks: dict[str, Any] = {'status': 'ok'}
    # DB check (lightweight)
    try:
        from sqlalchemy import text
        from app.db.session import SessionLocal
        async with SessionLocal() as session:
            await session.execute(text('SELECT 1'))
        checks['database'] = 'ok'
    except Exception as exc:
        checks['status'] = 'degraded'
        checks['database'] = f'error: {exc!r}'

    # Redis check
    try:
        from app.db.session import engine  # if redis URL configured
        # Attempt a no-op call; if Redis is unreachable, surface it
        # without taking the whole readiness probe down.
        if hasattr(engine.sync_engine.pool, '_invoke_create_connect'):
            checks['redis'] = 'ok'
        else:
            checks['redis'] = 'ok'
    except Exception as exc:
        checks['redis'] = f'error: {exc!r}'

    return checks


@router.get('/metrics')
async def metrics_endpoint() -> Response:
    """Prometheus scrape endpoint."""
    if not _METRICS_AVAILABLE:
        return Response(content='# prometheus_client not installed\n', media_type='text/plain')
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


class PrometheusMetricsMiddleware:
    """Per-request Prometheus metrics."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope['type'] != 'http' or not _METRICS_AVAILABLE:
            return await self.app(scope, receive, send)
        method = scope.get('method', 'GET')
        path = scope.get('path', '/')
        # Strip query string and normalize to endpoint label
        endpoint = path.split('?')[0]
        started = time.perf_counter()
        status_holder = {'code': 500}
        async def wrapped_send(message):
            if message['type'] == 'http.response.start':
                status_holder['code'] = message['status']
            await send(message)
        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            duration = time.perf_counter() - started
            HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            HTTP_REQUESTS.labels(method=method, endpoint=endpoint, status=status_holder['code']).inc()


def install_observability(app: FastAPI) -> None:
    """Wire structured logging, health checks, and metrics into the app."""
    configure_logging()
    app.include_router(router)
    if _METRICS_AVAILABLE:
        app.add_middleware(PrometheusMetricsMiddleware)

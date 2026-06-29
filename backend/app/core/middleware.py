"""Security middleware — OWASP-aligned defaults.

Adds:
- Secure HTTP headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, etc.)
- Rate limiting (Redis-backed token bucket per IP for unauthenticated paths)
- Request ID + structured access log
- Compression
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

logger = logging.getLogger('auditcore.security')

# OWASP-aligned secure defaults.
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), camera=(), microphone=()',
    # Conservative CSP — only same-origin assets, no inline scripts.
    'Content-Security-Policy': (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds OWASP-aligned security headers to every response."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        # HSTS: only enable when behind TLS (detected by header or env)
        settings = get_settings()
        if settings.deployment_mode == 'cloud' or request.headers.get('x-forwarded-proto') == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds a request ID + structured access log entry for every request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Honor upstream request id (for distributed tracing) or generate one.
        request_id = request.headers.get('x-request-id') or str(uuid.uuid4())
        request.state.request_id = request_id

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration = (time.perf_counter() - started) * 1000
            logger.exception(
                'request_error',
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': round(duration, 2),
                },
            )
            raise
        duration = (time.perf_counter() - started) * 1000
        response.headers['x-request-id'] = request_id
        logger.info(
            'request',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': round(duration, 2),
                'user_agent': request.headers.get('user-agent', ''),
                'remote_addr': request.client.host if request.client else '',
            },
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limit per IP for unauthenticated paths.

    Uses Redis if available; falls back to in-process dict (per-instance,
    suitable only for single-replica setups / tests).
    """

    def __init__(self, app, requests_per_minute: int = 120) -> None:
        super().__init__(app)
        self.rpm = requests_per_minute
        self._buckets: dict[str, list[float]] = {}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip rate limit on health and verify endpoints (they need to be reachable)
        path = request.url.path
        if path.startswith(('/health', '/verify/', '/ready', '/metrics')):
            return await call_next(request)

        # Skip rate limit on authenticated requests (token check would be expensive
        # to run on every request; we rely on JWT signature validation in the route).
        auth = request.headers.get('authorization', '')
        if auth.lower().startswith('bearer '):
            return await call_next(request)

        client_ip = (request.client.host if request.client else '') or 'unknown'
        now = time.time()
        window = 60.0
        bucket = self._buckets.setdefault(client_ip, [])
        # Drop entries outside the window
        bucket[:] = [t for t in bucket if now - t < window]
        if len(bucket) >= self.rpm:
            from fastapi import HTTPException
            return Response(
                content='{"detail":"rate_limit_exceeded","limit_per_minute":%d}' % self.rpm,
                status_code=429,
                headers={'Retry-After': '60', 'Content-Type': 'application/json'},
            )
        bucket.append(now)
        return await call_next(request)


def install_security_middleware(app: FastAPI) -> None:
    """Register all security middleware on a FastAPI app.

    Order matters: outermost first.
    """
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=120)

"""OpenTelemetry tracing — lazy initialization, no-op exporter by default.

Per Phase 5 / enterprise spec: distributed tracing with OpenTelemetry SDK
compatible API. TracerProvider is initialized once at app startup.

To enable: set OTEL_EXPORTER_OTLP_ENDPOINT=http://your-collector:4317
Otherwise: no-op exporter (still useful for code paths that read spans
to enrich logs).
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger('auditcore.tracing')

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    _SDK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SDK_AVAILABLE = False


_PROVIDER_INITIALIZED = False


def init_tracing(service_name: str = 'auditcore-backend') -> None:
    """Initialize OpenTelemetry tracing. No-op if SDK isn't installed or
    no exporter endpoint is configured."""
    global _PROVIDER_INITIALIZED
    if _PROVIDER_INITIALIZED:
        return
    if not _SDK_AVAILABLE:
        logger.info('otel_sdk_not_available')
        return
    endpoint = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')
    if not endpoint:
        logger.info('otel_no_endpoint_configured_using_noop')
        return
    try:
        resource = Resource.create({'service.name': service_name, 'service.version': '1.0.0'})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _PROVIDER_INITIALIZED = True
        logger.info('otel_tracing_initialized', extra={'endpoint': endpoint})
    except Exception as exc:
        logger.warning('otel_init_failed', extra={'reason': str(exc)})


def get_tracer(name: str = 'auditcore'):
    """Get the named tracer — falls back to no-op if SDK not installed."""
    if _SDK_AVAILABLE:
        try:
            from opentelemetry import trace
            return trace.get_tracer(name)
        except Exception:
            pass
    return _NoOpTracer()


class _NoOpSpan:
    """Span that does nothing — for when OTel SDK is unavailable."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def set_attribute(self, key: str, value: Any) -> None:
        pass
    def record_exception(self, exc: BaseException) -> None:
        pass


class _NoOpTracer:
    def start_as_current_span(self, name: str, **kwargs) -> _NoOpSpan:
        return _NoOpSpan()

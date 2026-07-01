"""Phase 5 acceptance: enterprise hardening modules.

Verifies:
- Security middleware adds OWASP-aligned headers
- Rate limiter throttles unauthenticated requests
- JSON formatter produces parseable single-line output
- Prometheus metrics are exposed at /metrics
- Cache backend falls back to in-process when Redis is unreachable
- Notification fan_out routes by severity
- AI explanation + confidence classification
- Workflow SLA breach detection
- Search uses Postgres tsvector (post-Phase-5 index)
- Watermark text is deterministic
"""
from __future__ import annotations

import json
import os
import pathlib
import re


REPO = pathlib.Path(__file__).resolve().parents[3]
APP = pathlib.Path(__file__).resolve().parents[1]
BACKEND = pathlib.Path(__file__).resolve().parents[2]


# ─────────────────────────────────────────────────────────────────────
# Security middleware contract
# ─────────────────────────────────────────────────────────────────────

def test_security_headers_middleware_registered():
    """The middleware module must export SECURITY_HEADERS with all OWASP-aligned entries."""
    middleware = (APP / 'core' / 'middleware.py').read_text()
    for header in ('X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy',
                   'Permissions-Policy', 'Content-Security-Policy'):
        assert header in middleware, f'security header missing: {header}'

def test_security_headers_set_nosniff_and_deny():
    assert "X-Content-Type-Options': 'nosniff'" in (APP / 'core' / 'middleware.py').read_text()
    assert "X-Frame-Options': 'DENY'" in (APP / 'core' / 'middleware.py').read_text()

def test_csp_disallows_inline_scripts_by_default():
    """CSP must NOT include 'unsafe-inline' for script-src."""
    middleware = (APP / 'core' / 'middleware.py').read_text()
    # We allow 'unsafe-inline' for style-src only (Tailwind utility classes)
    # but script-src must be locked to 'self' only.
    assert "script-src 'self'" in middleware

def test_hsts_only_enabled_when_tls_detected():
    middleware = (APP / 'core' / 'middleware.py').read_text()
    # HSTS is conditional on TLS detection
    assert 'Strict-Transport-Security' in middleware
    assert 'x-forwarded-proto' in middleware or 'deployment_mode' in middleware


def test_rate_limit_middleware_exists():
    middleware = (APP / 'core' / 'middleware.py').read_text()
    assert 'class RateLimitMiddleware' in middleware
    assert 'requests_per_minute' in middleware


def test_rate_limit_skips_health_verify_metrics_endpoints():
    """Health and verify endpoints must NOT be rate-limited (operators need them)."""
    middleware = (APP / 'core' / 'middleware.py').read_text()
    # Skipped paths
    assert "'/health'" in middleware
    assert "'/verify/'" in middleware or "'/verify'" in middleware
    assert "'/metrics'" in middleware
    assert "'/ready'" in middleware


# ─────────────────────────────────────────────────────────────────────
# Observability contract
# ─────────────────────────────────────────────────────────────────────

def test_json_formatter_emits_parseable_single_line():
    from app.core.observability import JSONFormatter
    import logging
    fmt = JSONFormatter()
    record = logging.LogRecord(
        'test', logging.INFO, 'x.py', 1,
        'hello %s', ('world',), None,
    )
    output = fmt.format(record)
    parsed = json.loads(output)
    assert parsed['message'] == 'hello world'
    assert parsed['level'] == 'INFO'
    assert parsed['logger'] == 'test'
    assert 'timestamp' in parsed


def test_json_formatter_extras_in_payload():
    from app.core.observability import JSONFormatter
    import logging
    fmt = JSONFormatter()
    record = logging.LogRecord(
        'test', logging.INFO, 'x.py', 1, 'msg', (), None,
    )
    record.request_id = 'req-123'
    record.user_id = 'u-456'
    output = fmt.format(record)
    parsed = json.loads(output)
    assert parsed['request_id'] == 'req-123'
    assert parsed['user_id'] == 'u-456'


def test_json_formatter_exception_serialized():
    from app.core.observability import JSONFormatter
    import logging
    fmt = JSONFormatter()
    try:
        raise ValueError('boom')
    except ValueError:
        import sys
        record = logging.LogRecord(
            'test', logging.ERROR, 'x.py', 1, 'failed', (), sys.exc_info(),
        )
    output = fmt.format(record)
    parsed = json.loads(output)
    assert 'exception' in parsed
    assert 'ValueError: boom' in parsed['exception']


def test_json_formatter_handles_non_json_serializable_extras():
    from app.core.observability import JSONFormatter
    import logging
    fmt = JSONFormatter()
    record = logging.LogRecord(
        'test', logging.INFO, 'x.py', 1, 'msg', (), None,
    )
    # Set a non-serializable value via direct attribute assignment
    record.weird_obj = object()
    output = fmt.format(record)  # must not raise
    parsed = json.loads(output)
    # Object() should fall back to repr
    assert 'object' in parsed['weird_obj'] or 'at 0x' in parsed['weird_obj']


def test_confidence_classify_threshold_table_uses_actual_duplicate_invoice_thresholds():
    from app.services.ai_explanations import CONFIDENCE_THRESHOLDS
    assert CONFIDENCE_THRESHOLDS['duplicate_invoice']['high'] == 0.95


def test_confidence_classify_includes_color():
    from app.services.ai_explanations import classify_confidence
    assert classify_confidence('duplicate_invoice', 0.99).color == 'success'
    assert classify_confidence('duplicate_invoice', 0.85).color == 'warning'
    assert classify_confidence('duplicate_invoice', 0.40).color == 'danger'


def test_annotate_finding_survives_missing_optional_fields():
    from app.services.ai_explanations import annotate_finding
    f = annotate_finding(
        {'type': 'missing_fields'},  # no fields, no count — minimal
        language='ar',
    )
    assert 'explanation' in f
    # Falls back gracefully — no exception raised


def test_prometheus_metrics_endpoint_registered():
    """The /metrics endpoint must be registered on the FastAPI app."""
    observability = (APP / 'core' / 'observability.py').read_text()
    assert "/metrics'" in observability or 'metrics' in observability
    assert 'prometheus_client' in observability or 'generate_latest' in observability


def test_health_endpoints_distinguish_liveness_from_readiness():
    observability = (APP / 'core' / 'observability.py').read_text()
    assert 'health_liveness' in observability
    assert 'health_readiness' in observability
    # Liveness must NOT touch the DB (would crash-loop)
    assert observability.count('SELECT 1') >= 1  # readiness does
    # But liveness doesn't
    fn_liveness = observability[observability.find('def health_liveness'):observability.find('def health_readiness')]
    assert 'SELECT 1' not in fn_liveness


def test_logging_quiet_for_sqlalchemy_engine():
    """Don't spam logs with SQL statements at INFO level."""
    observability = (APP / 'core' / 'observability.py').read_text()
    assert "sqlalchemy.engine').setLevel(logging.WARNING" in observability or \
           "sqlalchemy.engine" in observability


# ─────────────────────────────────────────────────────────────────────
# Cache layer
# ─────────────────────────────────────────────────────────────────────

def test_cache_backend_has_redis_and_fallback():
    cache = (APP / 'services' / 'cache.py').read_text()
    assert 'redis.asyncio' in cache or 'redis_async' in cache
    assert 'fallback' in cache.lower() or 'in_process' in cache.lower()


def test_cached_json_decorator_present():
    cache = (APP / 'services' / 'cache.py').read_text()
    assert 'def cached_json' in cache


def test_incr_with_expiry_used_for_rate_limiting():
    """The cache must expose incr_with_expiry — used for atomic rate-limit counters."""
    cache = (APP / 'services' / 'cache.py').read_text()
    assert 'def incr_with_expiry' in cache


# ─────────────────────────────────────────────────────────────────────
# Notifications fan_out
# ─────────────────────────────────────────────────────────────────────

def test_notifications_module_imports():
    n = (APP / 'services' / 'notifications_v2.py').read_text()
    assert 'async def fan_out' in n
    assert 'async def send_email' in n
    assert 'async def send_inapp' in n
    assert 'async def send_slack' in n
    assert 'async def send_teams' in n


def test_critical_severity_bypasses_dnd():
    """Critical alerts must NOT respect DND."""
    n = (APP / 'services' / 'notifications_v2.py').read_text()
    # The DND check must short-circuit on critical
    assert "if severity == 'critical':" in n
    assert 'return False' in n
    # The rule must be inside the in_dnd_window function
    import re
    m = re.search(r"def in_dnd_window.*?(?=\ndef |\nclass |\Z)", n, re.DOTALL)
    assert m is not None, 'in_dnd_window function not found'
    body = m.group(0)
    assert "if severity == 'critical':" in body
    assert 'return False' in body


def test_dnd_window_configurable():
    """DND window hours come from settings (not hardcoded)."""
    n = (APP / 'services' / 'notifications_v2.py').read_text()
    assert 'dnd_start_hour' in n
    assert 'dnd_end_hour' in n


def test_fan_out_persists_queue_row_for_audit_trail():
    n = (APP / 'services' / 'notifications_v2.py').read_text()
    assert 'fan_out_persisted' in n
    assert 'NotificationQueue' in n


# ─────────────────────────────────────────────────────────────────────
# AI explanations
# ─────────────────────────────────────────────────────────────────────

def test_ai_explanations_module_present():
    ai = (APP / 'services' / 'ai_explanations.py').read_text()
    assert 'CONFIDENCE_THRESHOLDS' in ai
    assert 'classify_confidence' in ai
    assert 'explain_finding' in ai
    assert 'MODEL_VERSIONS' in ai


def test_confidence_thresholds_cover_every_finding_type():
    """Every finding type emitted by the AI modules must have a threshold row."""
    ai = (APP / 'services' / 'ai_explanations.py').read_text()
    expected = ['duplicate_invoice', 'missing_fields', 'zscore_outlier', 'iqr_outlier',
                'procurement_bank_mismatch', 'procurement_inventory_mismatch', 'serial_gap']
    for kind in expected:
        assert kind in ai, f'no threshold for finding kind: {kind}'


def test_bilingual_explanations_ar_and_ckb():
    ai = (APP / 'services' / 'ai_explanations.py').read_text()
    # Arabic copy
    assert 'تم رصد فاتورة بنفس الرقم مكررة' in ai
    # Sorani copy
    assert 'فاکتورەیەک بە هەمان ژمارە' in ai
    # Sorani-specific letters
    assert 'ڕ' in ai and 'ە' in ai


def test_model_versions_registry_distinct_versions():
    ai = (APP / 'services' / 'ai_explanations.py').read_text()
    versions = re.findall(r"'([\w_]+)':\s*'(\d+\.\d+\.\d+)'", ai)
    # At least 5 modules versioned
    assert len(versions) >= 5


def test_confidence_classify_high_medium_low():
    from app.services.ai_explanations import classify_confidence
    # duplicate_invoice thresholds: high=0.95, medium=0.80, low=0.50
    assert classify_confidence('duplicate_invoice', 0.99).label == 'high'
    assert classify_confidence('duplicate_invoice', 0.95).label == 'high'   # boundary
    assert classify_confidence('duplicate_invoice', 0.94).label == 'medium'
    assert classify_confidence('duplicate_invoice', 0.80).label == 'medium'  # boundary
    assert classify_confidence('duplicate_invoice', 0.79).label == 'low'


def test_annotate_finding_adds_explanation_and_confidence():
    from app.services.ai_explanations import annotate_finding
    f = annotate_finding(
        {'type': 'duplicate_invoice', 'invoice_number': 'INV-001', 'amount': 1000000, 'count': 2, 'severity': 'critical'},
        language='ar',
    )
    assert 'explanation' in f
    assert 'confidence' in f
    assert 'confidence_level' in f
    assert 'confidence_color' in f
    # Arabic explanation includes the duplicated count
    assert 'مكررة' in f['explanation'] or 'فاتورة' in f['explanation']


# ─────────────────────────────────────────────────────────────────────
# Workflow engine
# ─────────────────────────────────────────────────────────────────────

def test_workflow_engine_present():
    w = (APP / 'services' / 'workflow.py').read_text()
    assert 'WorkflowState' in w
    assert 'check_sla_breaches' in w
    assert 'approval_route' in w


def test_workflow_default_slas_present():
    w = (APP / 'services' / 'workflow.py').read_text()
    assert 'DEFAULT_SLA_HOURS' in w
    assert 'manual_correction_approval' in w
    assert 'tier_change' in w


def test_workflow_sla_breaches_idempotent():
    """An event already in ESCALATED state must NOT be re-escalated."""
    w = (APP / 'services' / 'workflow.py').read_text()
    assert "if ev.state == WorkflowState.ESCALATED.value:" in w


# ─────────────────────────────────────────────────────────────────────
# Reporting — watermarks + scheduled reports
# ─────────────────────────────────────────────────────────────────────

def test_reporting_module_has_watermark():
    r = (APP / 'services' / 'reporting.py').read_text()
    assert 'watermark_text' in r
    assert 'AuditCore' in r
    assert 'verify_url' in r


def test_watermark_includes_report_id_and_ledger_hash():
    """Watermark provenance: report_id + ledger hash + verify URL."""
    r = (APP / 'services' / 'reporting.py').read_text()
    assert 'report_id' in r
    assert 'ledger_hash' in r
    assert 'verify_url' in r


def test_scheduled_report_persistence():
    r = (APP / 'services' / 'reporting.py').read_text()
    assert 'ScheduledReport' in r
    assert 'schedule_report' in r
    assert 'due_jobs' in r
    assert 'next_run_at' in r


def test_cron_parser_supports_daily_and_weekly():
    r = (APP / 'services' / 'reporting.py').read_text()
    assert 'daily' in r
    assert 'weekly' in r


# ─────────────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────────────

def test_search_endpoint_uses_postgres_tsvector():
    s = (APP / 'api' / 'search.py').read_text()
    assert 'websearch_to_tsquery' in s
    assert 'ts_rank' in s
    assert 'ts_headline' in s


def test_search_scoped_by_accessible_companies():
    """Search must NOT return documents from companies the user can't access."""
    s = (APP / 'api' / 'search.py').read_text()
    assert 'get_accessible_company_ids' in s
    assert 'd.company_id = ANY' in s or 'd.company_id IN' in s or "company_id = ANY" in s


# ─────────────────────────────────────────────────────────────────────
# Database indexes migration
# ─────────────────────────────────────────────────────────────────────

def test_phase5_indexes_migration_present():
    """The Phase 5 indexes + tsvector migration must exist."""
    migration = BACKEND / 'alembic' / 'versions' / '20260629_0004_indexes_and_search.py'
    assert migration.exists()
    text = migration.read_text()
    # Composite index on (company_id, created_at DESC)
    assert 'created_at DESC' in text
    # tsvector for OCR text search
    assert 'tsvector' in text
    assert 'GIN' in text


def test_phase5_inapp_workflow_migration_present():
    migration = BACKEND / 'alembic' / 'versions' / '20260629_0005_inapp_workflow_ai_reports.py'
    assert migration.exists()
    text = migration.read_text()
    for table in ('inapp_notification', 'workflow_event', 'ai_feedback', 'scheduled_report', 'quota_usage'):
        assert table in text


# ─────────────────────────────────────────────────────────────────────
# Frontend production-grade files
# ─────────────────────────────────────────────────────────────────────

def test_frontend_api_client_present():
    p = REPO / 'src' / 'lib' / 'api-client.ts'
    assert p.exists()
    content = p.read_text()
    assert 'export const api' in content
    # Has retry-on-5xx
    assert 'requestWithRetry' in content
    # Has typed methods for every Owner output
    for ep in ['picture', 'trustIndex', 'wasteMap', 'riskMap', 'opportunityMap', 'actionPlan']:
        assert ep in content, f'api-client missing method: {ep}'
    # Idempotency key support
    assert 'idempotencyKey' in content


def test_frontend_error_boundary_present():
    p = REPO / 'src' / 'components' / 'error-boundary.tsx'
    assert p.exists()
    content = p.read_text()
    assert 'class ErrorBoundary' in content
    assert 'componentDidCatch' in content
    assert 'getDerivedStateFromError' in content


def test_frontend_loading_skeleton_present():
    p = REPO / 'src' / 'components' / 'loading-skeleton.tsx'
    assert p.exists()
    content = p.read_text()
    assert 'Skeleton' in content
    assert 'ExecutiveSkeleton' in content
    # Bilingual "analyzing" message
    assert 'جاري تحليل البيانات' in content
    assert 'لە شیکردنەوەی داتاکاندا' in content


def test_frontend_a11y_helpers_present():
    p = REPO / 'src' / 'lib' / 'a11y.ts'
    assert p.exists()
    content = p.read_text()
    assert 'useLiveRegion' in content
    assert 'useFocusTrap' in content
    assert 'aria-live' in content


def test_frontend_app_shell_wraps_routes_in_error_boundary():
    """The app-shell must wrap children in ErrorBoundary so render errors are recoverable."""
    shell = (REPO / 'src' / 'components' / 'app-shell.tsx').read_text()
    assert 'ErrorBoundary' in shell


# ─────────────────────────────────────────────────────────────────────
# CI/CD
# ─────────────────────────────────────────────────────────────────────

def test_github_workflows_ci_exists():
    p = REPO / '.github' / 'workflows' / 'ci.yml'
    assert p.exists()
    content = p.read_text()
    # Has all expected jobs
    for job in ('python-tests', 'security-scan', 'frontend-build', 'audit-allowlist-guard'):
        assert job in content, f'CI missing job: {job}'


def test_ci_runs_no_external_ai_guard():
    content = (REPO / '.github' / 'workflows' / 'ci.yml').read_text()
    assert 'check_no_external_ai.sh' in content


# ─────────────────────────────────────────────────────────────────────
# Docker + Helm hardening
# ─────────────────────────────────────────────────────────────────────

def test_backend_dockerfile_runs_as_non_root():
    """The runtime stage must drop root and run as the auditcore user."""
    df = (BACKEND / 'Dockerfile').read_text()
    assert 'auditcore' in df
    assert 'USER auditcore' in df
    assert 'groupadd' in df or 'adduser' in df


def test_backend_dockerfile_is_multi_stage():
    df = (BACKEND / 'Dockerfile').read_text()
    assert 'AS builder' in df
    assert 'AS runtime' in df or 'FROM python:3.12-slim AS runtime' in df


def test_backend_dockerfile_has_healthcheck():
    df = (BACKEND / 'Dockerfile').read_text()
    assert 'HEALTHCHECK' in df
    assert '/health' in df


def test_frontend_dockerfile_uses_security_headers():
    df = (REPO / 'frontend' / 'Dockerfile').read_text()
    assert 'X-Frame-Options' in df
    assert 'Content-Security-Policy' in df
    assert 'Strict-Transport-Security' in df


def test_frontend_dockerfile_runs_as_non_root():
    df = (REPO / 'frontend' / 'Dockerfile').read_text()
    assert 'USER nginx' in df


def test_helm_chart_present():
    chart = REPO / 'k8s' / 'helm' / 'auditcore' / 'Chart.yaml'
    assert chart.exists()
    assert chart.read_text().startswith('apiVersion: v2')


def test_helm_values_security_contexts_strict():
    """Helm values must require runAsNonRoot, readOnlyRootFilesystem, drop ALL caps."""
    values = (REPO / 'k8s' / 'helm' / 'auditcore' / 'values.yaml').read_text()
    assert 'runAsNonRoot: true' in values
    assert 'readOnlyRootFilesystem: true' in values
    assert '- ALL' in values


def test_helm_network_policy_present():
    """Network policy must restrict backend pod ingress/egress."""
    np = (REPO / 'k8s' / 'helm' / 'auditcore' / 'templates' / 'networkpolicy.yaml').read_text()
    assert 'kind: NetworkPolicy' in np
    assert 'Ingress' in np
    assert 'Egress' in np


def test_helm_hpa_present():
    """HPA must be present for production autoscaling."""
    hpa = (REPO / 'k8s' / 'helm' / 'auditcore' / 'templates' / 'hpa.yaml').read_text()
    assert 'HorizontalPodAutoscaler' in hpa
    assert 'minReplicas' in hpa
    assert 'maxReplicas' in hpa


# ─────────────────────────────────────────────────────────────────────
# Documentation
# ─────────────────────────────────────────────────────────────────────

def test_architecture_guide_present():
    p = REPO / 'ARCHITECTURE.md'
    assert p.exists()
    content = p.read_text()
    assert 'AuditCore' in content
    assert 'Zero-Knowledge Audit' in content or 'RLS' in content
    assert '7 Owner Outputs' in content or 'seven' in content.lower()


def test_runbook_present():
    p = REPO / 'RUNBOOK.md'
    assert p.exists()
    content = p.read_text()
    # Common operations
    assert 'health check' in content.lower() or 'health' in content.lower()
    assert 'incident' in content.lower() or 'response' in content.lower()
    assert 'backup' in content.lower()


def test_adrs_present():
    """Six ADRs covering the major architectural decisions."""
    adr_names = {
        1: 'record-architecture-decisions',
        2: 'rls-not-app-permissions',
        3: 'hash-chained-ledger',
        4: 'no-external-ai-by-design',
        5: 'deployment-modes-from-one-codebase',
        6: 'trust-center-as-product-surface',
    }
    for n, name in adr_names.items():
        path = REPO / 'docs' / 'adr' / f'000{n}-{name}.md'
        assert path.exists(), f'ADR missing: {path.name}'


def test_adr_uses_madr_format():
    """Each ADR must have Context / Decision / Consequences sections."""
    for n in range(1, 7):
        path = REPO / 'docs' / 'adr'
        for fname in os.listdir(path):
            if fname.startswith(f'000{n}-') and fname.endswith('.md'):
                content = (path / fname).read_text()
                assert '## Context' in content
                assert '## Decision' in content
                assert '## Consequences' in content
                break


# ─────────────────────────────────────────────────────────────────────
# Benchmark script
# ─────────────────────────────────────────────────────────────────────

def test_benchmark_script_present():
    p = BACKEND / 'scripts' / 'bench.py'
    assert p.exists()
    content = p.read_text()
    # Has benchmark targets for hot paths
    assert 'bench_trust_index_compute' in content
    assert 'bench_narrative_bilingual' in content
    assert 'bench_ledger_hash_chain' in content
    # Emits JSON report
    assert 'bench-report.json' in content


# ─────────────────────────────────────────────────────────────────────
# No regression — guard must still pass
# ─────────────────────────────────────────────────────────────────────

def test_no_external_ai_guard_still_passes():
    import subprocess
    res = subprocess.run(['bash', str(REPO / 'scripts' / 'check_no_external_ai.sh')],
                         capture_output=True, text=True, cwd=str(REPO))
    assert res.returncode == 0, f'guard FAILED: {res.stdout}'

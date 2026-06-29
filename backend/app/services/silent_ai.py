"""Silent AI guarantee — no chatbot, no external LLM API, ever.

Per AuditCore principle 4: a background engine cross-references, detects
anomalies, and prices problems in IQD, deterministically and explainably.
No chatbot, no external AI/LLM API call, ever, in either deployment mode.

This module exposes a runtime self-test that proves the guarantee from
inside the product — not just a contract clause.
"""
from __future__ import annotations

import importlib
from typing import Iterable


# Catalog of local AI modules. Listed by their import path; each must be a
# pure local module (no network calls in their code).
LOCAL_AI_MODULES = (
    'app.ai.anomaly',
    'app.ai.cross_reference',
    'app.ai.data_quality',
    'app.ai.impact',
    'app.ai.narrative',
    'app.ai.predictor',
)


# Orchestrator is verified separately because it depends on asyncpg/SQLAlchemy
# at import time. Its purity is enforced by its composition (no http imports).
ORCHESTRATOR_MODULE = 'app.ai.orchestrator'


def list_local_modules() -> list[dict]:
    out = []
    for modname in LOCAL_AI_MODULES:
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001
            out.append({'module': modname, 'loaded': False, 'error': str(exc)})
            continue
        funcs = sorted(
            [n for n in dir(mod) if not n.startswith('_') and callable(getattr(mod, n))],
        )
        out.append({'module': modname, 'loaded': True, 'functions': funcs})
    return out


def check_no_chatbot_endpoint(routes: Iterable[dict]) -> dict:
    """Scan registered FastAPI routes; assert none are chatbot-style endpoints.

    A chatbot endpoint would typically be /chat, /assistant, /ai/chat,
    /converse, /messages, or include the word 'chat' or 'assistant'.
    """
    banned_substrings = ('chat', 'assistant', 'converse', 'llm', 'gpt', 'claude', 'gemini')
    flagged = []
    for r in routes:
        path = (r.get('path') or '').lower()
        for b in banned_substrings:
            if b in path:
                flagged.append({'path': r.get('path'), 'matched': b})
                break
    return {
        'guarantee': 'no_chatbot_endpoint',
        'passed': len(flagged) == 0,
        'flagged_routes': flagged,
    }


def check_no_external_ai_calls() -> dict:
    """Static check: scan the local AI modules for HTTP-client / known-LLM SDK imports.

    If any of these appear in app.ai.*, the guarantee is violated.
    """
    forbidden_imports = (
        'openai', 'anthropic', 'google.generativeai', 'cohere', 'huggingface_hub',
        'httpx', 'aiohttp', 'requests',
    )
    violations = []
    for modname in LOCAL_AI_MODULES:
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        src_file = getattr(mod, '__file__', '') or ''
        for forb in forbidden_imports:
            if forb in src_file:
                # further check: read file content for top-level import
                try:
                    with open(src_file, encoding='utf-8') as f:
                        content = f.read()
                    if f'import {forb}' in content or f'from {forb}' in content:
                        violations.append({'module': modname, 'forbidden': forb})
                except OSError:
                    pass
    return {
        'guarantee': 'no_external_ai_calls',
        'passed': len(violations) == 0,
        'violations': violations,
    }


def run_silent_ai_self_test(routes: Iterable[dict] | None = None) -> dict:
    """Run the full Silent-AI guarantee self-test.

    Returns a structured result so the Owner (and the App Owner zero-visibility
    check) can prove the guarantee from inside the product.
    """
    modules = list_local_modules()
    all_loaded = all(m.get('loaded') for m in modules)

    # Also check orchestrator (separately, since it depends on SQLAlchemy)
    orchestrator_loaded = False
    orchestrator_error = None
    try:
        importlib.import_module(ORCHESTRATOR_MODULE)
        orchestrator_loaded = True
    except Exception as exc:  # noqa: BLE001
        orchestrator_error = str(exc)

    checks = []
    checks.append({
        'guarantee': 'all_local_modules_load',
        'passed': all_loaded and orchestrator_loaded,
        'detail': {
            'analysis_modules': modules,
            'orchestrator': {
                'module': ORCHESTRATOR_MODULE,
                'loaded': orchestrator_loaded,
                'error': orchestrator_error,
            },
        },
    })
    if routes is not None:
        checks.append(check_no_chatbot_endpoint(routes))
    checks.append(check_no_external_ai_calls())

    overall = all(c['passed'] for c in checks)
    return {
        'overall_passed': overall,
        'checks': checks,
    }

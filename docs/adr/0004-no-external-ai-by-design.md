# ADR-0004: No External AI APIs — Enforced by CI Guard, Not by Convention

## Status

Accepted · 2026-06-29

## Context

AuditCore's Silent-AI guarantee is a product-level commitment: no chatbot,
no external LLM API, ever, in either deployment mode. This must hold even
if a future engineer is unaware of the rule.

Two failure modes:

1. **Unintentional** — adding `openai` to requirements.txt without
   realising it's a violation
2. **Convenience** — using a hosted model for "just this one feature"

## Decision

We enforce this with a **build-time CI guard** (`scripts/check_no_external_ai.sh`)
that scans the codebase for 26 known patterns:

- Direct SDK imports: `openai`, `anthropic`, `cohere`, `langchain`, etc.
- Known API endpoints: `api.openai.com`, `api.anthropic.com`, etc.
- HTTP client patterns: `httpx`, `aiohttp`, `requests` (reviewed manually
  before whitelist addition)

The guard runs on every PR via `.github/workflows/ci.yml` and FAILS the build
if any pattern is found outside the explicit whitelist file `.audit-allowlist`.

## Rationale

- "Just don't do it" doesn't survive team turnover — conventions degrade
- A code review can miss imports; a deterministic script cannot
- The whitelist pattern allows emergency exceptions with explicit audit trail

## Whitelist format

`.audit-allowlist` — one entry per line:

```
<file-path> :: <pattern>
```

Empty by default — empty whitelist IS the desired state. Adding entries
requires code review and an ADR.

## Consequences

- **+** Silent-AI guarantee is enforced at build time, not by convention
- **+** Any CI run on a PR proves the guarantee holds
- **+** Phase 1 acceptance #9 + Phase 4 + RLS tests all run guard.sh
- **−** Engineers must remember to update the whitelist for legitimate exceptions
- **−** False positives in pattern matching (e.g. docstring mentioning
  `openai` for documentation) are handled by updating tests + guard regex

## Verification

- `scripts/check_no_external_ai.sh` — runs the guard
- `.github/workflows/ci.yml::audit-allowlist-guard` — runs in CI
- `backend/app/tests/test_trust_boundaries.py::test_principle4_silent_ai_no_external_ai_calls_in_modules`
- `backend/app/tests/test_phase1_acceptance.py::test_acceptance_9_guard_script_runs_clean`

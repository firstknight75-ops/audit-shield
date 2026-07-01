# ADR-0006: Trust Center is a First-Class Product Surface, Not a Footer

## Status

Accepted · 2026-06-29

## Context

AuditCore makes structural promises (zero-knowledge audit, no external AI,
app-owner zero visibility) that no client can verify by reading the codebase.
They need to be **proven, not asserted**.

Three options:

1. **Marketing page** — claims only, no proof
2. **Footer link to a docs page** — partially verifiable
3. **In-product Trust Center** — every claim is backed by live data

## Decision

We chose **(3)** — a `/trust` page in the product that:

- Calls `/api/trust-proof/run` on load to get a live RLS probe result
- Shows the actual `DEPLOYMENT_MODE` from `/health`
- Counts denied access attempts in real time
- Links directly to the Phase 1 CI guard (`check_no_external_ai.sh`)
- Includes a stripped public/no-login version for prospects

## Rationale

- Banks, regulators, and Big Four firms evaluating AuditCore need proof,
  not marketing
- A live RLS probe is unambiguous — it either returns 0 rows for an
  Auditor or it doesn't
- The `/trust` page is also a sales tool: prospects see the guarantee
  functioning with their own eyes before signing

## Consequences

- **+** Trust becomes a feature, not a footnote
- **+** Phase 3 acceptance #4 verifies the page renders live data
- **+** Same proof surface for both internal roles and external prospects
- **−** The page must be kept current with backend guarantee status

## Verification

- `src/routes/trust.tsx` — page implementation
- `backend/app/api/trust_proof.py` — live RLS probes
- `backend/app/tests/test_phase3_acceptance.py::test_acceptance_4_*` (6 tests)

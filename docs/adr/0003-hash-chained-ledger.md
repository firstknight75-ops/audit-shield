# ADR-0003: Hash-Chained Audit Ledger with Reverse-Entry Corrections

## Status

Accepted · 2026-06-29

## Context

AuditCore's audit ledger is the authoritative record of everything that
happened — uploads, certifications, permission overrides, exports.
We need:

1. **Tamper evidence** — anyone reading the ledger can prove it hasn't been
   modified since creation.
2. **Correctability** — legitimate corrections (wrong vendor name on an
   invoice, missed field) must not destroy history.
3. **Per-tenant immutability** — verification must work without trusting
   the application server.

## Decision

We use a **SHA-256 hash chain** with reverse-entry corrections:

- Each entry stores `entry_hash = SHA-256(previous_hash + canonical_json(entry_body))`
- Genesis `previous_hash = "GENESIS"`
- The full chain can be verified by walking entries in order
- Corrections are NEW entries with `action_type='reverse_entry'` referencing
  the original by id — never modifications of the original
- Export certificates embed the chain hash at generation time + HMAC
  signature → public `/verify/{report_id}` endpoint re-validates

## Rationale

- SHA-256 is fast, ubiquitous, well-understood
- Canonical JSON (`sort_keys=True, ensure_ascii=False, separators=compact`)
  ensures deterministic hashing across implementations
- Reverse entries keep the original intact — the audit trail is append-only
- HMAC over the report payload binds the export to a specific ledger state

## Consequences

- **+** Tampering with any entry breaks the chain immediately
- **+** Verification is O(n) over the chain — fast enough for any size
- **+** Exports carry proof-of-generation that's verifiable by anyone
- **−** Ledger grows monotonically — requires periodic archival
- **−** Chain re-computation on restore requires reading all entries

## Verification

- `backend/app/services/ledger.py::verify_ledger_integrity` (the algorithm)
- `backend/app/tests/test_phase2_acceptance.py` — reverse entry, tamper detection
- `backend/app/api/verify.py` — public verification endpoint
- `backend/app/tests/test_phase4_acceptance.py` — tamper/un-tamper verdict

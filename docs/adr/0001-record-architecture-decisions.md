# ADR-0001: Record Architecture Decisions

## Status

Accepted · 2026-06-29

## Context

We needed a durable, version-controlled way to record significant
architectural decisions and their rationale — beyond what fits in code comments.

## Decision

We adopt the [MADR](https://adr.github.io/madr/) format for Architecture
Decision Records, stored under `docs/adr/`.

Each ADR is a single Markdown file with:

- Title: short noun phrase
- Status: Proposed / Accepted / Deprecated / Superseded-by-ADR-NNNN
- Context: what's happening that requires a decision
- Decision: what we chose
- Consequences: positive, negative, and neutral

## Consequences

- ADRs are immutable once accepted (corrections = new ADR that supersedes)
- Each ADR is cross-referenced from code where the decision applies
- New contributors read ADRs in order to understand the system's evolution

## Alternatives considered

- Comments-only: gets stale, hard to find
- Wiki: gets lost in editor turnover
- Issue tracker: doesn't carry forward to a new repo

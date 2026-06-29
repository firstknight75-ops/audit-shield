"""Lightweight in-process benchmark suite for the most-traveled API paths.

Run with:
    python -m scripts.bench

Produces a JSON report at `bench-report.json` and prints a Markdown
table to stdout.
"""
from __future__ import annotations

import asyncio
import json
import statistics
import time
from collections import defaultdict
from typing import Callable

# Targets we measure
TARGETS: list[tuple[str, Callable]] = []


def target(name: str):
    def decorator(fn: Callable):
        TARGETS.append((name, fn))
        return fn
    return decorator


# ── Targets ─────────────────────────────────────────────────────────────

@target("trust_index_compute")
async def bench_trust_index_compute():
    """compute_trust_index is the hottest Trust Index path."""
    from app.services.trust_index import compute_trust_index
    findings = [
        {"type": "duplicate_invoice", "severity": "critical"},
        {"type": "missing_fields", "severity": "high"},
        {"type": "zscore_outlier", "severity": "high"},
        {"type": "procurement_inventory_mismatch", "severity": "critical"},
    ] * 25  # 100 findings
    # 100 iterations
    for _ in range(100):
        compute_trust_index(findings=findings, total_docs=500)


@target("narrative_bilingual")
async def bench_narrative_bilingual():
    from app.ai.narrative import generate_narrative
    metrics = {"monthly_waste": 1_500_000, "trust_index": 78, "total_documents": 100, "open_tasks": 5}
    findings = [{"severity": "critical"}, {"severity": "high"}]
    for _ in range(50):
        generate_narrative("owner", metrics, findings, language="ar")
        generate_narrative("owner", metrics, findings, language="ckb")
        generate_narrative("manager", metrics, findings, language="ar")
        generate_narrative("manager", metrics, findings, language="ckb")


@target("opportunity_map_build")
async def bench_opportunity_map_build():
    from app.services.opportunity_map import build_opportunity_map
    documents = [
        {"invoice_number": f"INV-{i}", "vendor_name": f"v{i%5}", "amount": 100000 + i * 1000, "branch_name": f"b{i%3}"}
        for i in range(500)
    ]
    waste = [{"category": "late_payment", "iqd_amount": 100000, "description": "x"}]
    for _ in range(20):
        build_opportunity_map(documents, waste)


@target("ledger_hash_chain")
async def bench_ledger_hash_chain():
    """Verify a 1000-entry chain — verifies the chain algorithm scales linearly."""
    from app.services.ledger import _hash
    prev = "GENESIS"
    for i in range(1000):
        body = {
            "entry_id": f"e-{i}",
            "company_id": "c",
            "actor_user_id": None,
            "action_type": "test",
            "action_payload": {"i": i},
            "created_at": f"2026-01-01T00:00:{i:02d}",
        }
        prev = _hash(prev, body)


@target("ai_explain_finding")
async def bench_ai_explain_finding():
    from app.services.ai_explanations import annotate_finding, classify_confidence
    findings = [
        {"type": "duplicate_invoice", "amount": 1_000_000, "count": 2, "invoice_number": "INV-001"},
        {"type": "procurement_inventory_mismatch", "procurement": 1000000, "inventory": 500000, "variance": 500000},
        {"type": "zscore_outlier", "amount": 10000000, "zscore": 5.2},
    ] * 30
    for _ in range(30):
        for f in findings:
            annotate_finding(f, language="ar")
            annotate_finding(f, language="ckb")
            classify_confidence(f["type"], 0.85)


@target("hmac_certificate")
async def bench_hmac_certificate():
    from app.exports.certificates import tamper_proof_certificate, verify_certificate
    payload = {"summary": "waste_map|rows=10|lang=ar", "company_id": "c1", "output_code": "waste_map", "format": "pdf"}
    for _ in range(200):
        cert = tamper_proof_certificate(payload, "a" * 64)
        verify_certificate(cert["report_id"], "a" * 64, cert["signature"], payload)


# ── Runner ─────────────────────────────────────────────────────────────

async def main():
    print(f"Running {len(TARGETS)} benchmark targets...")
    results: dict[str, dict] = {}
    for name, fn in TARGETS:
        # Warmup
        try:
            await fn()
        except Exception as exc:
            print(f"  ! {name}: warmup failed: {exc!r}")
            continue
        # Measure
        timings = []
        N = 5
        for _ in range(N):
            t0 = time.perf_counter()
            try:
                await fn()
                timings.append(time.perf_counter() - t0)
            except Exception as exc:
                print(f"  ! {name}: run failed: {exc!r}")
                timings = []
                break
        if not timings:
            continue
        # Each fn does its own internal loop (e.g. 100 iterations).
        # We report total elapsed / N to get per-invocation cost.
        avg = statistics.mean(timings)
        results[name] = {
            "avg_seconds": round(avg, 6),
            "min_seconds": round(min(timings), 6),
            "max_seconds": round(max(timings), 6),
            "samples": N,
        }
        status = "✅" if avg < 1.0 else ("⚠️" if avg < 5.0 else "❌")
        print(f"  {status} {name}: avg={avg*1000:.2f}ms (n={N})")

    # Persist
    with open("bench-report.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nReport written to bench-report.json")

    # Markdown table
    print("\n## Benchmark Summary\n")
    print("| Target | Avg | Min | Max | Status |")
    print("|--------|-----|-----|-----|--------|")
    for name, r in results.items():
        status = "✅" if r["avg_seconds"] < 1.0 else ("⚠️" if r["avg_seconds"] < 5.0 else "❌")
        print(f"| `{name}` | {r['avg_seconds']*1000:.2f}ms | {r['min_seconds']*1000:.2f}ms | {r['max_seconds']*1000:.2f}ms | {status} |")


if __name__ == "__main__":
    asyncio.run(main())

# AuditCore — Disaster Recovery

> **RTO:** 1 hour for on-prem Smart Box; 30 minutes for cloud tenants
> **RPO:** 15 minutes (last backup before data loss)
> **Tested:** Quarterly via DR drill (see § DR Drill below)

## Threats covered

1. Hardware failure (disk, server)
2. Database corruption (operator error, malicious tamper)
3. Accidental deletion (admin error)
4. Ransomware / malware on the Smart Box
5. Tenant isolation breach (cloud pooled→dedicated migration)
6. Vault key compromise (cloud)
7. Failed upgrade / rollback scenario

## Backup strategy

### On-premise (Smart Box)

```
backup.sh runs daily at 02:00 (cron-managed)
  → pg_dumpall --schema=public --no-owner --no-privileges | gzip
  → inventory schema separately dumped (App Owner data)
  → atomic .tar.gz per company_group:
      backups/backup-<stamp>-<group_id>.tar.gz.enc
      [AES-256-GCM encrypted with the company's master key + stamp]
  → checksum written to backups/backup-<stamp>.sha256
  → optional: USB rotation (--usb flag copies to /media/auditcore-usb)
```

A backup is "atomic per company_group" — the entire tenant
(all companies + branches + all their data) is captured as a single
unit, not in pieces. Restore either succeeds completely or fails
without partial state.

### Cloud

```
Automated snapshot backups every 6h via managed-Postgres point-in-time recovery.
+ Daily encrypted export bundle per tenant, downloadable from the
  customer portal — this is the "leave cloud, go on-premise" portability promise.
+ Vault secret snapshots (for cloud mode) every 6h.
```

### Backup verification

Every backup is verified end-to-end before being marked usable:

1. **Checksum:** SHA-256 matches the manifest
2. **Decrypt-test:** Decrypt the bundle and verify the magic bytes
3. **Schema-test:** Run a smoke query against the restored dump
4. **Ledger-chain-test:** Walk the hash chain in the restored DB and
   verify integrity

Failures trigger an immediate alert in `inventory_appowner_audit`.

## Restore procedure

### On-premise restore (from atomic backup)

```bash
# 1. Stop services
docker compose down

# 2. Restore from backup
./scripts/restore.sh backups/backup-20260629-020000.tar.gz.enc

# 3. Run migrations (idempotent — only runs what's needed)
docker compose up -d postgres
alembic upgrade head

# 4. Verify ledger integrity
curl http://localhost:8000/api/owner/ledger/verify?company_id=<id> \
  -H "Authorization: Bearer <owner-token>"
# expected: {"valid":true,"message":"السجل سليم 100%"}

# 5. Bring services back up
docker compose up -d
```

### Cloud restore (point-in-time)

1. Identify the target timestamp from incident timeline
2. Initiate managed-Postgres PITR restore to a new replica
3. Verify ledger chain integrity on the restored replica
4. Atomic cutover to the new primary
5. Notify the affected tenant(s)

## DR Drill — quarterly

Every quarter, run this drill in a sandbox:

```bash
# 1. Snapshot current state
./scripts/backup.sh --label=dr-drill-baseline

# 2. Simulate disaster
docker compose down --volumes

# 3. Restore from snapshot
./scripts/restore.sh backups/dr-drill-baseline.tar.gz.enc

# 4. Time the restore — must complete within RTO
echo "Started: $(date)"
docker compose up -d postgres
alembic upgrade head
echo "RTO end: $(date)"

# 5. Verify ledger chain
curl http://localhost:8000/api/owner/ledger/verify?company_id=<id>
```

### Drill results documented in `RUNBOOK.md`

If the drill exceeds RTO/RPO, an incident review creates action items
and updates this document.

## Tenant isolation breach (cloud)

If a tenant's RLS is suspected of leaking to another tenant:

1. Pause the affected tenant's user sessions (revoke refresh tokens)
2. Enable emergency read-only mode for ALL tenants (feature flag `emergency.read_only`)
3. Investigate via `app_owner_audit` log + ledger chain
4. If confirmed breach: spin up a clean dedicated DB for the affected tenant
   via `migrate-tenant-to-elite.sh`
5. Migrate from pooled to dedicated schema before resuming normal service
6. Postmortem with affected tenant + write a new ADR if the threat model changed

## Vault key compromise (cloud)

If a Vault key is leaked:

1. Rotate the affected tenant's key in Vault — every encryption operation
   derives from `(vault_url, vault_token, company_id, file_id)`, so rotating
   `vault_token` invalidates all derived keys at once
2. Re-encrypt all encrypted blobs for the tenant with the new key
   (background job: `reencrypt_tenant.py <tenant_id>`)
3. Force re-issue of all access tokens for the tenant
4. Audit the key-rotation event via `inventory_appowner_audit`

## Failed upgrade / rollback

The `update.sh` and Helm upgrade path both:

1. Take a backup first (always)
2. Run migrations (each migration is reversible via `alembic downgrade`)
3. Run health checks — if any fails, **automatic rollback** triggers

Manual rollback:
```bash
# On-prem
./scripts/update.sh --rollback

# Cloud
helm rollback auditcore --revision=<previous>
```

## Ransomware scenario

If ransomware encrypts the Smart Box:

1. The OS-level RAID + offsite backup copy survives
2. Boot from a clean USB recovery image
3. Wipe the infected disk
4. Restore from the latest backup (the encrypted-at-rest backup bundle
   is unreadable without the company's master key, which is stored
   separately on the Vault replica / offline)
5. Re-issue credentials; audit for any changes during the breach window

## Communications

### Customer-facing status page

`/status` (planned Phase 6) — public page showing:
- System status (operational / degraded / down)
- Recent incidents (last 90 days)
- Scheduled maintenance windows

### Internal incident channels

- WhatsApp to App Owner on critical events
- Email to on-call rotation
- In-app banner for known ongoing incidents

## Appendix — Storage math

Per 10,000 documents per month:
- ~5 GB/month raw blobs (AES-256-GCM encrypted at rest)
- ~200 MB/month ledger entries
- ~50 MB/month audit certs
- Backup compression ratio: ~3.5x
- Daily backup size: ~500 MB compressed

For a tenant doing 100K documents/month, plan for ~50 GB/month backups.

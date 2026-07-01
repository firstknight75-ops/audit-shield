# SECURITY.md

## Deployment-mode-aware key management

### On-premise

- `DEPLOYMENT_MODE=onpremise`
- file encryption keys are derived from:
  - company master key
  - file UUID
- raw per-file key is not stored in the database
- intended for Smart Box isolation

### Cloud

- `DEPLOYMENT_MODE=cloud`
- key backend selected through Vault-oriented factory path
- tenant secrets should be provisioned in Vault at deploy time
- no external AI/LLM API calls are allowed in either mode

## Ledger trust

- exports include tamper-proof certificate metadata
- certificate includes:
  - `ledger_hash_at_generation`
  - HMAC signature

## App Owner boundary

- App Owner inventory data must remain separate from tenant financial schemas
- no financial/analytics joins into tenant schemas are allowed for App Owner inventory operations

## Export security

- every export includes ledger hash at generation
- every export includes HMAC signature
- exports are intended to be verifiable against ledger state

## App Owner isolation promise

- App Owner operations use inventory-only tables/models
- no tenant financial schema join is required for client listing, tiering, maintenance, or templates

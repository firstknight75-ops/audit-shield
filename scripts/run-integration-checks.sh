#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Run in a Docker-enabled environment:" 
echo "1) docker compose up -d postgres redis backend celery-worker celery-beat" 
echo "2) docker compose exec -T backend pytest -q backend/app/tests/test_phase2.py backend/app/tests/test_integration_api.py" 
echo "3) Use the backend container to run migration/seed and manual RLS+ledger verification checks." 

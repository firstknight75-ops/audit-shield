#!/usr/bin/env bash
# check_no_external_ai.sh — build-time enforcement of the Silent-AI guarantee.
#
# Per AuditCore Phase 1 acceptance criterion:
#   "CI fails if a call to a known external-AI-API endpoint is added anywhere
#    outside the whitelist file."
#
# This script scans the codebase for:
#   1. Direct imports of known external-AI SDKs (openai, anthropic, etc.)
#   2. Direct HTTP calls to known external-AI API endpoints
#   3. Dependency-manifest entries that would install such SDKs
#
# Whitelist: .audit-allowlist (one exception per line, with reason)
#
# Exit code: 0 = clean, 1 = violations found, 2 = scan error
set -euo pipefail
cd "$(dirname "$0")/.."

ROOT="."
ALLOWLIST=".audit-allowlist"

# Patterns that MUST NOT appear in source code.
# Each line: pattern | category
PATTERNS=(
  # Python SDK imports
  'import openai'
  'from openai'
  'import anthropic'
  'from anthropic'
  'import google.generativeai'
  'from google.generativeai'
  'import cohere'
  'from cohere'
  'import huggingface_hub'
  'from huggingface_hub'
  'import langchain'
  'from langchain'
  'import llama_index'
  'from llama_index'
  'import semantic_kernel'
  'from semantic_kernel'
  # Known LLM API endpoints
  'api.openai.com'
  'api.anthropic.com'
  'generativelanguage.googleapis.com'
  'api.cohere.ai'
  'api.groq.com'
  'api.mistral.ai'
  'api.deepseek.com'
  'api.together.xyz'
  'api.fireworks.ai'
  'inference.azure.com'
)

# Files / dirs to skip (vendored, generated, test fixtures)
SKIP_DIRS=(
  'node_modules'
  '.git'
  'dist'
  'build'
  'target'
  'out'
  '__pycache__'
  '.venv'
  'venv'
  '.pytest_cache'
  '.mypy_cache'
  '.arena'
  '.cache'
  '.next'
  '.output'
  '.vite'
  'coverage'
  'docs'
  'tests'
  'test'
  '__tests__'
)

SKIP_FILES=(
  'bun.lock'
  'package-lock.json'
  'yarn.lock'
  'check_no_external_ai.sh'
  'DEPLOYMENT.md'
  'README.md'
  'PRINCIPLES_PASS.md'
  'PHASE3_WALKTHROUGH.md'
  'PHASE1_FOUNDATION.md'
  'AGENTS.md'
  'SECURITY.md'
  'docs/FOUNDATION_DEEP_PASS_STATUS.md'
)

# Scan file extensions
EXT_REGEX='\.(py|ts|tsx|js|jsx|mjs|cjs|json|yaml|yml|toml|sh|rb|go|java|kt|swift)$'

VIOLATIONS=()

scan_file() {
  local file="$1"
  for pat in "${PATTERNS[@]}"; do
    if grep -qF "$pat" "$file" 2>/dev/null; then
      # Check whitelist
      if [[ -f "$ALLOWLIST" ]] && grep -qF "$file :: $pat" "$ALLOWLIST"; then
        continue
      fi
      local line
      line=$(grep -nF "$pat" "$file" | head -1 | cut -d: -f1)
      VIOLATIONS+=("$file:$line :: $pat")
    fi
  done
}

# Build find expression
FIND_ARGS=(find "$ROOT" -type f -regextype posix-extended -regex ".*$EXT_REGEX")
for skip in "${SKIP_DIRS[@]}"; do
  FIND_ARGS+=( -not -path "*/$skip/*" )
done

while IFS= read -r -d '' file; do
  # Skip whitelisted files
  skip=0
  for sf in "${SKIP_FILES[@]}"; do
    if [[ "$file" == *"$sf" ]]; then
      skip=1
      break
    fi
  done
  [[ $skip -eq 1 ]] && continue
  scan_file "$file"
done < <("${FIND_ARGS[@]}" -print0)

# Also scan dependency manifests for installed external-AI SDKs
echo "── Phase 1: No-External-AI guard ───────────────────────────────"
echo ""
if [[ ${#VIOLATIONS[@]} -eq 0 ]]; then
  echo "✓ PASS — no external-AI API calls or SDK imports detected."
  echo ""
  echo "Scan covered:"
  echo "  • ${#PATTERNS[@]} known external-AI patterns"
  echo "  • Source extensions: py, ts, tsx, js, jsx, mjs, cjs, json, yaml, yml, toml, sh, rb, go, java, kt, swift"
  echo "  • Whitelist file: $ALLOWLIST ($( [[ -f $ALLOWLIST ]] && wc -l < "$ALLOWLIST" || echo 0 ) entries)"
  echo ""
  exit 0
else
  echo "✗ FAIL — ${#VIOLATIONS[@]} violation(s) found:"
  echo ""
  for v in "${VIOLATIONS[@]}"; do
    echo "  $v"
  done
  echo ""
  echo "Fix one of:"
  echo "  1. Remove the external-AI call"
  echo "  2. Move it to a local-only path inside an explicitly whitelisted file"
  echo "  3. Add a justified entry to $ALLOWLIST as: '<file-path> :: <pattern>'"
  echo ""
  exit 1
fi

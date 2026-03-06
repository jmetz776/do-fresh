#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT_DIR="$ROOT/tmp"
mkdir -p "$OUT_DIR"

# Load local env for API credentials when present
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_JSON="$OUT_DIR/x_cycle_${STAMP}.json"

.venv/bin/python scripts/x_growth_assistant.py run-cycle --limit 20 --out-json "$OUT_JSON"
echo "wrote $OUT_JSON"

# X API Test Script (60-minute block)

## Goal
Validate end-to-end X mention ingest + draft pipeline safely.

## Step 1 — Sanity checks (5 min)
```bash
cd business/demandorchestrator/apps/api
.venv/bin/python - <<'PY'
import os
keys=['X_BEARER_TOKEN','X_USER_ID','X_MENTION_STATE_PATH','X_AUTO_REPLY_ENABLED']
print({k: bool(os.getenv(k,'')) if 'TOKEN' in k or k=='X_USER_ID' else os.getenv(k,'') for k in keys})
PY
```
Expected: token/user id true; auto reply false.

## Step 2 — Fetch mentions (10 min)
```bash
.venv/bin/python scripts/x_growth_assistant.py mentions --limit 20 > /tmp/do_mentions.json
```
Expected: JSON array/object with mentions; no auth error.

## Step 3 — Generate drafts (10 min)
```bash
.venv/bin/python scripts/x_growth_assistant.py draft-replies --input /tmp/do_mentions.json > /tmp/do_drafts.json
```
Expected: draft replies generated for candidate mentions.

## Step 4 — Re-run incremental fetch (10 min)
```bash
.venv/bin/python scripts/x_growth_assistant.py mentions --limit 20 > /tmp/do_mentions_second.json
```
Expected: no replay flood; state file advances.

## Step 5 — Guardrail validation (10 min)
- Ensure `X_AUTO_REPLY_ENABLED=false`.
- Confirm no outbound reply action triggered.
- Verify logs show draft-only mode.

## Step 6 — Capture evidence (15 min)
- Save command outputs and key observations.
- Log blockers/fixes in `memory/YYYY-MM-DD.md`.
- If good: mark ready for scheduler wiring.

## Pass criteria
- Auth succeeds.
- Mention fetch works twice with incremental behavior.
- Draft generation works.
- No unintended posting/replying.

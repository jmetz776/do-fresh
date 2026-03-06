# X Automation Setup (Guardrailed)

## Goal
Autonomous posting + mention monitoring, with **human approval for replies**.

## Env vars
Set in API/runtime env:

```bash
X_BEARER_TOKEN=...
X_USER_ID=...
X_MENTION_STATE_PATH=./apps/api/x_mentions_state.json
X_AUTO_REPLY_ENABLED=false
```

## Script
`apps/api/scripts/x_growth_assistant.py`

### Post tweet
```bash
cd apps/api
.venv/bin/python scripts/x_growth_assistant.py post --text "Hello from DemandOrchestrator"
```

### Fetch mentions (incremental)
```bash
cd apps/api
.venv/bin/python scripts/x_growth_assistant.py mentions --limit 20 > mentions.json
```

### Draft conservative replies from mentions payload
```bash
cd apps/api
.venv/bin/python scripts/x_growth_assistant.py draft-replies --input mentions.json
```

## Recommended operating mode (now)
- Auto-post allowed for scheduled top-level posts.
- Auto-reply disabled (`X_AUTO_REPLY_ENABLED=false`).
- Human approves mention replies before posting.

## Scheduler-ready cycle (fetch + draft queue)
`apps/api/scripts/run_x_cycle.sh`

```bash
cd business/demandorchestrator/apps/api
./scripts/run_x_cycle.sh
```

This runs:
- mention fetch (incremental)
- draft generation
- queue append (`X_REPLY_DRAFT_QUEUE_PATH`, default `./x_reply_drafts.ndjson`)
- cycle artifact output (`apps/api/tmp/x_cycle_*.json`)

## Example cron (every 15 min)
```cron
*/15 * * * * cd /Users/jaredmetz/.openclaw/workspace/business/demandorchestrator/apps/api && ./scripts/run_x_cycle.sh >> /tmp/do_x_cycle.log 2>&1
```

## Next hardening step
Add a lightweight API/ops panel to review queued drafts and approve/send selected replies.

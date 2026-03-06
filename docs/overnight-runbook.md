# Overnight Runbook (Draft-Only Safe Mode)

## What runs overnight
1. X mention fetch + draft queue append (no auto-send)
2. Queued HeyGen status refresh
3. Memory fail-safe / index refresh

## Commands
```bash
cd /Users/jaredmetz/.openclaw/workspace/business/demandorchestrator/apps/api
./scripts/run_x_cycle.sh
.venv/bin/python scripts/poll_queued_videos.py

cd /Users/jaredmetz/.openclaw/workspace
python3 scripts/memory_fail_safe.py
```

## Safety mode
- `X_AUTO_REPLY_ENABLED=false`
- No external posting without morning review

## Morning checklist
- Review X draft queue
- Review video queue completion
- Score 3 rerender clips using `quality/video-quality-scorecard.md`
- Approve only high-quality outputs

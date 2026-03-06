# DemandOrchestrator Execution Playbook (Single Source)

## Purpose
One document to run DO without context-switching across docs.

## Current priorities
1. Premium UX + seamless operator flow
2. Backend reliability/scoping hardening
3. X automation wiring (safe, draft-first)
4. Apify signal intake (token can be deferred)

## Runbook index
- Golden path demo: `docs/demo-runbook.md`
- UX gate checklist: `docs/ux-quality-checklist.md`
- UX audit baseline: `docs/ux-audit-2026-02-28.md`
- X automation setup: `docs/x-automation-setup.md`
- X wiring checklist: `docs/x-api-wiring-checklist.md`
- X 60-min test script: `docs/x-api-test-script.md`
- Apify plan: `docs/apify-integration-plan.md`

## Daily operator loop
1. Verify API/web build health.
2. Run golden-path smoke if core changed.
3. Execute active backend block task.
4. Update memory log with concrete outputs.
5. Re-run UX checklist before calling UI work done.

## Fast commands
```bash
# API golden path smoke
cd business/demandorchestrator/apps/api
.venv/bin/python scripts/demo_golden_path.py

# X cycle (mentions -> draft queue)
cd business/demandorchestrator/apps/api
./scripts/run_x_cycle.sh

# Web build
cd business/demandorchestrator/apps/web
npm run build
```

## Non-negotiables
- Workspace-scoped operations only.
- No direct publish from raw external signals.
- Replies stay human-approved unless explicitly changed.
- Failures must be visible/retryable.

## Next execution blocks
- X API automation wiring
- Scheduler + reply draft pipeline
- UX interaction states (pending/success/error)
- Apify live token hookup when ready

# DemandOrchestrator Demo Runbook (Golden Path)

## 60-second smoke check

```bash
cd business/demandorchestrator/apps/api
.venv/bin/python scripts/demo_golden_path.py
```

Expected signal:
- `publish_run.succeeded >= 1`
- `dashboard.published` increments
- `publish_jobs` increments

## Manual UI demo flow (operator narrative)

1. Open DO web app home (`apps/web`, route `/`).
2. Create source (URL or CSV payload).
3. Normalize source.
4. Generate content (channel + variant).
5. Edit one draft caption live.
6. Approve content.
7. Schedule immediate publish (or near-term time).
8. Run publish.
9. Show dashboard counts and Provider Audit Trail (`/publish/jobs` backing panel).
10. If needed, show failed queue + retry actions.

## Pre-demo checks

- API env loaded (`demandorchestrator/.env` present)
- Web build green:

```bash
cd business/demandorchestrator/apps/web
npm run build
```

- Relay mode (optional outbound posting) configured when needed (`docs/relay-setup.md`).

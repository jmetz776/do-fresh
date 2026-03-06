# DemandOrchestrator

Monorepo scaffold:
- apps/api (FastAPI)
- apps/web (Next.js placeholder)
- packages/prompts
- packages/shared

## Quickstart
1. API: `cd apps/api && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
2. Web: scaffold pending (`next` app structure seeded)

## Deploy source of truth (Render)
- Repo: `jmetz776/do-fresh`
- Branch: `main`
- API Root Directory: `apps/api`
- API Health Check: `/health`

## Dependency policy (API)
- Keep `apps/api/requirements.txt` fully pinned (`==` only)
- PostgreSQL runtime dependency is required on Render: `psycopg2-binary==2.9.9`
- CI workflow `.github/workflows/api-deps-check.yml` validates pinning + installability on push/PR

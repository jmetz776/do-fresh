# Deploy to DemandOrchestrator.ai (Fast Path)

## Target architecture
- `www.demandorchestrator.ai` -> Next.js web app (`apps/web`)
- `api.demandorchestrator.ai` -> FastAPI backend (`apps/api`)

## What is already prepared
- API container: `apps/api/Dockerfile`
- Render blueprint: `render.yaml`
- Web expects: `NEXT_PUBLIC_API_BASE=https://api.demandorchestrator.ai`

## 1) Push latest code
```bash
cd /Users/jaredmetz/.openclaw/workspace/business/demandorchestrator
git add .
git commit -m "prep production deploy for demandorchestrator.ai"
git push
```

## 2) Deploy on Render
1. Go to Render dashboard -> **New +** -> **Blueprint**
2. Connect GitHub repo and select this `demandorchestrator` project
3. Render reads `render.yaml` and creates:
   - `demandorchestrator-api`
   - `demandorchestrator-web`
4. In web service env vars, confirm:
   - `NEXT_PUBLIC_API_BASE=https://api.demandorchestrator.ai`

## 3) Attach custom domains
For API service:
- Add custom domain: `api.demandorchestrator.ai`

For Web service:
- Add custom domains:
  - `demandorchestrator.ai`
  - `www.demandorchestrator.ai`

## 4) DNS records at registrar/Cloudflare
Use values Render gives you.
Typical setup:
- `api` CNAME -> `<render-api-hostname>`
- `www` CNAME -> `<render-web-hostname>`
- apex/root `@` -> ALIAS/ANAME to web target (or provider instructions)

## 5) Smoke tests
After SSL is issued:
```bash
curl -s https://api.demandorchestrator.ai/health
curl -s https://api.demandorchestrator.ai/v1/leads/stats
open https://www.demandorchestrator.ai/waitlist
open https://www.demandorchestrator.ai/waitlist/admin
```

## 6) Launch checklist
- [ ] Waitlist form creates lead
- [ ] Metrics cards update
- [ ] Admin table loads
- [ ] CSV export downloads
- [ ] Copy emails works

## Notes
- Current API storage is SQLite local to service instance; acceptable for MVP demo, not durable at scale.
- Next hardening step: migrate leads to Postgres managed DB.

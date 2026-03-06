# DemandOrchestrator — 48 Hour Execution Plan

## Objective
Ship a working MVP foundation with real generation flow, approval loop, and lead capture.

## Success Criteria (48h)
- Backend API running locally
- Campaign + asset schema persisted
- End-to-end generation call produces campaign bundle
- Approval/reject action works per asset
- Waitlist endpoint stores leads
- Basic dashboard shows campaign + assets + statuses

---

## Hour 0-2: Project Bootstrap (Must Finish)
1. Create monorepo structure:
   - `apps/api` (FastAPI)
   - `apps/web` (Next.js)
   - `packages/prompts`
   - `packages/shared`
2. Add `.env.example` and secret handling policy.
3. Choose DB mode:
   - SQLite for day-1 speed, Postgres-ready schema.

Deliverable: runnable skeleton with health endpoint and web home page.

---

## Hour 2-8: Data + API Core
1. Implement models:
   - `workspace`, `brand_profile`, `campaign`, `asset`, `approval_event`, `lead`, `performance_event`
2. Create migrations.
3. Implement endpoints:
   - `POST /campaigns`
   - `GET /campaigns/:id`
   - `POST /assets/:id/approve`
   - `POST /assets/:id/reject`
   - `POST /leads`
4. Add campaign status state machine:
   - `draft -> generated -> reviewed -> ready`

Deliverable: API contracts stable and testable.

---

## Hour 8-16: Generation Pipeline v1
1. Add prompt templates for:
   - planner
   - writer
   - critic/editor
   - formatter
2. Build pipeline:
   - generate draft assets
   - critique pass
   - rewrite pass
   - score each asset (0-10 rubric)
3. Store output assets linked to campaign IDs.

Deliverable: one input produces asset bundle in DB.

---

## Hour 16-24: Frontend MVP
1. Build simple dashboard pages:
   - campaign list
   - campaign detail
   - asset list with scores
   - approve/reject/regenerate controls (regenerate can be stubbed)
2. Add brand profile input form.

Deliverable: manual approval loop works via UI.

---

## Hour 24-32: Waitlist + Tracking
1. Build waitlist landing page (demandorchestrator.ai target content).
2. Wire `POST /leads` capture.
3. Add UTM fields and source tracking.
4. Add basic event capture:
   - generated
   - approved
   - rejected
   - exported

Deliverable: lead capture + event telemetry functional.

---

## Hour 32-40: Quality + Guardrails
1. Enforce no auto-publish in code.
2. Add compliance pass placeholder and block low-score assets (<7.5 avg).
3. Add audit logging for approvals.
4. Add API/input validation and failure handling.

Deliverable: safe MVP with quality thresholding.

---

## Hour 40-48: Polish + Demo Readiness
1. Create 2 demo campaigns end-to-end.
2. Export campaign package format (copy/scripts/checklist).
3. Document quickstart and known gaps.
4. Set next sprint backlog (scheduling + deeper analytics).

Deliverable: usable internal demo + concrete next sprint queue.

---

## Non-Negotiables
- No auto-publish
- Human approval required
- Secrets never in prompts/logs
- Every campaign/asset has traceable IDs and statuses

## Kill Criteria (if hit, simplify immediately)
- If generation quality loop takes >6h to stabilize, ship planner+writer only and defer critic to sprint 2.
- If frontend stalls, ship API + minimal HTML admin first.

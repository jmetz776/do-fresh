# Faceless Studio v1 — Acceptance Criteria

## Definition of Done (v1)
1. User can open `/studio/faceless` from Studio navigation.
2. User can set niche, audience, goal, cadence.
3. User can select source rails (Reddit/YouTube/X/Trends/First-party).
4. User can choose a faceless template pack.
5. User can trigger one-click batch generation from the page.
6. System returns a ranked queue preview with lane outcomes:
   - `premium_render` (pass)
   - `intelligence` (rewrite/regenerate)
7. UX copy reflects product promise: source → script → gate → render.

## Milestone Status (2026-03-04)
- [x] Milestone 1: v1 scope + acceptance criteria locked.
- [x] Milestone 2: `/studio/faceless` skeleton shipped with working controls and queue preview.
- [ ] Milestone 3: wire live source ingest API to source rail selections.
- [ ] Milestone 4: wire live script generation and policy scoring (no stub queue output).
- [ ] Milestone 5: wire premium render enqueue + review queue integration.
- [ ] Milestone 6: feedback loop card with performance-driven adaptation signals.
- [x] Voice DNA scaffold: per-workspace seeded voice style parameters exposed in Faceless Studio.

## Next Engineering Tasks
- Add endpoint: `POST /faceless/batch/generate` (profile + sources + template + batch size)
- Add endpoint: `POST /faceless/batch/render-top` (top-N gate pass)
- Persist generated batch + scores to DB for replay/audit.
- Link queue cards to existing content review/publish workflow.

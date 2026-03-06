# Trend → Brand Intelligence Roadmap (Living)

_Last updated: 2026-03-06_

## Vision
Turn trend ingestion into a proprietary decision engine that outputs high-confidence, explainable, and outcome-optimized campaigns.

## Phase 1 (In progress)
- [x] Suggestion scoring v2 features (velocity/freshness/relevance/saturation/risk)
- [x] Confidence + explainability payload in suggestions API
- [x] Data model scaffolding: `signal_features`, `signal_scores`
- [x] Adaptive weight recompute endpoint: `POST /intelligence/learn/recompute-weights`
- [x] Narrative graph endpoint: `POST /intelligence/narrative/graph`
- [x] Unified Queue integration with optional suggestion-driven narrative branches
- [x] Click/lead-aware weight recompute inputs from analytics daily metrics

## Phase 2
- [ ] Performance-linked learning from analytics outcomes (click/lead weighted)
- [ ] Channel-specific recommendation profiles
- [ ] Contrarian opportunity scoring
- [ ] Queue planner auto-branch selection from narrative graph

## Phase 3
- [ ] Workspace-specific Brand DNA guardrails (voice, claims, compliance)
- [ ] Attribution-aware queue allocation by expected value
- [ ] Multi-objective optimization (engagement vs leads vs conversion)

## Success Metrics
- Suggestion acceptance rate
- Suggestion→publish conversion
- Clicks/leads per 1000 impressions
- Time-to-approved-queue

## Operating Rules
- Keep customer UX simple and non-technical.
- Keep model/provider complexity in operator/internal surfaces.
- Every score shown to user should have explainability fields.

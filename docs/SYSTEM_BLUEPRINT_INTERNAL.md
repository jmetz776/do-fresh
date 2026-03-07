# Demand Orchestrator — Internal System Blueprint

Status: Living internal blueprint
Audience: Product, Engineering, Ops
Updated: 2026-03-06

---

## 1) Mission
Build a resilient, explainable Demand Orchestration engine that converts trend signals into brand-aligned, outcome-oriented content queues while keeping customer UX simple and operator tooling powerful.

---

## 2) High-Level Architecture

### External Inputs
- Trend ingestion: Apify actors/runs
- Platform integrations: X, LinkedIn, Instagram, YouTube (publish + metrics)
- Video providers: HeyGen (+ fallback modes)

### Core Services (API)
- `routes_mvp.py`: source/content/schedule/publish core flow
- `routes_intelligence.py`: trend scoring, suggestions, feedback learning, narrative graphs
- `routes_consent.py`: voice/avatar/video render lifecycle, limits, premium background policy
- `routes_avatar_marketplace.py`: provider/listing/purchase/usage events
- `routes_analytics.py`: event ingest, rollup rebuild, summary outputs
- `routes_status.py`: provider health and maintenance state

### Web Surfaces
- `/studio`: customer-first orchestration
- `/studio/queue`: unified queue builder + scheduler controls
- `/studio/analytics`: decision-grade KPI surface
- `/help`: customer FAQ
- `/ops`: operator console (internal-only)

### Data Layer (SQLModel)
- MVP core: workspaces, sources, source_items, content_items, schedules, publish_jobs
- Intelligence: trend_suggestions, feedback_events, learning_profiles, signal_features, signal_scores
- Analytics: content_performance_events, content_daily_metrics
- Marketplace: avatar_providers, avatar_listings, avatar_purchases, avatar_usage_events
- Reliability: provider_health_statuses

---

## 3) End-to-End Mechanism Flows

### A) Trend → Brand Intelligence
1. Import source signals from Apify run
2. Parse into source items
3. Score each candidate (v2):
   - trend_velocity
   - freshness
   - brand_relevance
   - saturation_penalty
   - risk_penalty
4. Persist:
   - suggestion
   - feature row
   - score row (`v2`)
5. Return explainable recommendation payload:
   - confidence
   - whyNow / whyBrand / whyChannel / riskNote

### B) Unified Queue Build
1. User enters idea (optionally picks a trend suggestion)
2. Queue allocator applies mix + hard caps by plan
3. If suggestion selected, narrative graph is generated
4. Branches become source rows
5. Content generation produces drafts (one-per-branch in narrative mode)
6. User approves and scheduler applies cadence

### C) Publish + Analytics Loop
1. Publish run processes due schedules
2. Publish success/failure updates content + schedule state
3. Auto-emits analytics events (`publish_succeeded` / `publish_failed`)
4. Rollups aggregate into daily metrics
5. Analytics summary powers user dashboard
6. Learning recompute endpoint consumes feedback + analytics outcomes (CTR/leads)

### D) Avatar Marketplace Usage
1. Admin creates provider + listing
2. Workspace purchases listing
3. Render request with `avatarListingId` validates active purchase
4. On successful queued/succeeded render, usage event accrues payout ledger signal

---

## 4) Resilience / Failsafe Mechanisms

### Health + Status
- `/system/provider-health/check?probe=true`
- `/system/provider-health`
- DB persistence of latest provider states

### Degradation Strategy
- Maintenance flags:
  - `DO_MAINTENANCE_MODE`
  - `DO_MAINTENANCE_MESSAGE`
- Studio banner shown when degraded/maintenance
- Core text queue flow remains available when video/integration providers degrade

### Key Strategy
- Provider-level failover where supported (e.g., Apify secondary token)
- For single-token providers (e.g., HeyGen): graceful degrade + retry + deferred queue behavior

---

## 5) Plan/Tier & Cost Controls

### Video + Premium Background Controls
- Monthly video caps by plan
- Premium background included allowances by plan
- Overages enabled/disabled by policy
- Premium templates clearly labeled in UI

### Unified Queue Guardrails
- Queue cap hard limit
- Video overflow auto-converted to text slots
- Notice displayed when cap strategy applied

---

## 6) Security & Access Boundaries
- Operator console gated by allowlist emails
- Customer surface hides provider/model/ops complexity
- Admin-key protected endpoints for marketplace provisioning
- Workspace-role checks for purchase and operational actions

---

## 7) Observability & Operating KPIs

### Product KPIs
- Suggestion acceptance rate
- Suggestion → published conversion
- Clicks/leads per 1000 impressions
- Queue build time to approved state

### Reliability KPIs
- Provider uptime / degradation windows
- Publish success rate
- Queue delay distribution
- Mean time to recovery for provider incidents

---

## 8) Current Gaps / Next Mechanism Work
1. Scheduled watchdog job for provider health probes + proactive alerts
2. Contrarian opportunity scoring as first-class feature
3. Branch-to-channel optimization (format + CTA selection by channel)
4. Automated platform metrics sync (reduce manual event ingestion)
5. Marketplace payout settlement engine (beyond accrual)

---

## 9) Living-Doc Protocol
- Update this file whenever a new mechanism ships or architecture changes.
- Mirror strategic narrative updates in:
  - `docs/WHITEPAPER_DO_INTELLIGENCE.md`
  - `docs/INTELLIGENCE_ROADMAP.md`
- Append daily implementation summary in `memory/YYYY-MM-DD.md`.

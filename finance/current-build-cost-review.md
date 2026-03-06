# Current Build Cost Review (MVP)

## Fixed monthly costs (estimated)
- Render API (`starter`): **~$7/mo**
- Render Web (`starter`): **~$7/mo**
- Domain + DNS overhead: **~$1–3/mo** (annualized)

**Fixed baseline:** **~$15–17/mo** before usage-based AI costs.

## Variable costs (usage-based)
Main driver: generation model usage (text/image/video).

Working assumptions used in worksheet:
- Text generation avg cost: **$0.008/event**
- Image generation avg cost: **$0.06/event**
- Video generation avg cost: **$0.70/event**

See worksheet for scenario math:
- `finance/cost-pricing-worksheet.csv`

## Current build components that can add cost later
- Apify actor runs (when `APIFY_TOKEN` enabled)
- X API tooling (mostly ops time now; direct API cost depends on plan)
- Email provider throughput (if outbound workflows are enabled)
- Managed DB migration (Postgres) when moving off SQLite

## Immediate recommendation
1. Treat Render baseline as fixed overhead.
2. Price from variable COGS + margin target (75% draft target already in worksheet).
3. Add event-level cost logging (now wired) to replace assumptions with actual blended COGS.
4. Recompute ARPU targets weekly until pricing is finalized.

## Next finance task
Create `actuals` tab/file from live `/costs/summary` exports and compare against projected worksheet scenarios.

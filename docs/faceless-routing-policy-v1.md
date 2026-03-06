# Faceless/Cinematic Routing Policy — v1

## Objective
Maximize content quality while controlling cost.

Core rule: **cheap models for ideation and rewrites; premium models for final video render only after script passes quality gates.**

## Pipeline
1. Source ingest (Reddit, YouTube transcripts, X, Trends, first-party winners)
2. Topic clustering + angle selection (low-cost model)
3. Hook + script draft generation (low-cost model)
4. Quality gate scoring
5. If pass → premium faceless/cinematic render model
6. If fail → rewrite loop (low-cost), then re-score

## Scoring (0–1)
- `hook_score`
- `clarity_score`
- `narrative_score`
- `cta_fit_score`
- `policy_safety_score`
- `visual_beatmap_score`

Composite:
`render_readiness = 0.22*hook + 0.18*clarity + 0.2*narrative + 0.12*cta_fit + 0.13*policy_safety + 0.15*visual_beatmap`

## Routing Thresholds
- `render_readiness >= 0.72` and `policy_safety_score >= 0.9` → premium render
- `0.55 <= render_readiness < 0.72` → rewrite loop + re-score
- `< 0.55` → discard or regenerate from new angle

## Rewrite Loop Limits
- Max 2 cheap rewrites per script
- On third failure, regenerate concept from new source cluster

## Premium Render Guardrails
- Require scene beat map
- Require opening hook on-screen by second 0–2
- Require final CTA in last 15% of script duration

## Cost Controls
- Cap premium render attempts per script: 2
- Cap premium lane ratio per batch: 35%
- Prioritize premium renders for highest expected impact posts only

## Operational Metrics
- Gate pass rate
- Rewrite success rate
- Premium render success rate
- Cost per published asset
- Conversion/engagement delta vs baseline

## Fallback
If premium provider errors:
1. Retry once
2. Route to backup premium provider
3. Queue for operator review if both fail

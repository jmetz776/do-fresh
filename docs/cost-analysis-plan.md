# DO Cost Analysis Plan (Ongoing)

## Objective
Maintain a living cost model so advanced model selection remains profitable.

## Cadence
- Weekly: update worksheet assumptions + actual usage deltas.
- Monthly: lock actual COGS and compare to pricing margin targets.
- Quarterly: refresh model price cards and plan thresholds.

## Files
- Worksheet CSV: `finance/cost-pricing-worksheet.csv`
- Pro forma template: `finance/proforma-template.md`

## Required telemetry to wire next
1. Generation event log per asset:
   - workspace_id, capability, model_id, provider, usage units, estimated cost, timestamp
2. Monthly rollup:
   - cogs by workspace/plan/model
3. Alerting:
   - margin breach by plan

## Initial margin guardrails (draft)
- Minimum gross margin target: 75%
- Premium model surcharge enabled above baseline tier
- Hard cap / soft warning at 80% of monthly included usage

## Next implementation step
- Add cost-estimation middleware in generation path and persist event-level cost rows.

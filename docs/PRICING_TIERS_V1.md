# Pricing + Tiers v1 (Draft)

## Core plans (monthly)

- **Starter**
  - Queue cap: 20
  - Included video renders: 10/mo
  - Included premium backgrounds: 5/mo
- **Pro**
  - Queue cap: 60
  - Included video renders: 40/mo
  - Included premium backgrounds: 30/mo
- **Top Tier / Enterprise**
  - Queue cap: 200
  - Included video renders: 150/mo
  - Included premium backgrounds: 120/mo

## Premium background overage

- Premium background usage beyond included cap is billable add-on
- Default overage price: **$3.00 per premium background render**
- Can be disabled globally via env when needed

## Env controls (implemented)

- `DO_PREMIUM_BG_INCLUDED_STARTER` (default `5`)
- `DO_PREMIUM_BG_INCLUDED_PRO` (default `30`)
- `DO_PREMIUM_BG_INCLUDED_TOP_TIER` (default `120`)
- `DO_PREMIUM_BG_OVERAGE_PRICE_USD` (default `3.0`)
- `DO_PREMIUM_BG_OVERAGE_ENABLED` (default `true`)

## Notes

- Current catalog uses `tier: pro` and `tier: free`; `pro` is treated as `PREMIUM` in UI and validation logic.
- Billing collection and payout allocation for premium background overage is a follow-on phase; this version enforces caps/eligibility logic and publishes pricing metadata for operators.

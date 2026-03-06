# DemandOrchestrator — Pricing Table + Billing Rules (v1)

## Pricing Philosophy
Price on outcomes + controlled usage, not seats alone.

Cost anchor (current observed):
- Avg HeyGen video render cost: **~$0.13/video**
- Planning baseline: **$0.15/video**

---

## Plan Table (v1)

| Plan | Monthly Price | Included Seats | Included Video Credits | Overage | Key Features |
|---|---:|---:|---:|---:|---|
| Starter | $99 | 1 | 0 (text-only) | N/A | Draft + schedule text content, basic queue |
| Top Tier | $399 | up to 3 | 100 | $1.50/video | Synthetic presenter directory, video workflow, cadence queue |
| Corporate | $1,500 | 5 | 500 | $1.20/video | Team avatars, seats/roles, brand kits, approval flows, governance |

Notes:
- Additional corporate seats: priced separately (recommend $49–$99/seat based on support load)
- Human licensed presenter usage: add-on fee (see marketplace section)

---

## Marketplace Add-On (Real Human Presenter Likeness)

## Recommended structure
- Per-use licensing fee layered on top of video render
- Suggested range: **$0.75 to $3.00 per usage** (by model tier)
- Revenue split to model: **50/50 or 60/40 (platform/model)** after processor fees

## Model tiers (example)
- Standard model: +$0.75/use
- Premium model: +$1.50/use
- Exclusive model: +$3.00/use (or custom)

---

## Billing Rules (Must Enforce)

## 1) Credit accounting
- 1 generated video = 1 video credit
- Failed render due to platform/provider error:
  - Do not consume credit (or auto-credit back)
- Failed render due to user script/policy violation:
  - No render performed, no credit consumed

## 2) Overage billing
- When included credits are exhausted, charge overage per successful render
- Overage appears in real time in workspace usage dashboard
- Overage billed at cycle close (or immediately if pay-as-you-go mode enabled)

## 3) Threshold alerts
- Alert at 70%, 85%, and 100% of included credits
- At 100%:
  - continue with overage if enabled
  - otherwise block further renders until upgrade/top-up

## 4) Hard limits
- Workspace-level monthly spend cap (admin configurable)
- If projected render exceeds cap, block and prompt upgrade/top-up
- Risk mode for new accounts: conservative default cap

## 5) Proration / plan changes
- Upgrade mid-cycle: prorate seats + credit allocation
- Downgrade effective next cycle by default
- Keep usage history and policy logs across plan changes

## 6) Refund policy baseline (billing side)
- Subscription fees: per published policy
- Overage: generally non-refundable for successful renders
- Billing disputes resolved using audit logs (who/when/what generated)

---

## Margin Guardrails

Track per workspace:
- Revenue (subscription + overage + model add-ons)
- Cost (video + voice + LLM + infra)
- Gross margin %

## Suggested controls
- Margin warning: < 60%
- Margin risk: < 40% (restrict expensive features / push plan upgrade)
- Margin critical: < 25% (hard cap + manual review)

---

## Operational Rules for Corporate Accounts

- Seat-based access control for draft/approve/publish/video generation
- Team avatar usage permissions (who can use which avatar)
- Department/workspace budget caps
- Approval workflow required before external publish
- Exportable audit logs for compliance

---

## Policy + Compliance Dependencies

Before broad rollout, align billing with:
- Terms of Service
- Privacy Policy
- Acceptable Use Policy
- Model Participation Agreement (for human likeness marketplace)

---

## Launch Sequence Recommendation

1. Launch Starter + Top Tier with synthetic presenters only
2. Launch Corporate with governance controls
3. Launch human model marketplace as invite-only pilot
4. Scale marketplace after legal + abuse controls are validated

---

## Quick Default Config (Suggested)

- `plan.starter.video_enabled = false`
- `plan.top_tier.video_credits = 100`
- `plan.top_tier.video_overage_usd = 1.50`
- `plan.corporate.video_credits = 500`
- `plan.corporate.video_overage_usd = 1.20`
- `alerts.usage_thresholds = [0.70, 0.85, 1.00]`
- `limits.default_monthly_spend_cap_usd = 500` (adjust by plan)


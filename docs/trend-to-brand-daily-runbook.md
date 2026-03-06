# Trend → Brand Intelligence Daily Runbook (DO)

## Objective (Daily)
Ship content decisions from **live trend signals** with a repeatable quality bar.

## 20-Minute Morning Loop

1. **Signal Intake (5 min)**
   - Run Apify actor(s) for target signal sources.
   - Confirm `GET /integrations/apify/health` is configured.
   - Import run output into sources via `/integrations/apify/import/{run_id}`.

2. **Suggestion Build (3 min)**
   - For each new source, call `/intelligence/suggestions/import-from-source`.
   - Pull top suggestions with `/intelligence/suggestions?workspaceId=default&limit=20`.

3. **Quality Gate (7 min)**
   - Keep only suggestions where:
     - `finalScore >= 0.55`
     - `policyRiskScore <= 0.30`
   - Reject anything generic, stale, or unclear “why now”.

4. **Learning Feedback (3 min)**
   - For each reviewed suggestion, submit feedback:
     - `accepted` for usable
     - `rejected` for weak/noisy
     - `published` once it goes live
   - Use `/intelligence/feedback` every time to train profile weights.

5. **Execution Handoff (2 min)**
   - Push accepted items into content generation flow.
   - Keep rejected items logged (don’t silently drop).

## Non-Negotiables
- No feedback = no learning.
- No quality gate = noisy output.
- No “why now” specificity = auto reject.

## API Endpoints (Operator Set)
- `GET /integrations/apify/health`
- `POST /integrations/apify/run`
- `POST /integrations/apify/import/{run_id}`
- `POST /intelligence/suggestions/import-from-source`
- `GET /intelligence/suggestions`
- `POST /intelligence/feedback`

## First-Day Success Criteria
- At least 1 imported source from Apify
- At least 10 generated suggestions
- 100% reviewed with feedback events
- At least 3 accepted, 1 published-ready

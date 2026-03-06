# DO × Apify Integration Plan

## Why this matters
Use Apify as a high-leverage data acquisition layer so DO can ingest richer real-world signals (mentions, competitor content, trend topics, profile updates) before content generation.

Pattern to implement:
1. Agent decides what signal is needed.
2. DO triggers an Apify actor run.
3. DO normalizes actor output into source items.
4. Normalized items flow into generate → approve → schedule → publish.

## Initial use cases (phase 1)
- X/Twitter mention harvesting (brand + keyword monitoring)
- Competitor post scrape snapshots
- Trend topic discovery by niche keywords
- URL/article extraction for source enrichment

## Architecture (recommended)
- Add `apify_client.py` service in API layer.
- Add env vars in `business/demandorchestrator/.env.example`:
  - `APIFY_TOKEN`
  - `APIFY_BASE_URL` (default: `https://api.apify.com/v2`)
  - `APIFY_TIMEOUT_SECONDS`
- Add routes:
  - `POST /integrations/apify/run` (start actor)
  - `GET /integrations/apify/runs/{run_id}` (status)
  - `POST /integrations/apify/import/{run_id}` (map dataset to MVP source items)
- Add mapping module:
  - Convert arbitrary actor dataset records → canonical `MVPSourceItem` fields (`title`, `body`, `metadata_json`, `external_ref`).

## MVP implementation order
1. Wire secure Apify client + actor run/status.
2. Support one actor end-to-end (X mentions actor).
3. Import records into `/sources` pipeline and verify generation path.
4. Add retry/error/audit logs for Apify runs.
5. Add `/ops` UI card: “Fetch from Apify” with actor preset + import button.

## Guardrails
- Never publish directly from raw scrape output.
- Always require normalize + review step before approval.
- Store actor + run metadata for auditability.
- Rate-limit actor invocations per workspace.

## Success criteria
- One-click Apify fetch produces source items visible in DO queue.
- At least one generated + approved + scheduled item traced back to Apify metadata.
- Errors are recoverable from UI/API without manual DB intervention.

## Notes
This follows the “Claude Code + Apify” pattern Jared referenced: agentic decisioning + external data actors + deterministic internal workflow.

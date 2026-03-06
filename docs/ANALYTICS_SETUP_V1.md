# Analytics Setup v1

## What is implemented

- Event ingest endpoint: `POST /analytics/events`
- Rollup rebuild endpoint: `POST /analytics/rollups/rebuild`
- Summary endpoint: `GET /analytics/summary`
- Tables:
  - `content_performance_events`
  - `content_daily_metrics`
- Studio analytics page now reads summary metrics.

## Event types

Supported `eventType` values:
- `impression`
- `engagement`
- `click`
- `lead`
- `publish_succeeded`
- `publish_failed`

## Minimum ingestion contract

Each event should include:
- `workspaceId`
- `contentItemId`
- `channel`
- `eventType`
- `value`
- optional `scheduleId`, `occurredAt`, `metadata`

## Example ingest command

```bash
curl -X POST https://emandorchestrator-api-2.onrender.com/analytics/events \
  -H "Content-Type: application/json" \
  -d '{
    "workspaceId":"default",
    "contentItemId":"<content_id>",
    "channel":"x",
    "eventType":"impression",
    "value":120
  }'
```

## Rebuild rollups

```bash
curl -X POST "https://emandorchestrator-api-2.onrender.com/analytics/rollups/rebuild?workspaceId=default&days=30"
```

## Read summary

```bash
curl "https://emandorchestrator-api-2.onrender.com/analytics/summary?workspaceId=default&days=30"
```

## Next step (recommended)

Add scheduled platform sync jobs (X/LinkedIn/Instagram/YouTube) every 2-4 hours and map provider metrics into `analytics/events`.

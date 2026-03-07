# Background Automation Jobs (Trend -> Brand Intelligence)

## Always-on intelligence tick

Endpoint:
- `POST /intelligence/background/tick`

Purpose:
1) ingest trend records from Apify run/actor
2) import suggestions into intelligence table
3) recompute workspace learning weights

### Request payload
```json
{
  "workspaceId": "default",
  "actorId": "webzitto~content-crawler",
  "limit": 100,
  "actorInput": {}
}
```

- `runId` can be provided instead of `actorId` to process a specific completed run.
- If `actorId` omitted, endpoint uses `APIFY_DEFAULT_ACTOR_ID` env var.

### Recommended schedule
- Every 30 minutes for active workspaces
- Every 2-4 hours for low-activity workspaces

### Example cron-like curl
```bash
curl -X POST https://emandorchestrator-api-2.onrender.com/intelligence/background/tick \
  -H "Content-Type: application/json" \
  -d '{"workspaceId":"default","actorId":"webzitto~content-crawler","limit":100}'
```

## Follow-on automation (next)
- Add per-workspace scheduler registry and execution locks
- Add automatic queue refill trigger when approved/scheduled falls below threshold
- Add outage-aware backoff based on provider health

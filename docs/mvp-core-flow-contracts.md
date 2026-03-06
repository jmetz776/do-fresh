# DemandOrchestrator MVP Core Flow Contracts

## Proposed folder structure

```text
apps/
  api/
    app/
      api/
        routes_mvp.py        # source/content/schedule/publish/dashboard routes
      services/
        normalize.py          # source -> source_items
        generate.py           # source_item -> content variants
        publish.py            # provider publishing + retries/idempotency
    sql/
      20260227_mvp_core_flow.sql
packages/
  shared/
    src/
      mvp-types.ts
docs/
  mvp-core-flow-contracts.md
```

## Endpoint contracts (v1)

### `POST /sources`
Create ingest source.

Request:
```json
{
  "workspaceId": "uuid",
  "type": "csv",
  "rawPayload": "title,body\n..."
}
```

Response `201`:
```json
{ "id": "source_uuid", "status": "pending" }
```

---

### `POST /sources/:id/normalize`
Parse source payload into `source_items`.

Response `200`:
```json
{
  "sourceId": "uuid",
  "status": "normalized",
  "itemsCreated": 24
}
```

---

### `POST /content/generate`
Generate one or more content variants from one source item.

Request:
```json
{
  "workspaceId": "uuid",
  "sourceItemId": "uuid",
  "channels": ["x"],
  "variantCount": 3
}
```

Response `200`:
```json
{
  "contentItems": [
    { "id": "uuid", "status": "draft", "channel": "x" }
  ]
}
```

---

### `PATCH /content/:id`
Edit a content item.

Request:
```json
{
  "title": "new title",
  "hook": "new hook",
  "caption": "new caption"
}
```

Response `200`: full updated `content_item`.

---

### `POST /content/:id/approve`
Move item from `draft` to `approved`.

Response `200`:
```json
{ "id": "uuid", "status": "approved" }
```

---

### `POST /schedules`
Create schedule for an approved item.

Request:
```json
{
  "contentItemId": "uuid",
  "publishAt": "2026-02-27T14:30:00Z",
  "timezone": "America/New_York"
}
```

Response `201`:
```json
{ "id": "schedule_uuid", "status": "scheduled" }
```

---

### `POST /publish/run`
Worker trigger for due schedules.

Rules:
- Query schedules: `status='scheduled' AND publish_at <= now()`.
- Set schedule to `processing` before provider call.
- Build idempotency key: `channel:content_item_id:publish_at`.
- If `provider_post_id` exists, skip publish.
- Retry policy: 3 attempts with backoff (1m, 5m, 15m).
- Final failure leaves content/schedule visible for manual intervention.

Response `200`:
```json
{ "processed": 12, "succeeded": 10, "failed": 2 }
```

---

### `GET /dashboard?workspaceId=...`
Return operational counts.

Response `200`:
```json
{
  "draft": 14,
  "approved": 8,
  "scheduled": 6,
  "published": 41,
  "failed": 3,
  "recentPublishes": []
}
```

## Non-negotiables

1. Never publish twice for same content+time.
2. All provider calls must reuse the same idempotency key for retries.
3. Failed jobs remain in `Needs Attention` queue.
4. Happy path (source -> scheduled) must be <5 minutes.

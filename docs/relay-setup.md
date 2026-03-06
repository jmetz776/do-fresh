# Real Relay Setup (X + LinkedIn)

## 1) Configure env

Set in your API environment:

```bash
PUBLISH_PROVIDER_MODE=webhook
PUBLISH_PROVIDER_URL=http://127.0.0.1:8000/relay/publish
PUBLISH_PROVIDER_TOKEN=<same-as-RELAY_SHARED_TOKEN>
RELAY_SHARED_TOKEN=<shared-secret>

# X
X_BEARER_TOKEN=<x-api-bearer>

# LinkedIn
LINKEDIN_ACCESS_TOKEN=<linkedin-access-token>
LINKEDIN_AUTHOR_URN=urn:li:person:...   # or organization urn
```

## 2) Relay endpoint

`POST /relay/publish`

Request body:
```json
{
  "idempotency_key": "x:contentId:publishAt",
  "attempt": 1,
  "channel": "x",
  "title": "optional",
  "caption": "post body"
}
```

Success response:
```json
{
  "ok": true,
  "post_id": "...",
  "post_url": "...",
  "provider": {...}
}
```

## 3) Supported channels

- `x` / `twitter` -> X API v2 `/2/tweets`
- `linkedin` / `li` -> LinkedIn REST `/rest/posts`

## 4) Quick credential plumbing check

From `apps/api`:

```bash
.venv/bin/python scripts/relay_plumbing_check.py
```

It verifies required env vars and probes `GET /relay/health` if API is running.

## 5) Notes

- Relay rejects unknown channels with 502.
- If `RELAY_SHARED_TOKEN` is set, relay requires matching bearer auth.
- Keep `mock-social` mode for local dry runs without live credentials.

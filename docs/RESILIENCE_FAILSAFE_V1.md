# Resilience / Failsafe v1

## Implemented

1. **Provider health status API**
   - `POST /system/provider-health/check?probe=true|false`
   - `GET /system/provider-health`
   - Tracks latest status per provider in DB table `provider_health_statuses`

2. **API key failover scaffolding**
   - HeyGen supports:
     - `HEYGEN_API_KEY` (primary)
     - `HEYGEN_API_KEY_SECONDARY` (fallback)
   - Apify supports:
     - `APIFY_TOKEN` (primary)
     - `APIFY_TOKEN_SECONDARY` (fallback)
   - Client retries/failover on auth/rate-limit/transient server errors.

3. **User-facing degraded-mode notice**
   - Studio reads `/system/provider-health`
   - Shows service notice banner when maintenance is enabled or provider degraded.

4. **Automatic analytics on publish jobs**
   - Emits `publish_succeeded` / `publish_failed` events automatically from publish flow.

## Maintenance mode env flags

- `DO_MAINTENANCE_MODE=true|false`
- `DO_MAINTENANCE_MESSAGE="Planned updates in progress..."`

## Recommended runbook

- Before planned key rotation/outage:
  1) Set `DO_MAINTENANCE_MODE=true`
  2) Set maintenance message
  3) Deploy API
- During incident:
  1) Add/rotate secondary keys
  2) Run `POST /system/provider-health/check?probe=true`
  3) Verify fallback health in `/system/provider-health`
- After recovery:
  1) Set `DO_MAINTENANCE_MODE=false`
  2) Deploy API

## Next phase

- Scheduled watchdog task (every 5-15 min) to auto-run provider probes and send proactive alerts.
- Optional Telegram alert hook when provider transitions healthy -> degraded/down.

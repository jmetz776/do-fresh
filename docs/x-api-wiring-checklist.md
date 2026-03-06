# X API Wiring Checklist (DO)

## Objective
Implement X mention fetch + draft reply pipeline with safe defaults and fast verification.

## 1) Prereqs
- [ ] X developer app has required API access.
- [ ] Credentials available:
  - [ ] `X_BEARER_TOKEN`
  - [ ] `X_USER_ID`
- [ ] State path set: `X_MENTION_STATE_PATH`.
- [ ] Auto reply disabled by default: `X_AUTO_REPLY_ENABLED=false`.

## 2) Environment
- [ ] Add/verify values in `business/demandorchestrator/.env`.
- [ ] Confirm API loads env file at startup.
- [ ] Confirm no tokens are logged or returned in API responses.

## 3) Functional wiring
- [ ] Mention fetch endpoint/script returns latest mentions.
- [ ] Incremental state saves last-seen mention ID/time.
- [ ] Draft reply generator produces conservative drafts.
- [ ] Scheduler hook can run fetch+draft periodically.
- [ ] Manual approval gate remains required for replies.

## 4) Safety guardrails
- [ ] Ignore self-authored posts.
- [ ] Ignore duplicate mentions already processed.
- [ ] Rate limit outbound calls/replies.
- [ ] Hard block auto-reply when flag is false.
- [ ] Persist run logs for audit/replay.

## 5) Verification commands
```bash
cd business/demandorchestrator/apps/api
.venv/bin/python scripts/x_growth_assistant.py mentions --limit 20 > mentions.json
.venv/bin/python scripts/x_growth_assistant.py draft-replies --input mentions.json
```

## 6) Definition of done
- [ ] Mentions fetched incrementally with state persistence.
- [ ] Draft replies generated from fresh mentions.
- [ ] No auto replies sent when `X_AUTO_REPLY_ENABLED=false`.
- [ ] Failures are visible and recoverable.

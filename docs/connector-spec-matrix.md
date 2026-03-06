# DemandOrchestrator Connector Spec Matrix (v1)

_Last updated: 2026-02-28_

## Priority roadmap
1. X
2. LinkedIn
3. YouTube (Shorts + long-form)
4. Meta (Facebook Pages + Instagram Reels)
5. TikTok
6. Threads / Pinterest / Reddit (guarded)

## Viability decisions (2026-02-28)

### Launch-critical (GO)
- **X:** GO (already in active build track; mention + draft-reply pipeline exists)
- **LinkedIn company/page posting:** GO (high B2B relevance, manageable risk)

### Phase-2 (GO after launch)
- **YouTube (Shorts + long-form):** GO post-launch once video rendering pipeline stabilizes
- **Facebook Pages + Instagram Reels:** GO post-launch with async processing checks and token hardening

### Guarded / limited rollout
- **TikTok:** CONDITIONAL GO (access/policy variability; do pilot account first)
- **Threads / Pinterest:** CONDITIONAL GO (only for proven customer segments)
- **Reddit:** NO full automation at launch (manual/semi-manual only due to moderation and policy risk)

---

## Connector table

| Platform | MVP Priority | Viability | Auth Method | Post Types | Scheduling | Media Support | Error Handling | Policy Risk | Notes |
|---|---:|---|---|---|---|---|---|---|---|
| X | P1 | High | OAuth2 + bearer/user token | Text, image, video thread variants | Native app schedule + DO scheduler | Text, image, video | Rate-limit backoff, idempotency keys, retry queue | Medium | Fastest loop for distribution + engagement |
| LinkedIn (Company/Page) | P1 | High | OAuth2 (org/user scopes) | Post, doc/image posts, short video | DO scheduler | Text, image, video | Provider response audit + retry | Medium | Strong B2B lead quality |
| YouTube Shorts | P1 | Medium-High | Google OAuth2 | Shorts upload w/ title/desc/tags | DO scheduler | Video + thumbnail | Upload status polling + fail queue | Medium | Same upload rail as long-form with shorts constraints |
| YouTube Long-form | P1 | Medium-High | Google OAuth2 | Long video + metadata | DO scheduler | Video + thumbnail | Upload/transcode status handling | Medium | Reuse YouTube connector primitives |
| Facebook Pages | P2 | Medium | Meta OAuth2 + page tokens | Text, image, video page posts | DO scheduler | Text, image, video | Token refresh + retry | Medium-High | Account/app review friction |
| Instagram Reels | P2 | Medium | Meta OAuth2 + IG business linkage | Reel publish flow | DO scheduler (with async processing checks) | Video + caption | Async publish-state checks | Medium-High | More constraints than FB Pages |
| TikTok | P2 | Medium/Variable | TikTok app auth | Video posts | DO scheduler | Video + caption | Processing status handling | High | Access and policy constraints vary |
| Threads | P3 | Medium-Low | Meta ecosystem auth | Text/image posts | DO scheduler | Text/image | Basic retry + audit | Medium-High | API maturity still evolving |
| Pinterest | P3 | Variable | OAuth2 | Pins, idea pins (where available) | DO scheduler | Image/video | Retry + media validation | Medium | Great only for specific niches |
| Reddit | P3 | Low (full-auto) | OAuth2 | Text/link posts, comments | Semi-manual preferred | Text + link/media by subreddit | Strict moderation-safe queue | High | Strong community policy sensitivity |

---

## MVP connector requirements (all platforms)

- Unified connector interface:
  - `validate(payload)`
  - `publish(payload, idempotencyKey)`
  - `status(providerId)`
  - `normalizeError(error)`
- Idempotency key format: `channel:content_item_id:publish_at`
- Retry policy baseline: `1m, 5m, 15m` then fail to **Needs Attention**
- Provider audit trail required:
  - request timestamp
  - provider response body/status
  - provider post id/url (if success)
- Human override controls:
  - retry-one
  - retry-all
  - cancel schedule

## Guardrails

- Start with human-in-the-loop for replies and high-risk actions
- Respect platform posting policies and anti-spam limits
- Default to conservative posting cadence for new accounts
- Always support manual fallback publish

## Next build tickets

1. X connector hardening (reply draft pipeline + mention monitor)
2. LinkedIn production connector (company-page first)
3. YouTube upload connector (Shorts + long-form)
4. Token vault/rotation strategy
5. Per-connector health dashboard

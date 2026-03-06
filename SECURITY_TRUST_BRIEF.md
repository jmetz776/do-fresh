# DemandOrchestrator — Security & Trust Brief

> **Living document:** update continuously as controls evolve.

## 1) Security Philosophy
DemandOrchestrator is built on a simple principle: **fail closed on sensitive actions**.

We prioritize:
- explicit identity
- explicit authorization
- least privilege
- auditable decision paths

---

## 2) Identity & Authentication
- Token-based API authentication (Bearer token required).
- No anonymous/default actor fallback.
- Passwords stored as PBKDF2-SHA256 hashes.
- Session lifecycle implemented:
  - login/register issue token
  - refresh rotates token
  - logout clears session cookies

## 3) Session Security (Web)
HttpOnly cookie-backed session data:
- `do_user_id`
- `do_user_email`
- `do_workspace_id`
- `do_api_token`

Security controls:
- secure cookies in production
- SameSite=Lax
- middleware route gating for protected studio surfaces

## 4) Authorization Model
- Workspace membership enforcement
- Role hierarchy enforcement (viewer → owner)
- Corporate domain policy checks for corporate workspaces
- Per-platform publish authorization matrix
- Publish attempts blocked if actor lacks explicit authorization

## 5) Entitlements Enforcement
Account types:
- Personal
- Corporate (premium governance)

Feature gating in backend enforces enterprise controls (not just UI labels), including:
- approval workflow
- publish authorization matrix
- full audit log views
- organization-level integration controls

## 6) API & Web Protections
- CORS allowlist (explicit origins)
- Login rate limiting on auth path
- CSRF same-origin checks on session-mutating web routes
- Security headers in middleware:
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy restrictions

## 7) Auditability
- Publish job events persisted with status/attempt metadata.
- Failure states and provider responses logged.
- Corporate-tier flows expose richer audit visibility.

## 8) Current Risk Posture (Honest View)
Strong progress has been made, but this is an actively evolving security program.

### Implemented now
- tokenized auth
- entitlement-gated enterprise controls
- session hardening baseline

### Next hardening priorities
1. Distributed rate limiting (Redis-backed)
2. Token revocation/versioning strategy
3. Secret rotation policy and key lifecycle
4. WAF/edge protections + anomaly alerting
5. External security assessment / penetration testing

## 9) Data Governance Direction
In progress toward enterprise-readiness:
- stronger retention/deletion policies
- expanded operational logging standards
- formal incident response and disclosure process

## 10) Enterprise Trust Statement
DemandOrchestrator is designed for organizations that need **high-velocity publishing without governance blind spots**.

Security is treated as a core product capability and is being continuously strengthened as part of the platform roadmap.

---

## 11) Related Documentation
- `business/demandorchestrator/FULL_BLUEPRINT.md`
- `business/demandorchestrator/PARTNER_BRIEF.md`
- `business/demandorchestrator/PARTNER_DECK_SLIDES.md`
- `business/demandorchestrator/DO_AUTH_ARCHITECTURE.md`

# DemandOrchestrator — Full Blueprint

> **Living document:** this blueprint is intentionally fluid and must be updated continuously as architecture, product scope, security posture, and go-to-market decisions evolve.

_Last updated: 2026-03-02 (10:22 ET)_

## Update Log (Rolling)
- Added token lifecycle hardening: refresh/logout routes + studio logout UX.
- Replaced header-based identity path with bearer-token session enforcement.
- Added entitlement enforcement for enterprise-only governance endpoints.
- Added security hardening baseline: CORS allowlist, CSRF same-origin checks, secure prod cookies, security headers, auth login rate limiting.
- Added Redis-ready security state service for distributed rate limiting + token revocation (jti).


## 1) Executive Summary
DemandOrchestrator evolved from MVP social workflow tooling into an enterprise-governed platform with:
- account-type split (Personal vs Corporate)
- token-based authentication
- corporate-domain access controls
- role-based authorization
- per-platform publish authorization matrix
- entitlement-gated enterprise features
- hardened session + security baseline

This document is the canonical build record for partner diligence, acquisition diligence, or extension planning.

---

## 2) Product Direction Locked

### Core Thesis
**Speed + Governance**: ship content fast without sacrificing enterprise controls.

### Account Strategy
- **Personal (lower-cost):** lean creator flow, minimal governance overhead.
- **Corporate (premium):** organization-grade controls, auditability, and policy enforcement.

### Non-Negotiables Implemented
1. No fallback anonymous/default actor auth.
2. Corporate-domain gating for corporate workspaces.
3. Explicit per-account publish authorization.
4. Entitlements enforce premium governance features.
5. Fail-closed behavior on sensitive operations.

---

## 3) Current System Architecture

## 3.1 Web App (Next.js)
Key routes:
- `/login`
- `/register` (personal/corporate)
- `/studio`
- `/auth/set-session` (web route)
- `/auth/refresh` (web route)
- `/auth/logout` (web route)

Session cookies used:
- `do_user_id`
- `do_user_email`
- `do_workspace_id`
- `do_api_token`

Middleware protections:
- studio route gating (`/studio/*`)
- early-access gate enforcement
- login redirect if missing session cookie set
- security headers added at edge middleware

## 3.2 API (FastAPI)
Key routers:
- `routes_auth.py`
- `routes_mvp.py`
- `routes_integrations.py`

Authentication:
- Bearer token required for actor identity (Authorization header)
- token verification via `services/session_token.py`

Authorization stack:
- workspace membership + role checks
- corporate-domain checks
- entitlements checks by feature
- publish authorization checks by platform/channel

## 3.3 Data & Models
Auth/governance models:
- `User`
- `Workspace`
- `WorkspaceMembership`
- `WorkspaceSetting`

MVP workflow models:
- `MVPSource`, `MVPSourceItem`
- `MVPContentItem`
- `MVPSchedule`
- `MVPPublishJob`
- cost and event tables

Workspace settings keys in active use:
- `account.type` (`personal` | `corporate`)
- `auth.allowed_domains` (JSON array)

---

## 4) Authentication & Session Blueprint

## 4.1 Implemented Auth Endpoints
- `POST /auth/register/personal`
- `POST /auth/register/corporate`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /auth/entitlements/{account_type}`

## 4.2 Password Handling
- PBKDF2-SHA256 hashing implemented in API.

## 4.3 Token Model
- Signed token issued on registration/login.
- API actor identity now comes from token claims.
- Web stores token in HttpOnly cookie and forwards as Bearer.

## 4.4 Session Lifecycle
- Login/register → set session cookie bundle.
- Refresh route rotates token.
- Logout route clears all session cookies.

---

## 5) Authorization & Governance Blueprint

## 5.1 Role Hierarchy
Ranked roles:
- viewer < editor < publisher < admin < owner

## 5.2 Corporate Domain Enforcement
- Corporate-domain checks enforce workspace-authorized domains before access-sensitive flows.

## 5.3 Publish Authorization Matrix
- Workspace-level mapping of authorized publishers by platform.
- Publish execution fails closed when actor lacks explicit authorization.
- Admin endpoint added to authorize publisher per platform.

## 5.4 Entitlements (Personal vs Corporate)
Feature gates:
- `basic_publish`: personal + corporate
- `rbac`: corporate
- `approval_workflow`: corporate
- `publish_authorization_matrix`: corporate
- `full_audit_log`: corporate

Current enforced areas include:
- publisher authorization management (corporate only)
- LinkedIn org controls (corporate only)
- approval workflow requirement for corporate scheduling path
- publish jobs/failed audit routes (corporate only)

---

## 6) Security Hardening Status

Implemented:
1. **Login rate limiting** on `/auth/login`.
2. **CORS allowlist** middleware (no wildcard by default).
3. **CSRF same-origin checks** on session mutation routes.
4. **Secure cookie flag in production**.
5. **Security headers** in middleware:
   - X-Frame-Options
   - X-Content-Type-Options
   - Referrer-Policy
   - Permissions-Policy

Still recommended next:
- secret rotation policy + key versioning
- distributed rate limiting backend (Redis) for multi-instance deployment
- token revocation list for forced logout / compromised token invalidation
- WAF/CDN edge protections and anomaly alerting

---

## 7) UX/Product Behavior by Account Type

## Personal
- low-friction content workflow
- can schedule from draft in simplified path
- no enterprise policy surface

## Corporate
- premium governance controls unlocked
- strict approval and authorization enforcement
- org controls (e.g., LinkedIn org selection)
- richer audit visibility

---

## 8) API/Platform Integration Posture

Connected accounts flow supports:
- X
- LinkedIn
- YouTube

LinkedIn protections include org-level guardrails and explicit org selection behavior for corporate use cases.

---

## 9) Revenue & Packaging Logic

Pricing and capability split is now structurally represented in backend entitlement logic (not just marketing text).

Recommended packaging language:
- Personal: creator/prosumer velocity tier.
- Corporate: governance/compliance/security tier (premium).

---

## 10) Partner / M&A Diligence Readiness

Artifacts now available for review:
- Auth architecture (tokenized, cookie-secured web flow)
- Entitlement framework and enforcement points
- Governance and publish authorization controls
- Security hardening baseline
- Enterprise pitch deck draft (`ENTERPRISE_PITCH_DECK.md`)

What a buyer/partner will ask next (prepare now):
1. Infra topology diagram (environments, secrets, networking)
2. Incident response + vulnerability patch SLA
3. Pen-test results / third-party security assessment
4. Data retention/deletion and privacy compliance specifics
5. SOC2 roadmap and evidence collection process

---

## 11) Environment Variables (Current + Critical)

Auth/session/security:
- `DO_SESSION_SECRET` (must be strong in production)
- `AUTH_LOGIN_RATE_LIMIT`
- `AUTH_LOGIN_WINDOW_SECONDS`
- `CORS_ORIGINS`
- `NODE_ENV`

App wiring:
- `NEXT_PUBLIC_API_BASE`

Corporate controls:
- `CORP_ALLOWED_DOMAINS` (bootstrap/fallback behavior)

Publishing safety:
- `ALLOW_LINKEDIN_PUBLISH`
- `LINKEDIN_ALLOWED_ORG_URN`

---

## 12) Source-of-Truth Files

Primary implementation files:
- `apps/api/app/api/routes_auth.py`
- `apps/api/app/services/session_token.py`
- `apps/api/app/services/authz.py`
- `apps/api/app/services/entitlements.py`
- `apps/api/app/api/routes_mvp.py`
- `apps/api/app/api/routes_integrations.py`
- `apps/api/app/main.py`
- `apps/web/app/actions.ts`
- `apps/web/app/studio/page.tsx`
- `apps/web/app/login/page.tsx`
- `apps/web/app/register/page.tsx`
- `apps/web/app/auth/set-session/route.ts`
- `apps/web/app/auth/refresh/route.ts`
- `apps/web/app/auth/logout/route.ts`
- `apps/web/middleware.ts`

Product narrative docs:
- `DO_AUTH_ARCHITECTURE.md`
- `ENTERPRISE_PITCH_DECK.md`

---

## 13) Recommended Next 7-Day Build Plan
1. Replace in-memory login limiter with Redis-backed limiter.
2. Add token revocation/version checks and forced logout support.
3. Add entitlement checks to any remaining enterprise-sensitive endpoints.
4. Add admin UI for domain allowlist + role assignment + entitlement visibility.
5. Produce security one-pager + architecture diagram for enterprise outbound.
6. Create investor/partner variant of pitch deck from this blueprint.

---

## 14) Model Routing Policy (Faceless/Cinematic Content)

### 14.1 Strategic Rule
**Optimize cost where users do not see it; optimize quality where users do.**

### 14.2 Two-Lane Architecture
- **Lane A — Intelligence (low-cost models):**
  - source ingest, trend clustering, idea expansion
  - hook generation, script drafts, CTA variants
  - rewrite loops for policy/clarity fixes
- **Lane B — Premium Render (high-quality models):**
  - faceless/cinematic video generation
  - only for scripts that pass objective gates

### 14.3 Source Priority Stack (Signal Quality)
1. First-party winners (historical top-performing posts)
2. YouTube transcripts (retention-tested language)
3. Reddit niche threads (pain-point language)
4. X lists/real-time narrative streams
5. Google Trends and news/industry feeds for timing validation

### 14.4 Routing Gates (Must Pass Before Premium Render)
- Hook clarity and force in first 2 seconds
- Single narrative arc with scene beat map
- Platform-fit CTA alignment
- Policy and brand-safety pass
- Score threshold met for expected performance

### 14.5 Fallback Chain
- Fail gate → cheap rewrite model pass
- Fail again → alternate low-cost model for rewrite
- Pass gate → premium render model
- Premium render failure → fallback premium provider or queue retry

### 14.6 KPI Targets
- Premium render utilization only on gate-passing scripts
- COGS reduction from two-lane routing
- Higher consistency in faceless video quality
- Improved conversion from script-to-publish output

---

## 15) Bottom Line
You now have the beginnings of an enterprise-ready social ops platform, not a toy scheduler.
The right next move is polish + evidence: harden remaining security edges, complete entitlement coverage, and package the story for buyers/partners.

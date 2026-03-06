# DemandOrchestrator — Architecture Shift (MVP → Multi-Tenant v1)

## Goal
Move from single-workspace MVP patterns to production-safe multi-tenant architecture with:
- user auth
- workspace roles
- platform authorization controls
- immutable audit trails
- safer publish governance

---

## Phase 1 (Immediate): Identity + Workspace Core

## Data model additions
- `users` (id, email, email_verified, password_hash/oidc_subject, created_at)
- `workspaces` (id, name, plan_tier, owner_user_id, created_at)
- `workspace_memberships` (user_id, workspace_id, role, status)
- `workspace_settings` (workspace_id, json)

## Roles (minimum)
- `owner`
- `admin`
- `editor`
- `publisher`
- `viewer`

## Enforcement
- Every API route requires `workspace_id` + authenticated user
- Action authorization middleware:
  - draft/rewrite: editor+
  - approve/schedule/publish: publisher+
  - account connections/policies/billing: admin+

---

## Phase 2: Platform Connections + Target Controls

## Data model additions
- `platform_connections` (workspace_id, platform, account_id, scopes, token_ref, refresh_ref, connected_at, status)
- `publish_targets` (workspace_id, platform, target_type: personal|organization, target_id, target_name, is_default, allowed)

## Policy controls
- `workspace_policies`:
  - linkedin_target_mode: personal_only | org_only | both
  - require_approval_before_publish: bool
  - allowed_platforms
  - content_risk_level

## Rules
- OAuth connection does not auto-enable publishing
- Publishing requires target selection + allowed policy match
- Corporate default: `org_only`

---

## Phase 3: Audit + Compliance Layer

## Immutable logs
- `audit_events` (id, workspace_id, user_id, action, entity_type, entity_id, metadata_json, created_at)
- `publish_events` (id, workspace_id, user_id, content_id, platform, target_id, status, provider_response, created_at)
- `policy_decisions` (allow/deny + reason)

## Required coverage
- account connect/disconnect
- policy changes
- publish attempts/results
- role changes
- content approvals

---

## Phase 4: Auth Productization

## Auth methods
- Email/password (starter)
- Google OAuth / Microsoft OAuth (recommended)
- SSO (corporate, later)

## Verification
- Individual: verified email
- Corporate: company-domain verification required (or admin-approved exception)

---

## Phase 5: Billing + Entitlements

## Entitlement checks
- plan_tier gates (Starter/Top Tier/Corporate)
- feature flags by workspace
- usage limits (video credits, seats, posting volume)

## Guardrails
- hard spend caps
- usage threshold alerts (70/85/100)
- auto-restrict over limit unless top-up enabled

---

## Migration Strategy (No Big-Bang)

1) Keep MVP endpoints, add auth/workspace wrappers.
2) Backfill existing data into `default workspace` owned by Jared.
3) Introduce role checks route-by-route.
4) Turn on strict enforcement once all critical routes are wrapped.

---

## Immediate Next Build Tasks

1. Add auth session middleware + user model
2. Add workspace membership role checks
3. Add publish target model (personal/org) and selection UI
4. Move LinkedIn org-only lock from env to workspace policy
5. Write audit events on publish + policy changes

---

## Non-Negotiables
- No publish without role + platform permission + target policy pass
- No silent account-level posting defaults
- All sensitive actions logged with user + workspace attribution

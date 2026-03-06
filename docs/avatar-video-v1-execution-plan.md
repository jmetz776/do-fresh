# Avatar Video v1 — Execution Plan

## Goal
Ship a truly simple user flow for avatar videos with scene templates while keeping reliability high.

## P0 (Ship now)

### 1) One-click voice bootstrap in Avatar Video page
**User story:** If no approved voice render exists, user can click one button to create one from sample script.

**Build:**
- Add `Create sample voice render` button on `/studio/avatar-video` when no approved voice exists.
- Backend action:
  - pick first active voice profile
  - create voice render with short default script
  - auto-approve if render succeeds

**Acceptance criteria:**
- User without approved voice can still get to video creation in <=2 clicks.
- Clear success/error banner shown.

---

### 2) Auto-template recommendations in wizard
**User story:** User sees top recommended scene templates based on script.

**Build:**
- On submit draft/script input, call `/video/background-recommendations`.
- Show top 3 as pills + still allow full dropdown.

**Acceptance criteria:**
- Recommendations appear in <1s for normal script length.
- Selected recommended template is persisted and used in job creation.

---

### 3) Unified status card for created render
**User story:** After creating a video job, user can clearly see current state and next action.

**Build:**
- Add status panel on `/studio/avatar-video` for latest render id.
- States: `queued`, `processing`, `delayed`, `succeeded`, `failed`.
- Button actions:
  - queued/processing → refresh
  - failed → retry
  - succeeded → open in Review Theater

**Acceptance criteria:**
- No silent actions.
- Every state has user-readable explanation.

---

## P1 (Hardening)

### 4) Persistent data guard in production
**Build:**
- Enable `DO_REQUIRE_PERSISTENT_DB=true` in production.
- Confirm `DATABASE_URL` points to Render Postgres.

**Acceptance criteria:**
- Voice profiles persist across deploys/restarts.

---

### 5) Scene asset readiness checks
**Build:**
- Preflight template URL reachability (HEAD/GET test) during ingest/approve.
- Mark template unusable if unreachable.

**Acceptance criteria:**
- No `HTTP_DOWNLOAD_FAILED` during normal use for approved templates.

---

### 6) Provider reliability UX
**Build:**
- Show provider delay message if queued beyond SLA.
- Keep timeout + inflight cap behavior visible in UI.

**Acceptance criteria:**
- User gets explicit reason when provider stalls.

---

## P2 (Product quality)

### 7) Scene compositing architecture
**Build:**
- Avatar foreground + scene background compositing for deterministic placement.
- Add shadow/color-match controls per template.

**Acceptance criteria:**
- Avatar appears grounded in scene consistently.
- Result is visibly different across scene templates.

---

## Rollout order
1. P0.1 voice bootstrap
2. P0.3 unified status card
3. P0.2 recommendations in wizard
4. P1.4 persistent DB enforcement
5. P1.5 template URL preflight
6. P1.6 provider delay UX
7. P2.7 compositing engine

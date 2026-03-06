# DemandOrchestrator — Implementation Plan (v1)

## Product Thesis
Build an autonomous **demand orchestration platform** that turns one input (idea/transcript/link) into a complete campaign pipeline:

**Input → Content Assets → Distribution Queue → Lead Capture → Performance Feedback**

The platform is not “content spam automation.” It is a **conversion-oriented operating system** for solo operators and small teams.

---

## North Star Outcomes
1. Generate a full campaign pack in under 10 minutes.
2. Reduce manual content operations by >70%.
3. Increase weekly outbound content consistency.
4. Tie generated assets to measurable lead/revenue outcomes.

---

## Target User (Initial ICP)
- Solo founders / micro-agencies / lean SaaS teams
- Need consistent demand generation
- Limited time, no media team, no full growth stack

---

## MVP Scope (Phase 1)
### 1) Input & Context Layer
- Accept topic, transcript, URL, or notes
- Brand profile:
  - voice/tone
  - offer positioning
  - CTA preferences
- Campaign objective selector:
  - awareness / lead-gen / conversion

### 2) Campaign Generation Engine
Generate from one input:
- 10-20 hooks
- 3 short-form scripts
- 3 social posts (channel-optimized)
- 1 email draft
- 1 lead magnet outline
- 1 landing section block (headline, copy, CTA)

### 3) Approval & Editing Layer
- Asset queue
- Regenerate by component (hook/script/copy)
- Approve/reject workflow
- Save winning variants

### 4) Distribution Layer (MVP-lite)
- Export package (copy + scripts)
- Manual publishing checklist
- Scheduling stub (internal queue objects)

### 5) Lead Capture Layer
- Waitlist endpoint
- Basic CRM table (email/source/status)
- UTM-friendly CTA templates

### 6) Analytics Layer v1
- Track generated assets + campaign IDs
- Track published status + manual outcomes
- Score winners by simple metrics (CTR/replies/signups)

---

## LLM Architecture (Critical Quality Layer)
Content quality is make-or-break. Use a **model ensemble by task**, not one model for everything.

### Model Roles
1. **Planner Model (Reasoning-heavy)**
   - Purpose: campaign strategy, audience framing, angle selection
   - Output: structured campaign blueprint

2. **Writer Model (High style/control)**
   - Purpose: hooks, scripts, posts, email copy
   - Output: multiple quality variants

3. **Editor/Critic Model (Strict QA)**
   - Purpose: tighten clarity, persuasion, novelty, compliance
   - Output: revised draft + rationale + scorecard

4. **Channel Formatter Model (Constraint-focused)**
   - Purpose: adapt to platform limits + formatting norms
   - Output: publish-ready channel variants

### Quality Pipeline (Required)
Every asset runs through:
1. Draft generation
2. Critique pass (clarity, originality, CTA strength)
3. Rewrite pass
4. Compliance/claims pass
5. Final scoring

### Scoring Rubric (0-10 each)
- Novelty
- Specificity
- Emotional pull
- CTA clarity
- Offer alignment
- Channel fit

Reject and regenerate assets below threshold (e.g. avg < 7.5).

---

## Tech Stack
- Backend: FastAPI
- DB: Postgres (SQLite allowed for local bootstrap)
- Queue: lightweight jobs/cron initially
- Frontend: Next.js minimal dashboard
- Storage: local/S3-compatible for media outputs
- Auth: simple email magic link (later)

---

## Data Model (Core Entities)
- `workspace`
- `brand_profile`
- `campaign`
- `asset` (type, channel, status, score)
- `approval_event`
- `publish_job`
- `lead`
- `performance_event`

---

## Delivery Roadmap
## Sprint 1 (Days 1-3)
- Backend skeleton
- Campaign + asset schema
- Generation endpoint
- Prompt templates v1

## Sprint 2 (Days 4-6)
- Approval dashboard
- Regenerate/edit actions
- Export package

## Sprint 3 (Days 7-9)
- Waitlist capture
- Analytics events + scorecard
- Basic campaign history view

## Sprint 4 (Days 10-14)
- Polish + onboarding
- 3 demo campaigns/case studies
- Beta launch page + intake flow

---

## Guardrails (Non-Negotiable)
- Never auto-publish unapproved content in v1
- Claims/compliance check before finalization
- No secrets in prompts/logs
- Human override always available

---

## KPIs (First 30 Days)
- Time-to-first-campaign
- Assets generated per campaign
- Approval rate
- Publish rate
- Lead conversion per campaign
- % winning assets reused next cycle

---

## Immediate Next Actions
1. Scaffold backend + schema
2. Build prompt pack (planner/writer/editor)
3. Build minimal dashboard for approvals
4. Launch waitlist landing page on demandorchestrator.ai

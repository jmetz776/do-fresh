# Email Connectors + Repurpose Delivery v1

Date: 2026-03-07
Status: Draft
Owner: Growth + Platform

## Objective
Enable users to send repurposed email content from their own preferred sender addresses, to permission-based audiences, with deliverability and compliance guardrails.

---

## 1) Sender Connection Model (Outbound)

### v1 providers
- Google Workspace / Gmail (OAuth)
- Microsoft 365 / Outlook (OAuth)

### Flow
1. User clicks **Connect Email Sender** in Studio/Settings.
2. OAuth consent grants scoped send permission.
3. DO stores encrypted token + sender metadata.
4. User selects default From identity (and alias where supported).
5. Test send verifies setup.

### Data model (proposed)
- `email_sender_connections`
  - id
  - workspace_id
  - provider
  - sender_email
  - sender_name
  - status (active/expired/error)
  - scopes_json
  - token_ref (encrypted/secret-managed)
  - last_tested_at

---

## 2) Audience Source Model (Inbound)

### v1 audience sources
- CSV import
- HubSpot sync

### v1.1+
- Salesforce/Pipedrive sync
- Other CRM connectors

### Data model (proposed)
- `audience_lists`
  - id, workspace_id, name, source_type
- `audience_contacts`
  - id, list_id, email, first_name, last_name, tags_json, consent_status
- `suppression_list`
  - workspace_id, email, reason, created_at

---

## 3) Compliance + Deliverability Guardrails (Required)
- Opt-in/permission-only sends.
- Unsubscribe link + physical address footer support.
- Suppression list enforcement before every send.
- Bounce/complaint suppression handling.
- Sender domain alignment guidance (SPF/DKIM/DMARC).
- Warmup/rate controls for new sender identities.

---

## 4) Repurpose Engine Email Mode

### Formats
- `newsletter_snippet`
- `campaign_email`
- `followup_email`

### Output package (email)
- Subject line variants (2–3)
- Preview text variants (1–2)
- Body (plain + optional HTML)
- CTA blocks
- Segment-specific personalization tokens

---

## 5) Visual Variant Pack (Image Generation)

### Why
Improve engagement and segment relevance in repurposed email campaigns.

### v1 behavior
For each email package, generate optional visual variants:
- Hero image (2 variants)
- Offer/support graphic (1–2 variants)
- Alt text suggestions

### QA checks
- Brand color/voice alignment
- Mobile-safe dimensions
- File size budget
- Contrast/readability checks

---

## 6) Studio UX (Simplicity-first)
1. Select source content.
2. Toggle **Repurpose to Email**.
3. Pick audience list.
4. Pick sender identity.
5. Choose recommended variant.
6. Preview + send/schedule.

Advanced settings remain collapsed by default.

---

## 7) API Endpoints (Proposed)

### Sender connections
- `POST /v1/email/senders/connect/{provider}`
- `GET /v1/email/senders`
- `POST /v1/email/senders/{id}/test`
- `POST /v1/email/senders/{id}/disconnect`

### Audience
- `POST /v1/email/audiences/import-csv`
- `POST /v1/email/audiences/sync/hubspot`
- `GET /v1/email/audiences`
- `GET /v1/email/audiences/{id}/stats`

### Campaign delivery
- `POST /v1/email/repurpose/send`
- `POST /v1/email/repurpose/schedule`
- `GET /v1/email/campaigns/{id}`

---

## 8) KPI Framework
- Sender connection success rate
- Deliverability rate (delivered / sent)
- Open/click rates by segment
- Unsubscribe + complaint rates
- Revenue/lead conversion from email campaigns
- Time saved via repurpose-to-email workflow

---

## 9) Rollout Plan
### Phase A
- Gmail/Outlook sender OAuth
- CSV list import
- Repurpose -> newsletter snippet send

### Phase B
- HubSpot sync
- Scheduled sends + simple A/B subject tests
- Visual variant pack for email creatives

### Phase C
- Expanded CRM integrations
- Advanced segmentation and lifecycle automation

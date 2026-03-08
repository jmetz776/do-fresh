# Repurpose Engine Contract v1

Date: 2026-03-07
Status: Draft
Owner: Content Engine

## Purpose
Transform one source asset (idea, text post, script, image, or video transcript) into a structured multi-channel package with channel-native variants and quality scores.

---

## 1) Input Contract

```json
{
  "workspaceId": "default",
  "source": {
    "type": "idea|text|script|image|video_transcript",
    "title": "US Youth Soccer age group changes",
    "body": "...",
    "transcript": "...",
    "assetUrls": ["https://..."],
    "language": "en",
    "brandContextId": "optional-brand-profile-id"
  },
  "intent": {
    "goal": "lead_gen|awareness|education|conversion|community",
    "audience": "parents of youth athletes",
    "offer": "club tryout consult",
    "cta": "Book a consult"
  },
  "targets": [
    { "channel": "x", "formats": ["text_post"] },
    { "channel": "linkedin", "formats": ["text_post", "carousel"] },
    { "channel": "instagram", "formats": ["caption", "carousel"] },
    { "channel": "youtube_shorts", "formats": ["short_script"] },
    { "channel": "email", "formats": ["newsletter_snippet"] }
  ],
  "constraints": {
    "tone": "authoritative but approachable",
    "doNotSay": ["guaranteed results"],
    "compliance": ["no medical/legal claims"],
    "maxVariantsPerTarget": 2
  }
}
```

---

## 2) Output Contract

```json
{
  "repurposeJobId": "uuid",
  "status": "succeeded|partial|failed",
  "summary": {
    "sourceType": "script",
    "targetsRequested": 5,
    "targetsCompleted": 5,
    "totalVariants": 8
  },
  "outputs": [
    {
      "channel": "x",
      "format": "text_post",
      "variants": [
        {
          "id": "uuid",
          "title": "Hook-first variant",
          "body": "...",
          "hashtags": ["#YouthSoccer", "#Tryouts"],
          "cta": "Book a consult",
          "quality": {
            "overall": 0.86,
            "brandFit": 0.89,
            "clarity": 0.84,
            "originality": 0.81,
            "compliance": 0.98
          },
          "flags": [],
          "metadata": {
            "readingTimeSec": 20,
            "estimatedEngagementBand": "medium-high"
          }
        }
      ]
    },
    {
      "channel": "linkedin",
      "format": "carousel",
      "variants": [
        {
          "id": "uuid",
          "slidePlan": [
            { "slide": 1, "headline": "What changed", "body": "..." },
            { "slide": 2, "headline": "Why it matters", "body": "..." }
          ],
          "caption": "...",
          "cta": "Book a consult",
          "quality": {
            "overall": 0.83,
            "brandFit": 0.88,
            "clarity": 0.86,
            "originality": 0.76,
            "compliance": 0.97
          },
          "flags": ["low_originality_warning"],
          "metadata": {
            "slideCount": 6
          }
        }
      ]
    }
  ],
  "qualityGate": {
    "passed": true,
    "threshold": 0.78,
    "failedItems": []
  },
  "errors": []
}
```

---

## 3) Supported Formats (v1)
- `text_post` (X, LinkedIn)
- `caption` (Instagram)
- `carousel` (LinkedIn, Instagram)
- `short_script` (TikTok/YouTube Shorts)
- `newsletter_snippet` (Email)

---

## 4) Quality Gate Rules (v1)
Each variant gets 0–1 scores for:
- Brand fit
- Clarity
- Originality
- Compliance

Default pass threshold: `overall >= 0.78` and `compliance >= 0.95`.

Fail behavior:
- Mark variant with `flags`
- Attempt one guided regeneration
- If still failed, return as `needs_review` (never silently auto-publish)

---

## 5) UI Flow (v1)
1. User selects source asset in Studio.
2. Clicks **Repurpose**.
3. Chooses channels + formats.
4. System generates package and displays grouped outputs by channel.
5. User can:
   - accept/reject each variant
   - rewrite/regenerate per variant
   - bulk-approve passing variants
6. Approved variants route into existing queue/review/schedule flow.

---

## 6) API Endpoints (proposed)
- `POST /v1/repurpose/jobs`
- `GET /v1/repurpose/jobs/{jobId}`
- `POST /v1/repurpose/jobs/{jobId}/regenerate-variant`
- `POST /v1/repurpose/jobs/{jobId}/approve`
- `POST /v1/repurpose/jobs/{jobId}/publish-to-queue`

---

## 7) Telemetry (must-have)
Track:
- job created/completed/failed
- per-variant quality scores
- regeneration count
- approve/reject actions
- publish outcomes per channel

KPIs:
- Time saved vs manual creation
- Approval rate per channel/format
- Regeneration rate
- Publish success rate
- Downstream engagement/conversion lift

---

## 8) Non-goals (v1)
- Fully autonomous posting without review
- Advanced multimedia rendering orchestration in same step
- Multi-language auto-localization (defer to v1.1+)

---

## 9) Next Implementation Tasks
1. Define SQL model(s): repurpose_job, repurpose_output_variant, repurpose_quality_event.
2. Add service layer for generation + scoring + fallback regeneration.
3. Build Studio repurpose panel with grouped variant review UX.
4. Connect approved outputs to unified queue and scheduling endpoints.

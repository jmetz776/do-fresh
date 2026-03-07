# Onboarding + AI Helper Premium Voice (v1)

## Scope (2026-03-07)
This release adds a premium narrated onboarding experience and an in-app AI helper with stuck detection.

## What shipped

### 1) Onboarding premium narration
- Onboarding story uses approved ElevenLabs renders when present.
- Route: `GET /api/onboarding/voiceover`
- Returns profile + `audioBySlide` URLs sourced from approved voice renders.
- Fallback: browser speech synthesis when premium audio is unavailable.

### 2) Manual readability-first story progression
- Story autoplay defaults OFF.
- User advances slides manually via prominent **Next Slide →** CTA.
- Voiceover completion hint shown to user.

### 3) AI assisted helper (onboarding + studio)
- Floating helper UI component: `app/components/AIAssistHelper.tsx`
- Voice route: `POST /api/assist/voice`
- Behavior:
  - contextual text guidance
  - on-demand premium voice playback
  - browser speech fallback

### 4) Smart stuck triggers
- Inactivity trigger (~30s idle)
- Repeated click loop trigger (same target repeatedly)
- Form invalid/required field trigger

## UX principles used
- Keep user in control (manual slide progression by default)
- Provide voice as enhancement, not blocker
- Offer text + voice for accessibility and resilience
- Nudge only when friction signals appear

## Follow-on improvements (v1.1)
- Add threshold tuning and analytics for stuck-trigger precision
- Add allowlist of sensitive forms where helper should stay passive
- Add optional one-click "Guide me through this page" walkthrough scripts
- Add static pre-generated onboarding audio assets for lower latency/cost

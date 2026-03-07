# ElevenLabs Integration Status (DO)

## Implemented now
- Consent/identity-gated voice profile creation
- ElevenLabs client service (`app/services/elevenlabs_client.py`)
- Voice render job lifecycle endpoints:
  - `POST /v1/consent/voice/renders`
  - `GET /v1/consent/voice/renders`
  - `POST /v1/consent/voice/renders/{id}/approve`
- Voice render audio retrieval endpoint:
  - `GET /v1/consent/voice/renders/{id}/audio`
- Web onboarding premium voice endpoint:
  - `GET /api/onboarding/voiceover`
- AI helper premium voice endpoint:
  - `POST /api/assist/voice`
- Audio artifact persistence to:
  - `/app/data/audio/renders/*.mp3` (runtime)

## Validation run (2026-03-07)
- Created consent record -> verified identity
- Created active ElevenLabs voice profile
- Configured active profile:
  - Display name: `Harper Premium Voice`
  - Voice ID: `QLAlOeRuLwKX0skeTR7R`
- Rendered sample voice job successfully
- Approved rendered job successfully
- Generated and approved 5 onboarding slide narration renders

## Current product behavior
- Onboarding uses premium ElevenLabs slide audio when available.
- If premium audio fails/unavailable, fallback is browser speech synthesis.
- AI helper can generate and play contextual premium guidance on demand.

## Remaining (next)
- `/ops` UI panel for voice render queue and in-browser playback
- Persist provider usage data for invoice-grade cost reconciliation
- Add voice moderation/quality checks before auto-approval in helper flow
- Optional pre-baked static onboarding audio assets to reduce per-session render latency/cost

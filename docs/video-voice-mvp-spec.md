# DO Video + Voice MVP Spec (Likeness-Aware)

## Product goal
Enable customers to generate high-quality video content with synced voice, with optional user likeness, while enforcing strict consent and abuse prevention.

## Recommended v1 stack
- Voice cloning/TTS: ElevenLabs
- Avatar/lip-sync video: HeyGen (or Tavus alternative)
- DO role: orchestration + script quality + approval + publishing + audit

## V1 user flow
1. Create script in DO (or import source -> generate script)
2. Choose voice mode:
   - Standard AI voice
   - Custom cloned voice (requires consent flow)
3. Choose visual mode:
   - No avatar (B-roll/text video)
   - Personal avatar (requires likeness consent flow)
4. Render preview
5. Human review + approve
6. Publish/schedule

## Key entities
- VoiceProfile
  - owner_user_id, provider, voice_id, consent_record_id, status
- AvatarProfile
  - owner_user_id, provider, avatar_id, consent_record_id, status
- ConsentRecord
  - subject_name, subject_email, scope, signed_at, revoked_at, evidence_uri
- VideoRenderJob
  - script_id, voice_profile_id, avatar_profile_id, status, provider_job_id, cost_estimate

## API endpoints (proposed)
- `POST /v1/voice/profiles` (create + consent attestation)
- `POST /v1/avatar/profiles` (create + consent attestation)
- `POST /v1/video/render` (submit render job)
- `GET /v1/video/renders/{id}` (status/result)
- `POST /v1/video/renders/{id}/approve`
- `POST /v1/video/renders/{id}/publish`

## Guardrails (must-have)
- No custom voice/avatar render without valid consent record
- Block celebrity/public-figure mimic attempts by policy
- Revocation support: disable profile if consent withdrawn
- Immutable audit log for consent + render actions
- Watermark/provenance metadata on generated video

## Pricing implications
- Video + voice costs are materially higher than text
- Restrict custom voice/avatar features to Pro/Growth tiers
- Enforce per-render cost checks before queueing

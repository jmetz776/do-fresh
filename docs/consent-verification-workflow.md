# Consent + Identity Verification Workflow (Step 1)

## Goal
Hard-gate custom voice/avatar usage behind explicit consent and identity verification.

## Implemented API scaffold
- `POST /v1/consent/records`
- `POST /v1/consent/records/{id}/verify-identity`
- `POST /v1/consent/records/{id}/revoke`
- `GET /v1/consent/records`
- `POST /v1/consent/voice/profiles`
- `POST /v1/consent/avatar/profiles`

## Data models added
- `ConsentRecord`
- `IdentityVerification`
- `VoiceProfile`
- `AvatarProfile`

## Enforcement logic
- Voice/avatar profile creation requires:
  1) active signed consent record
  2) latest identity verification status = `verified`

## Operational checklist before launch
- Integrate e-sign provider for release form artifact
- Integrate ID+liveness verification provider
- Add admin review queue for failed/flagged verifications
- Add revocation automation to disable related voice/avatar profiles
- Add immutable audit export endpoint

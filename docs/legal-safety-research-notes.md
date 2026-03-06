# Legal & Safety Research Notes (Synthetic Voice/Likeness)

> Not legal advice. Use counsel before launch.

## Why this matters
Allowing user-uploaded likeness/voice without controls creates major legal and trust risk.

## Platform policy signals (high-level)
- ElevenLabs policy indicates no unauthorized voice replication; user must have consent/legal right.
- HeyGen policy/trust pages indicate explicit consent is required for real-person avatars/likeness.

## Regulatory risk themes (US and broader trend)
- State-by-state synthetic media/deepfake laws are expanding.
- Non-consensual synthetic media risk is increasingly targeted by civil/criminal frameworks.
- Commercial misuse and deceptive impersonation exposure is high.

## Minimum legal/safety requirements for DO
1. Explicit consent capture for voice and likeness (signed + timestamped)
2. Identity linkage between account and consent subject
3. Scope-limited consent (where/how content may be used)
4. Revocation workflow and rapid takedown process
5. Content provenance/watermarking
6. Abuse reporting + moderation + account sanctions
7. Updated Terms/Privacy and customer warranties

## Operational controls
- Manual review for first N renders on custom profiles
- Risk scoring for suspicious prompts (impersonation intent)
- Denylist for known protected/public identities where appropriate
- Logging retained for incident response

## Open legal questions for counsel
- Which consent form language is required by target jurisdictions?
- What retention period for consent artifacts is required/recommended?
- What disclosure is needed for synthetic/AI-generated content in ads?
- Liability allocation in Terms for user-provided likeness claims?

## Launch recommendation
Do not enable public custom likeness/voice until:
- consent system + revocation are in production,
- policy enforcement is tested,
- legal review is completed.

# DO Launch Gate Checklist (Reputation-Critical)

## Must-pass technical gates
- [ ] Core pipeline stable (ingest -> generate -> approve -> schedule -> publish)
- [ ] Voice render reliability <= 2% failure
- [ ] Video render reliability <= 2% failure or clearly bounded async SLA
- [ ] Cost guardrails enforced by plan (warnings + hard caps)
- [ ] Retries + recovery path for failed voice/video jobs

## Must-pass quality gates
- [x] Text benchmark pass (>=8.5 avg, no axis <7)
- [x] Voice bakeoff winner selected and documented (ElevenLabs primary)
- [ ] Video quality pass on 3+ samples (>=8.5 avg, no metric <7) — current avg 8.44 (near-pass)
- [ ] Landing copy accurately reflects shipped capabilities only

## Must-pass legal/safety gates
- [ ] Signed consent records required for custom voice/avatar
- [ ] Identity verification required before profile activation
- [ ] Revocation flow works and disables future renders
- [ ] Minor cloning hard-block policy implemented
- [ ] Audit trail export available for incidents/compliance

## Must-pass operational gates
- [ ] Daily command brief + EOD closeout calendar workflow active
- [ ] Memory continuity process verified (daily + long-term)
- [ ] Expense tracking updated (domains/subscriptions/API credits)
- [ ] Incident response owner identified

## Launch decision
- [ ] GO
- [ ] NO-GO
- [ ] Date:
- [ ] Decision owner:

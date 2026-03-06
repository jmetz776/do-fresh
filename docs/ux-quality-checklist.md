# DO UX Quality Checklist

Use this as a release gate for every UI-facing change.

## Scoring
- 0 = broken/missing
- 1 = weak/inconsistent
- 2 = acceptable
- 3 = excellent

**Ship bar:**
- No 0s in Core Flow or Reliability
- Average >= 2.4 across all sections

---

## 1) Core Flow Clarity (must-pass)
- [ ] One obvious primary action per step (no competing CTAs)
- [ ] Steps are visually ordered and easy to scan
- [ ] Labels are plain-English (no internal jargon)
- [ ] Empty states tell user exactly what to do next
- [ ] Critical context is visible (workspace, environment, status)

## 2) Visual Quality (must-pass)
- [ ] Consistent spacing rhythm and typography scale
- [ ] Buttons/inputs use a shared visual system
- [ ] Color use communicates hierarchy/status, not decoration
- [ ] Cards/sections feel intentional, not raw scaffolding
- [ ] Mobile and desktop layouts both feel designed

## 3) Interaction Quality
- [ ] Submit actions show pending/loading feedback
- [ ] Success and error messages are explicit and actionable
- [ ] Keyboard-friendly forms (tab order, enter behavior)
- [ ] Dangerous actions are clearly marked/guarded
- [ ] Time/date inputs are local and obvious

## 4) Reliability & Trust (must-pass)
- [ ] UI workspace defaults match backend defaults
- [ ] Data shown is fresh and consistent after actions
- [ ] Retry flows exist for known failure modes
- [ ] Audit surfaces exist for critical operations
- [ ] Known edge cases fail gracefully (no silent failure)

## 5) Conversion/Business Fit
- [ ] Value proposition is immediately clear
- [ ] Waitlist/signup friction is minimal
- [ ] Admin tools support real follow-up workflow
- [ ] Metrics displayed are decision-useful
- [ ] Product tone matches premium operator brand

---

## Release Decision
- [ ] Pass (ship)
- [ ] Pass with punch-list (time-boxed)
- [ ] Fail (block release)

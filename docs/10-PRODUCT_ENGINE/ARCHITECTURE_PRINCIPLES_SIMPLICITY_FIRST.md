# Architecture Principles — Simplicity First

Date: 2026-03-07
Context: As platform surface area expands (new channels, new modes, GTM features), user simplicity remains top priority.

## Non-Negotiable Principle
**User simplicity > feature quantity.**
If a feature increases confusion, it must be redesigned, staged, or hidden behind progressive disclosure.

## Practical Design Rules
1. **One obvious next action per screen.**
2. **Default-safe behavior.** (manual review path before publish)
3. **Progressive complexity.** advanced controls appear only when needed.
4. **Consistency across modes.** queue/review/schedule should feel the same.
5. **Text + voice guidance.** helper guidance should never require audio only.
6. **Fail graceful.** when provider fails, keep user flow moving with clear fallback.

## Architecture Implications
- Shared contract patterns across content modes.
- Shared quality-gate service before publish.
- Shared helper infrastructure for stuck detection + guidance.
- Shared telemetry for friction hotspots and time-to-value.

## Release Gate Addendum
Any new mode/channel must pass:
- task completion clarity
- low-friction first-run path
- fallback behavior documented
- scorecard PASS for usability + reliability

## What this means for Repurpose Engine
- Keep v1 to five core formats.
- Bundle outputs by channel with clear approve/reject actions.
- Avoid overloading UI with too many variants at once.
- Surface best recommended variant first.

# UI Polish Punch-List (Ready to Execute)

## P0 — Do first
1. Action feedback states (`/ops`, `/waitlist/admin`)
   - Pending button states
   - Inline success/error messages
   - Recoverable error copy

2. Guardrail confirmations
   - Confirm before `Run Publisher Now`
   - Confirm before `Retry All Failed`

3. Shared UI primitives
   - Button/Input/Select/Textarea/Card/Badge tokens
   - Consistent spacing and type scale

## P1 — Next
4. `/waitlist/admin` table ergonomics
   - Pagination
   - Search by email/source/campaign
   - Sort by created/status

5. `/ops` focus improvements
   - Collapse secondary panels by default
   - Add lightweight “recent activity” rail

6. Waitlist trust copy
   - Privacy line near email submit
   - Expected response timeline

## P2 — After
7. Motion refinement
   - Success pulse on approvals/publish
   - Error shake/subtle alert on failures
   - Reduced-motion parity

8. Marketing proof layer
   - Replace placeholder proof with real outcomes

## Definition of done
- No P0 items open
- UX checklist average >= 2.4
- Zero critical regressions in build + smoke flow

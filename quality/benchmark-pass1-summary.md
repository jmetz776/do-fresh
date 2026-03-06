# Quality Benchmark — Scoring Pass #1

- Overall average: **4.86/10**
- Lowest sample average: **4.43/10**
- Pass bar: **8.5+ average and no axis below 7**
- Result: **FAIL (rewrite required on all 10/10 samples)**

## Key failure patterns
- Prompt leakage/instruction echo instead of true generated copy
- Weak channel formatting (especially email and short-form script)
- Low specificity and weak conversion intent
- Hook strength too soft for high-performing social posts

## Next fixes (priority)
1. Add strict output templates per task (x post, linkedin post, email, script, reply, hooks list).
2. Add anti-prompt-echo guardrail and regeneration when instruction text appears in output.
3. Add richer task constraints (target audience, CTA, length, tone) into task layer.
4. Add post-generation quality gate: auto-rewrite when any axis proxy is below threshold.

Scored file: `/Users/jaredmetz/.openclaw/workspace/business/demandorchestrator/quality/benchmark-results-pass1.json`
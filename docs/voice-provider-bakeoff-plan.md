# Voice Provider Bakeoff Plan (ElevenLabs vs voicebox.sh)

## Objective
Choose the launch voice provider using measurable quality/reliability/cost data.

## Providers
- Provider A: ElevenLabs (production baseline)
- Provider B: voicebox.sh (local/open alternative)

## Test set
- 30 scripts total:
  - 10 short social voiceovers (10–20s)
  - 10 explainer reads (20–45s)
  - 10 CTA-heavy promos (15–30s)
- 3 tones each: neutral, energetic, authoritative
- 2 speakers each (male/female or chosen brand voices)

## Metrics (scored 1–10 unless stated)
1. Naturalness
2. Intelligibility
3. Emotional fit
4. Pronunciation accuracy (names/brands)
5. Consistency across repeated renders
6. Latency (seconds)
7. Failure rate (%)
8. Unit cost (USD per minute generated)

## Hard launch gates
- Avg quality score >= 8.5
- Pronunciation accuracy >= 95%
- Failure rate <= 2%
- P95 latency <= 12s for short clips
- No critical policy/compliance gaps

## Procedure
1. Run identical script pack through both providers.
2. Blind-score outputs (hide provider identity from reviewers).
3. Compute weighted score:
   - Quality 45%
   - Reliability 25%
   - Latency 15%
   - Cost 15%
4. Decide:
   - Winner = launch primary
   - Runner-up = fallback/secondary lane

## Artifacts
- `quality/voice-bakeoff-inputs.json`
- `quality/voice-bakeoff-results.csv`
- `quality/voice-bakeoff-summary.md`

## Decision policy
- If Provider B beats or matches Provider A on quality/reliability and wins materially on cost, promote B.
- Otherwise launch with A and keep B in R&D.

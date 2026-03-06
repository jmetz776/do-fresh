# DO Prompt Layering Spec (Text/Image/Video)

## Why
Output quality is bottlenecked by prompt quality. We need consistent, high-quality prompts independent of user skill.

## Prompt stack (layered)
1. **System Layer (global rules)**
   - brand-safe behavior
   - style constraints
   - output contract
2. **Product Layer (DO best practices)**
   - channel heuristics
   - structure templates
   - conversion intent logic
3. **Workspace Layer (customer voice)**
   - tone/persona
   - banned terms
   - positioning
4. **Task Layer (current ask)**
   - user input/source material
   - campaign goal
   - format constraints
5. **Post-Processor Layer**
   - quality checks
   - policy checks
   - rewriting/repair if needed

## Capability-specific templates
- Text: hooks, CTA variants, channel format rules
- Image: subject, composition, style, lighting, color, negative prompts
- Video: scene breakdown, pacing, shot language, motion constraints, duration

## Quality loop
- Run auto-scoring per output:
  - clarity
  - brand alignment
  - platform fit
  - conversion strength
- If below threshold, auto-regenerate with targeted guidance.

## Versioning
- Prompt packs are versioned (`prompt_pack_id`, `version`)
- Every generated asset stores prompt pack + model used
- Rollback to prior pack in one click

## Guardrails
- Never expose raw system prompts in UI
- Keep user overrides sandboxed to task/workspace layer
- Enforce safe defaults if user prompt conflicts with policy

## Implementation order
1. Prompt pack schema + loader
2. Layer composer
3. Quality scorer + auto-repair pass
4. UI: preview effective prompt summary (not raw internals)
5. Telemetry: per-pack win rates

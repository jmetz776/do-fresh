# DO Model Registry + Routing Spec (v1)

## Goal
Support fast-changing LLM/image/video ecosystems without frequent code rewrites.

## Core design
- Keep provider/model definitions in a dynamic registry (JSON/DB), not hardcoded.
- Route generation requests through one internal interface.
- Default everyone to **Auto (recommended)**; expose **Advanced model selection** optionally.

## Internal generation interface
- `generate_text(task, input, options)`
- `generate_image(task, input, options)`
- `generate_video(task, input, options)`

Each adapter must return normalized output:
- `content`
- `model_used`
- `provider`
- `latency_ms`
- `usage` (tokens/cost when available)
- `warnings`

## Registry schema (minimum)
- `id` (e.g., `openai:gpt-5.1-mini`)
- `provider` (openai/anthropic/google/...)
- `display_name`
- `capabilities` (`text|image|video`)
- `quality_tier` (`best|high|standard`)
- `speed_tier` (`fast|balanced|slow`)
- `cost_tier` (`low|medium|high`)
- `status` (`active|beta|deprecated`)
- `max_context`
- `supports_json`
- `supports_tools`
- `default_for` (optional task tags)

## Routing policy (Auto mode)
Inputs:
- task type
- target quality/speed profile
- workspace budget guardrail
- provider health (error/latency)

Output:
- ranked candidate list
- selected model + fallback chain

## Advanced mode
- Workspace-level override by capability (text/image/video)
- Campaign-level override optional
- UI shows quality/speed/cost badges + model status

## Reliability
- Auto-fallback on provider/model error
- Circuit-breaker on repeated failures
- Log selected model + fallback events

## Transparency
- Save model metadata on every generated asset
- Show generation provenance in UI (model/provider/time)

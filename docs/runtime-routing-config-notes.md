# Runtime Routing Config Notes (Faceless Pipeline)

## Files
- Registry: `apps/api/app/config/model_registry.json`
- Routing policy: `apps/api/app/config/routing_policy_v1.json`

## Intended runtime contract
1. Resolver loads `routing_policy_v1.json`
2. For a given task:
   - choose lane (`intelligence` or `premium_render`)
   - read `model_pool`
   - intersect with active models in registry
   - rank by existing `pick_model` scoring + lane preference
3. Apply gates before entering premium lane
4. Apply fallback chain on render failure

## Minimal implementation steps
- Add `RoutingPolicy` loader service in `apps/api/app/services/`.
- Add `pick_model_with_policy(task_tag, scores, overrides)` wrapper.
- Call wrapper in generation/render orchestration path.
- Emit routing decision events for audit + cost reporting.

## Event payload (recommended)
```
{
  "workspace_id": "default",
  "task_tag": "faceless_video_render",
  "lane": "premium_render",
  "candidate_models": ["heygen:digital-twin-v2", "runway:gen-3-alpha"],
  "chosen_model": "heygen:digital-twin-v2",
  "scores": {
    "hook_score": 0.81,
    "render_readiness": 0.77
  },
  "decision": "pass_to_premium"
}
```

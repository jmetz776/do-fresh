from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from app.services.routing_policy import RoutingPolicy
except Exception:
    # Fail-open fallback to keep API bootable if routing policy module is unavailable in a deploy.
    class RoutingPolicy:  # type: ignore
        def lane_for_task(self, task_tag: str) -> str:
            return 'intelligence'

        def model_pool_for_task(self, task_tag: str) -> list[str]:
            return []

        def preference_for_task(self, task_tag: str, fallback: str = 'balanced') -> str:
            return fallback

        def render_pass(self, scores: Optional[Dict[str, float]] = None) -> bool:
            return True

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / 'config' / 'model_registry.json'


class ModelRegistry:
    def __init__(self, path: Optional[str] = None):
        override = (path or os.getenv('DO_MODEL_REGISTRY_PATH') or '').strip()
        self.path = Path(override) if override else DEFAULT_REGISTRY_PATH
        self._cache: Optional[List[Dict[str, Any]]] = None

    def models(self) -> List[Dict[str, Any]]:
        if self._cache is not None:
            return self._cache
        if not self.path.exists():
            self._cache = []
            return self._cache
        payload = json.loads(self.path.read_text(encoding='utf-8'))
        self._cache = payload.get('models', []) if isinstance(payload, dict) else []
        return self._cache

    def active_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        out = []
        for m in self.models():
            if m.get('status') != 'active':
                continue
            caps = m.get('capabilities') or []
            if capability in caps:
                out.append(m)
        return out

    def get_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        for m in self.models():
            if m.get('id') == model_id and m.get('status') == 'active':
                return m
        return None


def _score_model(m: Dict[str, Any], task_tag: str, preference: str) -> int:
    score = 0
    defaults = m.get('default_for') or []
    if task_tag in defaults:
        score += 20

    quality = m.get('quality_tier', 'standard')
    speed = m.get('speed_tier', 'balanced')
    cost = m.get('cost_tier', 'medium')

    if preference == 'quality':
        score += {'best': 15, 'high': 12, 'standard': 8}.get(quality, 6)
        score += {'slow': 3, 'balanced': 4, 'fast': 5}.get(speed, 3)
    elif preference == 'speed':
        score += {'fast': 15, 'balanced': 10, 'slow': 6}.get(speed, 8)
        score += {'low': 6, 'medium': 5, 'high': 4}.get(cost, 5)
    else:  # balanced
        score += {'high': 10, 'best': 11, 'standard': 8}.get(quality, 8)
        score += {'fast': 9, 'balanced': 10, 'slow': 7}.get(speed, 8)
        score += {'low': 8, 'medium': 9, 'high': 7}.get(cost, 8)

    return score


def estimate_text_cost_usd(model: Dict[str, Any], input_tokens: float, output_tokens: float) -> float:
    pricing = model.get('pricing') or {}
    in_per_1m = float(pricing.get('input_per_1m_usd', 0.0) or 0.0)
    out_per_1m = float(pricing.get('output_per_1m_usd', 0.0) or 0.0)
    return round((input_tokens / 1_000_000.0) * in_per_1m + (output_tokens / 1_000_000.0) * out_per_1m, 6)


def pick_model(capability: str, task_tag: str, preference: str = 'balanced', override_model_id: Optional[str] = None) -> Dict[str, Any]:
    reg = ModelRegistry()
    if override_model_id:
        chosen = reg.get_by_id(override_model_id)
        if chosen and capability in (chosen.get('capabilities') or []):
            return chosen

    candidates = reg.active_by_capability(capability)
    if not candidates:
        return {
            'id': 'internal:stub-text',
            'provider': 'internal',
            'display_name': 'Internal Stub',
            'capabilities': [capability],
            'quality_tier': 'standard',
            'speed_tier': 'fast',
            'cost_tier': 'low',
            'status': 'active',
        }

    ranked = sorted(candidates, key=lambda m: _score_model(m, task_tag, preference), reverse=True)
    return ranked[0]


def pick_model_with_policy(
    capability: str,
    task_tag: str,
    preference: str = 'balanced',
    override_model_id: Optional[str] = None,
    scores: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    policy = RoutingPolicy()
    lane = policy.lane_for_task(task_tag)

    if lane == 'premium_render' and not policy.render_pass(scores=scores):
        return {
            'id': 'internal:gate-blocked',
            'provider': 'internal',
            'display_name': 'Gate Blocked',
            'capabilities': [capability],
            'quality_tier': 'standard',
            'speed_tier': 'fast',
            'cost_tier': 'low',
            'status': 'active',
            '_decision': 'rewrite_or_regenerate',
            '_lane': lane,
        }

    reg = ModelRegistry()
    pool = policy.model_pool_for_task(task_tag)
    if pool:
        pool_models = []
        for model_id in pool:
            m = reg.get_by_id(model_id)
            if m and capability in (m.get('capabilities') or []):
                pool_models.append(m)
        if pool_models:
            pref = policy.preference_for_task(task_tag, fallback=preference)
            ranked = sorted(pool_models, key=lambda m: _score_model(m, task_tag, pref), reverse=True)
            chosen = ranked[0]
            chosen = {**chosen, '_lane': lane, '_decision': 'policy_pool_select'}
            return chosen

    chosen = pick_model(capability=capability, task_tag=task_tag, preference=preference, override_model_id=override_model_id)
    return {**chosen, '_lane': lane, '_decision': 'registry_fallback'}

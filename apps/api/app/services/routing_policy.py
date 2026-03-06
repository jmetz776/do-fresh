from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = ROOT / 'config' / 'routing_policy_v1.json'


class RoutingPolicy:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path) if path else DEFAULT_POLICY_PATH
        self._cache: Optional[Dict[str, Any]] = None

    def data(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if not self.path.exists():
            self._cache = {}
            return self._cache
        try:
            self._cache = json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:
            self._cache = {}
        return self._cache

    def lane_for_task(self, task_tag: str) -> str:
        d = self.data()
        lanes = d.get('lanes') or {}
        for lane_name, lane_cfg in lanes.items():
            if task_tag in (lane_cfg.get('tasks') or []):
                return lane_name
        return 'intelligence'

    def model_pool_for_task(self, task_tag: str) -> list[str]:
        d = self.data()
        lane = self.lane_for_task(task_tag)
        lane_cfg = ((d.get('lanes') or {}).get(lane) or {})
        return [str(x) for x in (lane_cfg.get('model_pool') or [])]

    def preference_for_task(self, task_tag: str, fallback: str = 'balanced') -> str:
        d = self.data()
        lane = self.lane_for_task(task_tag)
        lane_cfg = ((d.get('lanes') or {}).get(lane) or {})
        return str(lane_cfg.get('preference') or fallback)

    def render_pass(self, scores: Optional[Dict[str, float]] = None) -> bool:
        d = self.data()
        gates = d.get('gates') or {}
        req = (gates.get('required_minimums') or {})
        rr = ((gates.get('render_readiness') or {}).get('pass_threshold') or 0.72)
        s = scores or {}
        for k, v in req.items():
            if float(s.get(k, 0.0)) < float(v):
                return False
        if float(s.get('render_readiness', 0.0)) < float(rr):
            return False
        return True

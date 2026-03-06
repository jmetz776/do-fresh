from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict


def _prefs_path() -> Path:
    raw = os.getenv('DO_MODEL_PREFS_PATH', './model_prefs.json')
    return Path(raw)


def load_prefs() -> Dict[str, dict]:
    p = _prefs_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def get_workspace_prefs(workspace_id: str) -> dict:
    all_prefs = load_prefs()
    return all_prefs.get(workspace_id, {'mode': 'auto', 'overrides': {}})


def set_workspace_prefs(workspace_id: str, mode: str, overrides: dict) -> dict:
    mode = mode if mode in ('auto', 'advanced') else 'auto'
    payload = {'mode': mode, 'overrides': overrides or {}}
    all_prefs = load_prefs()
    all_prefs[workspace_id] = payload

    p = _prefs_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(all_prefs, indent=2), encoding='utf-8')
    return payload

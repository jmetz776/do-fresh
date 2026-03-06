from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, select

try:
    from app.models.mvp import MVPGenerationCostEvent
except Exception:  # pragma: no cover - deploy compatibility fallback
    MVPGenerationCostEvent = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PLAN_LIMITS_PATH = Path(os.getenv('DO_PLAN_LIMITS_PATH', str(ROOT / 'config' / 'plan_limits.json')))
WORKSPACE_PLAN_PATH = Path(os.getenv('DO_WORKSPACE_PLAN_PATH', './workspace_plans.json'))


def _month_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _load_plan_config() -> dict[str, Any]:
    if not PLAN_LIMITS_PATH.exists():
        return {'plans': {'starter': {'included_monthly_cost_usd': 10, 'hard_cap_monthly_cost_usd': 25, 'allowed_quality_tiers': ['standard'], 'allow_advanced_models': False}}, 'default_plan': 'starter'}
    return json.loads(PLAN_LIMITS_PATH.read_text(encoding='utf-8'))


def _workspace_plan(workspace_id: str) -> str:
    if not WORKSPACE_PLAN_PATH.exists():
        return _load_plan_config().get('default_plan', 'starter')
    try:
        data = json.loads(WORKSPACE_PLAN_PATH.read_text(encoding='utf-8'))
        return data.get(workspace_id) or data.get('default') or _load_plan_config().get('default_plan', 'starter')
    except Exception:
        return _load_plan_config().get('default_plan', 'starter')


def _current_month_cost(session: Session, workspace_id: str) -> float:
    if MVPGenerationCostEvent is None:
        return 0.0
    start = _month_start_utc()
    total = session.exec(
        select(func.sum(MVPGenerationCostEvent.estimated_cost_usd)).where(
            MVPGenerationCostEvent.workspace_id == workspace_id,
            MVPGenerationCostEvent.created_at >= start,
        )
    ).one()
    return float(total or 0.0)


def evaluate_generation_guardrail(session: Session, workspace_id: str, model: dict, projected_cost: float, mode: str = 'auto') -> dict[str, Any]:
    cfg = _load_plan_config()
    plan_name = _workspace_plan(workspace_id)
    plan = (cfg.get('plans') or {}).get(plan_name) or (cfg.get('plans') or {}).get(cfg.get('default_plan', 'starter'))

    current = _current_month_cost(session, workspace_id)
    projected_total = current + max(0.0, projected_cost)

    hard_cap = float(plan.get('hard_cap_monthly_cost_usd', 25))
    included = float(plan.get('included_monthly_cost_usd', hard_cap * 0.5))
    allowed_tiers = set(plan.get('allowed_quality_tiers', ['standard']))
    model_tier = model.get('quality_tier', 'standard')

    if mode == 'advanced' and not bool(plan.get('allow_advanced_models', False)):
        return {'allowed': False, 'reason': 'Advanced model mode not allowed on current plan', 'plan': plan_name, 'currentMonthlyCostUsd': round(current, 6), 'projectedMonthlyCostUsd': round(projected_total, 6)}

    if model_tier not in allowed_tiers:
        return {'allowed': False, 'reason': f'Model tier {model_tier} not allowed on plan {plan_name}', 'plan': plan_name, 'currentMonthlyCostUsd': round(current, 6), 'projectedMonthlyCostUsd': round(projected_total, 6)}

    if projected_total > hard_cap:
        return {'allowed': False, 'reason': f'Projected monthly cost exceeds hard cap (${hard_cap})', 'plan': plan_name, 'currentMonthlyCostUsd': round(current, 6), 'projectedMonthlyCostUsd': round(projected_total, 6)}

    warning = None
    if projected_total >= included * 0.8:
        warning = f'Usage above 80% of included monthly budget (${included})'

    return {
        'allowed': True,
        'warning': warning,
        'plan': plan_name,
        'currentMonthlyCostUsd': round(current, 6),
        'projectedMonthlyCostUsd': round(projected_total, 6),
        'includedMonthlyCostUsd': included,
        'hardCapMonthlyCostUsd': hard_cap,
    }

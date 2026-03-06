from __future__ import annotations

import json

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.auth import Workspace, WorkspaceSetting


FEATURES = {
    'basic_publish': {'personal', 'corporate'},
    'rbac': {'corporate'},
    'approval_workflow': {'corporate'},
    'publish_authorization_matrix': {'corporate'},
    'full_audit_log': {'corporate'},
}


def workspace_account_type(session: Session, workspace_id: str) -> str:
    row = session.exec(
        select(WorkspaceSetting).where(
            WorkspaceSetting.workspace_id == workspace_id,
            WorkspaceSetting.key == 'account.type',
        )
    ).first()
    if row and row.value_json:
        try:
            v = json.loads(row.value_json)
            return str(v or '').strip().lower() or 'personal'
        except Exception:
            pass

    ws = session.exec(select(Workspace).where(Workspace.id == workspace_id)).first()
    tier = (ws.plan_tier if ws else 'starter').lower()
    return 'corporate' if tier == 'corporate' else 'personal'


def require_feature(session: Session, workspace_id: str, feature: str) -> str:
    account_type = workspace_account_type(session, workspace_id)
    allowed = FEATURES.get(feature, {'corporate'})
    if account_type not in allowed:
        raise HTTPException(status_code=403, detail=f'feature {feature} requires {"/".join(sorted(allowed))} account')
    return account_type

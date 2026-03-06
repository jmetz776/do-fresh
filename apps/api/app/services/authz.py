from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException
from sqlmodel import Session, select

from app.models.auth import WorkspaceMembership, WorkspaceSetting
from app.services.session_token import verify_token

ROLE_RANK = {
    'viewer': 1,
    'editor': 2,
    'publisher': 3,
    'admin': 4,
    'owner': 5,
}


def _rank(role: str) -> int:
    return ROLE_RANK.get((role or '').lower().strip(), 0)


def require_workspace_role(
    session: Session,
    workspace_id: str,
    min_role: str,
    user_id: str,
) -> WorkspaceMembership:
    stmt = select(WorkspaceMembership).where(
        WorkspaceMembership.workspace_id == workspace_id,
        WorkspaceMembership.user_id == user_id,
        WorkspaceMembership.status == 'active',
    )
    membership = session.exec(stmt).first()
    if not membership:
        raise HTTPException(status_code=403, detail='workspace membership required')

    if _rank(membership.role) < _rank(min_role):
        raise HTTPException(status_code=403, detail=f'{min_role}+ role required')

    return membership


def _token_payload(authorization: Optional[str]) -> dict:
    auth = (authorization or '').strip()
    if not auth.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='missing bearer token')
    token = auth.split(' ', 1)[1].strip()
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='invalid or expired token')
    return payload


def actor_user_id(authorization: Optional[str] = Header(default=None, alias='Authorization')) -> str:
    payload = _token_payload(authorization)
    user_id = str(payload.get('sub') or '').strip()
    if not user_id:
        raise HTTPException(status_code=401, detail='token missing subject')
    return user_id


def actor_user_email(authorization: Optional[str] = Header(default=None, alias='Authorization')) -> str:
    payload = _token_payload(authorization)
    email = str(payload.get('email') or '').strip().lower()
    if not email or '@' not in email:
        raise HTTPException(status_code=401, detail='token missing email')
    return email


def allowed_workspace_domains(session: Session, workspace_id: str) -> set[str]:
    stmt = select(WorkspaceSetting).where(
        WorkspaceSetting.workspace_id == workspace_id,
        WorkspaceSetting.key == 'auth.allowed_domains',
    )
    row = session.exec(stmt).first()
    if row and row.value_json:
        try:
            import json

            values = json.loads(row.value_json)
            if isinstance(values, list):
                return {str(v).strip().lower() for v in values if str(v).strip()}
        except Exception:
            pass

    env_domains = os.getenv('CORP_ALLOWED_DOMAINS', '').strip()
    if env_domains:
        return {d.strip().lower() for d in env_domains.split(',') if d.strip()}
    return set()


def require_corporate_email_domain(session: Session, workspace_id: str, email: str) -> None:
    domain = email.split('@')[-1].strip().lower()
    allowed = allowed_workspace_domains(session, workspace_id)
    if not allowed:
        raise HTTPException(status_code=403, detail='workspace corporate domains not configured')
    if domain not in allowed:
        raise HTTPException(status_code=403, detail='email domain is not authorized for this workspace')

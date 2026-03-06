from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models.auth import User, Workspace, WorkspaceMembership, WorkspaceSetting, BetaInvite, MagicLinkToken
from app.services.session_token import issue_token, verify_token
from app.services.security_state import clear_rate_limit, rate_limit_hit, revoke_jti

router = APIRouter(prefix='/auth', tags=['auth'])

CONSUMER_DOMAINS = {
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'aol.com', 'proton.me', 'protonmail.com'
}

LOGIN_RATE_LIMIT = int(os.getenv('AUTH_LOGIN_RATE_LIMIT', '10'))
LOGIN_WINDOW_SECONDS = int(os.getenv('AUTH_LOGIN_WINDOW_SECONDS', '300'))
INVITE_ONLY_MODE = os.getenv('AUTH_INVITE_ONLY', 'true').strip().lower() == 'true'
MAGIC_LINK_TTL_MINUTES = int(os.getenv('AUTH_MAGIC_LINK_TTL_MINUTES', '20'))
MAGIC_LINK_BASE_URL = os.getenv('AUTH_MAGIC_LINK_BASE_URL', 'https://demandorchestrator.ai/login')
INVITE_ADMIN_KEY = os.getenv('AUTH_INVITE_ADMIN_KEY', '').strip()
SUPERUSER_EMAILS = {e.strip().lower() for e in os.getenv('AUTH_SUPERUSER_EMAILS', '').split(',') if e.strip()}


def _check_login_rate_limit(email: str) -> None:
    key = f"login:{(email or '').strip().lower()}"
    if rate_limit_hit(key, LOGIN_RATE_LIMIT, LOGIN_WINDOW_SECONDS):
        raise HTTPException(status_code=429, detail='too many login attempts; try again shortly')


def _clear_login_rate_limit(email: str) -> None:
    key = f"login:{(email or '').strip().lower()}"
    clear_rate_limit(key)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _is_past(dt: Optional[datetime]) -> bool:
    if not dt:
        return False
    if dt.tzinfo is None:
        return dt < datetime.utcnow()
    return dt < now_utc()


def _is_superuser_email(email: str) -> bool:
    return (email or '').strip().lower() in SUPERUSER_EMAILS


def _require_invite_admin_or_superuser(session: Session, x_admin_key: Optional[str], authorization: Optional[str]) -> None:
    if INVITE_ADMIN_KEY and (x_admin_key or '').strip() == INVITE_ADMIN_KEY:
        return

    auth = (authorization or '').strip()
    if auth.lower().startswith('bearer '):
        token = auth.split(' ', 1)[1].strip()
        payload = verify_token(token)
        if payload:
            email = str(payload.get('email') or '').strip().lower()
            if email and _is_superuser_email(email):
                # Ensure the bearer user still exists.
                user = session.exec(select(User).where(User.email == email)).first()
                if user:
                    return

    if INVITE_ADMIN_KEY or SUPERUSER_EMAILS:
        raise HTTPException(status_code=403, detail='forbidden')
    raise HTTPException(status_code=503, detail='invite admin controls not configured')


def _hash_magic_token(raw: str) -> str:
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _active_invite_for_email(session: Session, email: str) -> Optional[BetaInvite]:
    rows = session.exec(
        select(BetaInvite)
        .where(BetaInvite.email == email, BetaInvite.status == 'active')
        .order_by(BetaInvite.created_at.desc())
    ).all()
    ts = now_utc()
    for inv in rows:
        if _is_past(inv.expires_at):
            inv.status = 'expired'
            inv.updated_at = ts
            session.add(inv)
            continue
        if inv.used_count >= max(1, inv.max_uses):
            inv.status = 'used'
            inv.updated_at = ts
            session.add(inv)
            continue
        return inv
    session.commit()
    return None


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 120_000)
    return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt_b64, digest_b64 = stored.split('$', 2)
        if algo != 'pbkdf2_sha256':
            return False
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _get_workspace_account_type(session: Session, workspace_id: str) -> str:
    row = session.exec(
        select(WorkspaceSetting).where(
            WorkspaceSetting.workspace_id == workspace_id,
            WorkspaceSetting.key == 'account.type',
        )
    ).first()
    if not row:
        return 'personal'
    try:
        v = json.loads(row.value_json or '"personal"')
        return str(v or 'personal')
    except Exception:
        return 'personal'


class RegisterPersonalRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    workspaceName: str = Field(default='My Workspace', min_length=2, max_length=120)


class RegisterCorporateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    workspaceName: str = Field(default='Corporate Workspace', min_length=2, max_length=120)
    companyDomain: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class CreateInviteRequest(BaseModel):
    email: EmailStr
    workspaceName: str = Field(default='Beta Workspace', min_length=2, max_length=120)
    role: str = Field(default='owner')
    expiresInHours: int = Field(default=168, ge=1, le=24 * 90)
    maxUses: int = Field(default=1, ge=1, le=10)


class RequestMagicLinkRequest(BaseModel):
    email: EmailStr


class ConsumeMagicLinkRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)


@router.post('/register/personal')
def register_personal(payload: RegisterPersonalRequest, session: Session = Depends(get_session)):
    email = str(payload.email).strip().lower()
    if INVITE_ONLY_MODE and not _active_invite_for_email(session, email):
        raise HTTPException(status_code=403, detail='invite required')
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=409, detail='email already registered')

    user_id = f"u_{uuid4().hex[:12]}"
    workspace_id = f"ws_{uuid4().hex[:12]}"
    ts = now_utc()

    user = User(
        id=user_id,
        email=email,
        email_verified=True,
        password_hash=_hash_password(payload.password),
        created_at=ts,
    )
    ws = Workspace(
        id=workspace_id,
        name=payload.workspaceName,
        plan_tier='starter',
        owner_user_id=user_id,
        created_at=ts,
    )
    membership = WorkspaceMembership(
        id=str(uuid4()),
        workspace_id=workspace_id,
        user_id=user_id,
        role='owner',
        status='active',
        created_at=ts,
    )
    setting = WorkspaceSetting(
        id=str(uuid4()),
        workspace_id=workspace_id,
        key='account.type',
        value_json='"personal"',
        created_at=ts,
        updated_at=ts,
    )

    session.add(user)
    session.add(ws)
    session.add(membership)
    session.add(setting)
    session.commit()

    return {
        'ok': True,
        'accountType': 'personal',
        'workspaceId': workspace_id,
        'planTier': 'starter',
        'user': {'id': user_id, 'email': email},
        'token': issue_token(user_id=user_id, email=email, workspace_id=workspace_id, role='owner'),
    }


@router.post('/register/corporate')
def register_corporate(payload: RegisterCorporateRequest, session: Session = Depends(get_session)):
    email = str(payload.email).strip().lower()
    if INVITE_ONLY_MODE and not _active_invite_for_email(session, email):
        raise HTTPException(status_code=403, detail='invite required')
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=409, detail='email already registered')

    email_domain = email.split('@')[-1]
    company_domain = (payload.companyDomain or email_domain).strip().lower()
    if company_domain in CONSUMER_DOMAINS:
        raise HTTPException(status_code=400, detail='corporate account requires a business domain email')

    user_id = f"u_{uuid4().hex[:12]}"
    workspace_id = f"ws_{uuid4().hex[:12]}"
    ts = now_utc()

    user = User(
        id=user_id,
        email=email,
        email_verified=True,
        password_hash=_hash_password(payload.password),
        created_at=ts,
    )
    ws = Workspace(
        id=workspace_id,
        name=payload.workspaceName,
        plan_tier='corporate',
        owner_user_id=user_id,
        created_at=ts,
    )
    membership = WorkspaceMembership(
        id=str(uuid4()),
        workspace_id=workspace_id,
        user_id=user_id,
        role='owner',
        status='active',
        created_at=ts,
    )
    type_setting = WorkspaceSetting(
        id=str(uuid4()),
        workspace_id=workspace_id,
        key='account.type',
        value_json='"corporate"',
        created_at=ts,
        updated_at=ts,
    )
    domain_setting = WorkspaceSetting(
        id=str(uuid4()),
        workspace_id=workspace_id,
        key='auth.allowed_domains',
        value_json=json.dumps([company_domain]),
        created_at=ts,
        updated_at=ts,
    )

    session.add(user)
    session.add(ws)
    session.add(membership)
    session.add(type_setting)
    session.add(domain_setting)
    session.commit()

    return {
        'ok': True,
        'accountType': 'corporate',
        'workspaceId': workspace_id,
        'planTier': 'corporate',
        'allowedDomains': [company_domain],
        'user': {'id': user_id, 'email': email},
        'token': issue_token(user_id=user_id, email=email, workspace_id=workspace_id, role='owner'),
    }


@router.get('/entitlements/{account_type}')
def entitlements(account_type: str):
    key = (account_type or '').strip().lower()
    matrix = {
        'personal': {
            'priceHint': 'lower',
            'seats': 1,
            'sso': False,
            'rbac': False,
            'approvalWorkflow': False,
            'publishAuthorizationMatrix': False,
            'auditLog': 'basic',
        },
        'corporate': {
            'priceHint': 'premium',
            'seats': 'multi',
            'sso': True,
            'rbac': True,
            'approvalWorkflow': True,
            'publishAuthorizationMatrix': True,
            'auditLog': 'full',
        },
    }
    if key not in matrix:
        raise HTTPException(status_code=404, detail='unknown account type')
    return {'accountType': key, 'entitlements': matrix[key]}


@router.post('/refresh')
def refresh_token(authorization: Optional[str] = Header(default=None, alias='Authorization')):
    auth = (authorization or '').strip()
    if not auth.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='missing bearer token')
    token = auth.split(' ', 1)[1].strip()
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='invalid or expired token')

    user_id = str(payload.get('sub') or '').strip()
    email = str(payload.get('email') or '').strip().lower()
    workspace_id = str(payload.get('workspace_id') or '').strip()
    role = str(payload.get('role') or 'viewer').strip().lower()
    if not user_id or not email or not workspace_id:
        raise HTTPException(status_code=401, detail='invalid token payload')

    return {
        'ok': True,
        'token': issue_token(user_id=user_id, email=email, workspace_id=workspace_id, role=role),
    }


@router.post('/logout')
def logout(authorization: Optional[str] = Header(default=None, alias='Authorization')):
    auth = (authorization or '').strip()
    if auth.lower().startswith('bearer '):
        token = auth.split(' ', 1)[1].strip()
        payload = verify_token(token)
        if payload:
            jti = str(payload.get('jti') or '')
            exp = int(payload.get('exp') or 0)
            if jti and exp:
                revoke_jti(jti, exp)
    return {'ok': True}


@router.get('/me')
def me(authorization: Optional[str] = Header(default=None, alias='Authorization'), session: Session = Depends(get_session)):
    auth = (authorization or '').strip()
    if not auth.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='missing bearer token')
    token = auth.split(' ', 1)[1].strip()
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='invalid or expired token')

    user_id = str(payload.get('sub') or '').strip()
    email = str(payload.get('email') or '').strip().lower()
    workspace_id = str(payload.get('workspace_id') or '').strip()
    role = str(payload.get('role') or 'viewer').strip().lower()
    if not user_id or not email or not workspace_id:
        raise HTTPException(status_code=401, detail='invalid token payload')

    ws = session.exec(select(Workspace).where(Workspace.id == workspace_id)).first()
    if not ws:
        raise HTTPException(status_code=404, detail='workspace not found')
    account_type = _get_workspace_account_type(session, workspace_id)

    return {
        'ok': True,
        'user': {'id': user_id, 'email': email},
        'workspaceId': workspace_id,
        'role': role,
        'accountType': account_type,
        'planTier': ws.plan_tier,
    }


@router.post('/invites')
def create_invite(
    payload: CreateInviteRequest,
    session: Session = Depends(get_session),
    x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key'),
    authorization: Optional[str] = Header(default=None, alias='Authorization'),
):
    _require_invite_admin_or_superuser(session, x_admin_key, authorization)
    email = str(payload.email).strip().lower()
    ts = now_utc()
    inv = BetaInvite(
        id=str(uuid4()),
        email=email,
        workspace_name=payload.workspaceName,
        role=(payload.role or 'owner').strip().lower(),
        status='active',
        expires_at=ts + timedelta(hours=payload.expiresInHours),
        max_uses=payload.maxUses,
        used_count=0,
        created_by='admin',
        created_at=ts,
        updated_at=ts,
    )
    session.add(inv)
    session.commit()
    return {
        'ok': True,
        'invite': {
            'id': inv.id,
            'email': inv.email,
            'workspaceName': inv.workspace_name,
            'role': inv.role,
            'expiresAt': inv.expires_at.isoformat() if inv.expires_at else None,
            'maxUses': inv.max_uses,
        },
    }


@router.post('/magic-link/request')
def request_magic_link(payload: RequestMagicLinkRequest, session: Session = Depends(get_session)):
    email = str(payload.email).strip().lower()
    invite = _active_invite_for_email(session, email)

    # Permanent bootstrap rule: superuser emails can always request magic links.
    if INVITE_ONLY_MODE and not invite and not _is_superuser_email(email):
        raise HTTPException(status_code=403, detail='invite required')

    if not invite:
        # Fallback for non-invite mode OR superuser bootstrap mode.
        invite = BetaInvite(
            id=str(uuid4()),
            email=email,
            workspace_name='Beta Workspace' if not _is_superuser_email(email) else 'Superuser Workspace',
            role='owner',
            status='active',
            max_uses=10 if not _is_superuser_email(email) else 100,
            used_count=0,
            created_by='self-serve' if not _is_superuser_email(email) else 'superuser-bootstrap',
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        session.add(invite)
        session.commit()

    raw = secrets.token_urlsafe(32)
    ts = now_utc()
    token_row = MagicLinkToken(
        id=str(uuid4()),
        email=email,
        invite_id=invite.id,
        token_hash=_hash_magic_token(raw),
        status='issued',
        expires_at=ts + timedelta(minutes=MAGIC_LINK_TTL_MINUTES),
        created_at=ts,
    )
    session.add(token_row)
    session.commit()

    magic_url = f"{MAGIC_LINK_BASE_URL}?token={raw}"
    return {
        'ok': True,
        'email': email,
        'expiresInMinutes': MAGIC_LINK_TTL_MINUTES,
        # Until email provider is wired, return link directly for operator/tester use.
        'magicUrl': magic_url,
    }


@router.post('/magic-link/consume')
def consume_magic_link(payload: ConsumeMagicLinkRequest, session: Session = Depends(get_session)):
    token_hash = _hash_magic_token(payload.token.strip())
    row = session.exec(
        select(MagicLinkToken)
        .where(MagicLinkToken.token_hash == token_hash)
        .order_by(MagicLinkToken.created_at.desc())
    ).first()
    if not row:
        raise HTTPException(status_code=401, detail='invalid token')

    if _is_past(row.expires_at):
        row.status = 'expired'
        session.add(row)
        session.commit()
        raise HTTPException(status_code=401, detail='token expired')

    if row.status in {'revoked', 'expired'}:
        raise HTTPException(status_code=401, detail='token already used or revoked')

    invite = session.get(BetaInvite, row.invite_id)
    if not invite or invite.status not in {'active', 'used'}:
        raise HTTPException(status_code=403, detail='invite unavailable')

    email = row.email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()
    ts = now_utc()
    if not user:
        user = User(
            id=f"u_{uuid4().hex[:12]}",
            email=email,
            email_verified=True,
            password_hash=None,
            created_at=ts,
        )
        session.add(user)
        session.flush()

    membership = session.exec(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user.id,
            WorkspaceMembership.status == 'active',
        )
    ).first()

    ws = None
    if membership:
        ws = session.exec(select(Workspace).where(Workspace.id == membership.workspace_id)).first()
    if not ws:
        workspace_id = f"ws_{uuid4().hex[:12]}"
        ws = Workspace(
            id=workspace_id,
            name=invite.workspace_name,
            plan_tier='starter',
            owner_user_id=user.id,
            created_at=ts,
        )
        membership = WorkspaceMembership(
            id=str(uuid4()),
            workspace_id=workspace_id,
            user_id=user.id,
            role=invite.role or 'owner',
            status='active',
            created_at=ts,
        )
        setting = WorkspaceSetting(
            id=str(uuid4()),
            workspace_id=workspace_id,
            key='account.type',
            value_json='"personal"',
            created_at=ts,
            updated_at=ts,
        )
        session.add(ws)
        session.add(membership)
        session.add(setting)

    first_consume = row.status == 'issued'
    row.status = 'consumed'
    if not row.consumed_at:
        row.consumed_at = ts

    if first_consume:
        invite.used_count += 1
        if invite.used_count >= max(1, invite.max_uses):
            invite.status = 'used'
        invite.updated_at = ts

    session.add(row)
    session.add(invite)
    session.commit()

    return {
        'ok': True,
        'workspaceId': ws.id,
        'role': membership.role if membership else 'owner',
        'user': {'id': user.id, 'email': user.email},
        'token': issue_token(user_id=user.id, email=user.email, workspace_id=ws.id, role=(membership.role if membership else 'owner')),
    }


@router.post('/login')
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    email = str(payload.email).strip().lower()
    _check_login_rate_limit(email)
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not user.password_hash or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='invalid credentials')

    _clear_login_rate_limit(email)

    membership = session.exec(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user.id,
            WorkspaceMembership.status == 'active',
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail='no active workspace membership')

    ws = session.exec(select(Workspace).where(Workspace.id == membership.workspace_id)).first()
    if not ws:
        raise HTTPException(status_code=404, detail='workspace not found')

    account_type = _get_workspace_account_type(session, ws.id)

    return {
        'ok': True,
        'accountType': account_type,
        'workspaceId': ws.id,
        'planTier': ws.plan_tier,
        'role': membership.role,
        'user': {'id': user.id, 'email': user.email},
        'token': issue_token(user_id=user.id, email=user.email, workspace_id=ws.id, role=membership.role),
    }

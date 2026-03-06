from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models.provider_health import ProviderHealthStatus
from app.services.apify_client import ApifyClient
from app.services.heygen_client import HeyGenClient

router = APIRouter(prefix='/system', tags=['system-status'])


def _set_health(session: Session, provider: str, status: str, message: str, failed: bool) -> ProviderHealthStatus:
    row = session.exec(
        select(ProviderHealthStatus)
        .where(ProviderHealthStatus.provider == provider)
        .order_by(ProviderHealthStatus.checked_at.desc())
    ).first()

    now = datetime.utcnow()
    if not row:
        row = ProviderHealthStatus(
            id=f'phs_{uuid4().hex[:14]}',
            provider=provider,
            status=status,
            message=message,
            consecutive_failures=1 if failed else 0,
            checked_at=now,
            updated_at=now,
        )
    else:
        row.status = status
        row.message = message
        row.consecutive_failures = (row.consecutive_failures + 1) if failed else 0
        row.checked_at = now
        row.updated_at = now
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.post('/provider-health/check')
def check_provider_health(
    probe: bool = Query(default=False),
    session: Session = Depends(get_session),
):
    out = []

    # HeyGen
    hey = HeyGenClient()
    if not hey.configured():
        row = _set_health(session, 'heygen', 'down', 'No API key configured', True)
    else:
        status = 'healthy'
        msg = f'Configured ({len(hey.api_keys)} key(s))'
        failed = False
        if probe:
            ok, probe_msg = hey.health_probe()
            status = 'healthy' if ok else 'degraded'
            msg = probe_msg
            failed = not ok
        row = _set_health(session, 'heygen', status, msg, failed)
    out.append({'provider': row.provider, 'status': row.status, 'message': row.message, 'checkedAt': row.checked_at.isoformat()})

    # Apify
    ap = ApifyClient()
    if not ap.configured():
        row = _set_health(session, 'apify', 'down', 'No API token configured', True)
    else:
        status = 'healthy'
        msg = f'Configured ({len(ap.tokens)} token(s))'
        failed = False
        if probe:
            ok, probe_msg = ap.health_probe()
            status = 'healthy' if ok else 'degraded'
            msg = probe_msg
            failed = not ok
        row = _set_health(session, 'apify', status, msg, failed)
    out.append({'provider': row.provider, 'status': row.status, 'message': row.message, 'checkedAt': row.checked_at.isoformat()})

    maintenance = {
        'enabled': (os.getenv('DO_MAINTENANCE_MODE') or 'false').strip().lower() == 'true',
        'message': (os.getenv('DO_MAINTENANCE_MESSAGE') or '').strip(),
    }

    return {'ok': True, 'providers': out, 'maintenance': maintenance}


@router.get('/provider-health')
def get_provider_health(session: Session = Depends(get_session)):
    rows = session.exec(select(ProviderHealthStatus).order_by(ProviderHealthStatus.checked_at.desc())).all()
    latest = {}
    for r in rows:
        if r.provider not in latest:
            latest[r.provider] = {
                'provider': r.provider,
                'status': r.status,
                'message': r.message,
                'consecutiveFailures': r.consecutive_failures,
                'checkedAt': r.checked_at.isoformat(),
            }

    maintenance = {
        'enabled': (os.getenv('DO_MAINTENANCE_MODE') or 'false').strip().lower() == 'true',
        'message': (os.getenv('DO_MAINTENANCE_MESSAGE') or '').strip(),
    }
    return {'items': list(latest.values()), 'maintenance': maintenance}

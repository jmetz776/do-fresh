import csv
import io
import json
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlmodel import Session, select

from app.db import get_session
from app.models.core import Campaign, Asset, ApprovalEvent, Lead, LeadActivityEvent
from app.schemas.campaigns import CreateCampaignRequest, CampaignOut, AssetOut, AssetActionRequest
from app.schemas.leads import LeadCreateRequest, LeadOut
from pydantic import BaseModel
from app.services.generation import generate_seed_assets, regenerate_asset_content

router = APIRouter()


class LeadStatusUpdateRequest(BaseModel):
    status: str


def _send_waitlist_alert_email(lead: Lead, profile: Optional[dict] = None) -> None:
    to_email = (os.getenv('WAITLIST_ALERT_TO_EMAIL') or '').strip()
    smtp_host = (os.getenv('SMTP_HOST') or '').strip()
    smtp_user = (os.getenv('SMTP_USER') or '').strip()
    smtp_pass = (os.getenv('SMTP_PASS') or '').strip()
    smtp_from = (os.getenv('SMTP_FROM') or smtp_user or '').strip()
    smtp_port = int((os.getenv('SMTP_PORT') or '587').strip() or '587')
    approve_token = (os.getenv('WAITLIST_APPROVAL_TOKEN') or '').strip()
    web_base = (os.getenv('WEB_APP_BASE') or 'http://127.0.0.1:3000').rstrip('/')
    api_base = (os.getenv('API_BASE') or os.getenv('NEXT_PUBLIC_API_BASE') or 'http://127.0.0.1:8000').rstrip('/')

    if not (to_email and smtp_host and smtp_from and smtp_user and smtp_pass and approve_token):
        return

    admin_url = f"{web_base}/waitlist/admin?q={quote_plus(lead.email)}"
    approve_url = f"{api_base}/v1/leads/{lead.id}/approve-link?token={quote_plus(approve_token)}"

    p = profile or {}
    lines = [
        f"New waitlist lead submitted.",
        f"",
        f"Lead ID: {lead.id}",
        f"Email: {lead.email}",
        f"Source: {lead.source or 'waitlist'}",
        f"Campaign: {lead.utm_campaign or '-'}",
        f"",
        f"Name: {p.get('full_name', '')}",
        f"Company: {p.get('company', '')}",
        f"Role: {p.get('role', '')}",
        f"Use case: {p.get('use_case', '')}",
        f"Timeline: {p.get('timeline', '')}",
        f"",
        f"Approve instantly: {approve_url}",
        f"Open admin: {admin_url}",
    ]

    msg = EmailMessage()
    msg['Subject'] = f"[DO Waitlist] New lead: {lead.email}"
    msg['From'] = smtp_from
    msg['To'] = to_email
    msg.set_content('\n'.join(lines))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)


def _send_waitlist_approved_email(lead: Lead) -> None:
    smtp_host = (os.getenv('SMTP_HOST') or '').strip()
    smtp_user = (os.getenv('SMTP_USER') or '').strip()
    smtp_pass = (os.getenv('SMTP_PASS') or '').strip()
    smtp_from = (os.getenv('SMTP_FROM') or smtp_user or '').strip()
    smtp_port = int((os.getenv('SMTP_PORT') or '587').strip() or '587')
    web_base = (os.getenv('WEB_APP_BASE') or 'http://127.0.0.1:3000').rstrip('/')

    if not (smtp_host and smtp_from and smtp_user and smtp_pass and lead.email):
        return

    msg = EmailMessage()
    msg['Subject'] = 'You’re approved for DemandOrchestrator early access'
    msg['From'] = smtp_from
    msg['To'] = lead.email
    msg.set_content('\n'.join([
        'You’re in — your early access is approved.',
        '',
        'Next steps:',
        f'1) Open {web_base}/login',
        '2) Enter this email address',
        '3) Use the magic link to enter Studio',
        '',
        'If login fails, reply to this email and we will fix it immediately.'
    ]))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)


def _log_lead_event(session: Session, lead_id: int, event_type: str, metadata: Optional[dict] = None):
    evt = LeadActivityEvent(
        lead_id=lead_id,
        event_type=event_type,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
    )
    session.add(evt)


def sync_campaign_status(session: Session, campaign_id: int):
    c = session.get(Campaign, campaign_id)
    if not c:
        return None

    assets = session.exec(select(Asset).where(Asset.campaign_id == campaign_id)).all()
    total = len(assets)
    approved = sum(1 for a in assets if a.status == 'approved')
    reviewed = sum(1 for a in assets if a.status in ('approved', 'rejected'))

    if total > 0 and approved == total:
        c.status = 'ready'
    elif reviewed > 0:
        c.status = 'reviewed'
    else:
        c.status = 'generated'

    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@router.get('/health')
def health():
    return {'status': 'ok', 'service': 'demandorchestrator-api'}


@router.get('/v1/ping')
def ping():
    return {'pong': True}


@router.get('/v1/campaigns')
def list_campaigns(session: Session = Depends(get_session), limit: int = 20):
    rows = session.exec(select(Campaign).order_by(Campaign.id.desc()).limit(limit)).all()
    return [
        {
            'id': c.id,
            'workspace_id': c.workspace_id,
            'objective': c.objective,
            'source_type': c.source_type,
            'status': c.status,
            'created_at': c.created_at.isoformat(),
        }
        for c in rows
    ]


@router.post('/v1/campaigns', response_model=CampaignOut)
def create_campaign(payload: CreateCampaignRequest, session: Session = Depends(get_session)):
    c = Campaign(
        workspace_id=payload.workspace_id,
        objective=payload.objective,
        source_type=payload.source_type,
        source_input=payload.source_input,
        status='generated',
    )
    session.add(c)
    session.commit()
    session.refresh(c)

    assets = generate_seed_assets(c.id, payload.source_input)
    for a in assets:
        session.add(a)
    session.commit()

    db_assets = session.exec(select(Asset).where(Asset.campaign_id == c.id)).all()
    return CampaignOut(
        id=c.id,
        workspace_id=c.workspace_id,
        objective=c.objective,
        source_type=c.source_type,
        source_input=c.source_input,
        status=c.status,
        assets=[AssetOut(id=a.id, asset_type=a.asset_type, channel=a.channel, content=a.content, score=a.score, status=a.status) for a in db_assets],
    )


@router.get('/v1/campaigns/{campaign_id}', response_model=CampaignOut)
def get_campaign(campaign_id: int, session: Session = Depends(get_session)):
    c = session.get(Campaign, campaign_id)
    if not c:
        raise HTTPException(status_code=404, detail='campaign not found')
    db_assets = session.exec(select(Asset).where(Asset.campaign_id == c.id)).all()
    return CampaignOut(
        id=c.id,
        workspace_id=c.workspace_id,
        objective=c.objective,
        source_type=c.source_type,
        source_input=c.source_input,
        status=c.status,
        assets=[AssetOut(id=a.id, asset_type=a.asset_type, channel=a.channel, content=a.content, score=a.score, status=a.status) for a in db_assets],
    )


@router.post('/v1/assets/{asset_id}/approve')
def approve_asset(asset_id: int, payload: AssetActionRequest, session: Session = Depends(get_session)):
    a = session.get(Asset, asset_id)
    if not a:
        raise HTTPException(status_code=404, detail='asset not found')
    a.status = 'approved'
    session.add(ApprovalEvent(asset_id=asset_id, action='approve', note=payload.note or ''))
    session.add(a)
    session.commit()
    c = sync_campaign_status(session, a.campaign_id)
    return {'ok': True, 'asset_id': asset_id, 'status': a.status, 'campaign_status': c.status if c else None}


@router.post('/v1/assets/{asset_id}/reject')
def reject_asset(asset_id: int, payload: AssetActionRequest, session: Session = Depends(get_session)):
    a = session.get(Asset, asset_id)
    if not a:
        raise HTTPException(status_code=404, detail='asset not found')
    a.status = 'rejected'
    session.add(ApprovalEvent(asset_id=asset_id, action='reject', note=payload.note or ''))
    session.add(a)
    session.commit()
    c = sync_campaign_status(session, a.campaign_id)
    return {'ok': True, 'asset_id': asset_id, 'status': a.status, 'campaign_status': c.status if c else None}


@router.post('/v1/assets/{asset_id}/regenerate')
def regenerate_asset(asset_id: int, payload: AssetActionRequest, session: Session = Depends(get_session)):
    a = session.get(Asset, asset_id)
    if not a:
        raise HTTPException(status_code=404, detail='asset not found')

    regenerate_asset_content(a, guidance=payload.note or '')
    session.add(a)
    session.commit()
    c = sync_campaign_status(session, a.campaign_id)
    return {'ok': True, 'asset_id': a.id, 'status': a.status, 'score': a.score, 'campaign_status': c.status if c else None}


@router.post('/v1/campaigns/{campaign_id}/status/{new_status}')
def set_campaign_status(campaign_id: int, new_status: str, session: Session = Depends(get_session)):
    c = session.get(Campaign, campaign_id)
    if not c:
        raise HTTPException(status_code=404, detail='campaign not found')

    allowed = {'generated', 'reviewed', 'ready'}
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f'invalid status: {new_status}')

    order = {'generated': 1, 'reviewed': 2, 'ready': 3}
    if order[new_status] < order.get(c.status, 1):
        raise HTTPException(status_code=400, detail='status regression not allowed')

    c.status = new_status
    session.add(c)
    session.commit()
    session.refresh(c)
    return {'ok': True, 'campaign_id': c.id, 'status': c.status}


@router.post('/v1/leads', response_model=LeadOut)
def create_lead(payload: LeadCreateRequest, session: Session = Depends(get_session)):
    email = payload.email.strip().lower()
    source = (payload.source or 'waitlist').strip()
    utm_campaign = (payload.utm_campaign or '').strip()

    existing = session.exec(
        select(Lead).where(
            Lead.email == email,
            Lead.source == source,
            Lead.utm_campaign == utm_campaign,
        ).order_by(Lead.id.desc())
    ).first()

    if existing:
        _log_lead_event(
            session,
            existing.id,
            'duplicate_blocked',
            {'email': email, 'source': source, 'utm_campaign': utm_campaign},
        )
        session.commit()
        return LeadOut(id=existing.id, email=existing.email, source=existing.source, status=existing.status)

    lead = Lead(
        email=email,
        source=source,
        status='new',
        utm_source=(payload.utm_source or '').strip(),
        utm_medium=(payload.utm_medium or '').strip(),
        utm_campaign=utm_campaign,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    profile_data = payload.profile or {}
    _log_lead_event(
        session,
        lead.id,
        'created',
        {
            'source': lead.source,
            'utm_source': lead.utm_source,
            'utm_medium': lead.utm_medium,
            'utm_campaign': lead.utm_campaign,
            'profile': profile_data,
        },
    )
    session.commit()

    try:
        _send_waitlist_alert_email(lead, profile=profile_data)
    except Exception as e:
        _log_lead_event(session, lead.id, 'alert_email_failed', {'error': str(e)[:300]})
        session.commit()

    return LeadOut(id=lead.id, email=lead.email, source=lead.source, status=lead.status)


@router.patch('/v1/leads/{lead_id}/status')
def update_lead_status(lead_id: int, payload: LeadStatusUpdateRequest, session: Session = Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='lead not found')

    allowed = {'new', 'not_contacted', 'contacted', 'replied', 'qualified', 'closed'}
    status = (payload.status or '').strip().lower()
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f'invalid status: {status}')

    prev = lead.status
    lead.status = status
    session.add(lead)
    _log_lead_event(session, lead.id, 'status_changed', {'from': prev, 'to': status})
    session.commit()

    if status == 'qualified' and prev != 'qualified':
      try:
          _send_waitlist_approved_email(lead)
          _log_lead_event(session, lead.id, 'approval_email_sent', {})
      except Exception as e:
          _log_lead_event(session, lead.id, 'approval_email_failed', {'error': str(e)[:300]})
      session.commit()

    session.refresh(lead)
    return {'id': lead.id, 'status': lead.status}


@router.get('/v1/leads/{lead_id}/approve-link')
def approve_lead_link(
    lead_id: int,
    token: str = Query(default=''),
    status: str = Query(default='qualified'),
    session: Session = Depends(get_session),
):
    expected = (os.getenv('WAITLIST_APPROVAL_TOKEN') or '').strip()
    if not expected or token.strip() != expected:
        raise HTTPException(status_code=403, detail='invalid approval token')

    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='lead not found')

    allowed = {'new', 'not_contacted', 'contacted', 'replied', 'qualified', 'closed'}
    new_status = (status or 'qualified').strip().lower()
    if new_status not in allowed:
        new_status = 'qualified'

    prev = lead.status
    lead.status = new_status
    session.add(lead)
    _log_lead_event(session, lead.id, 'approved_via_email_link', {'from': prev, 'to': new_status})
    session.commit()

    if new_status == 'qualified' and prev != 'qualified':
        try:
            _send_waitlist_approved_email(lead)
            _log_lead_event(session, lead.id, 'approval_email_sent', {'via': 'approve_link'})
        except Exception as e:
            _log_lead_event(session, lead.id, 'approval_email_failed', {'via': 'approve_link', 'error': str(e)[:300]})
        session.commit()

    web_base = (os.getenv('WEB_APP_BASE') or 'http://127.0.0.1:3000').rstrip('/')
    return RedirectResponse(url=f"{web_base}/waitlist/admin?q={quote_plus(lead.email)}")


@router.get('/v1/leads')
def list_leads(
    source: str = '',
    campaign: str = '',
    status: str = '',
    q: str = '',
    dedupe: bool = False,
    include_tests: bool = False,
    sort: str = 'newest',
    limit: int = 100,
    session: Session = Depends(get_session),
):
    rows = session.exec(select(Lead).limit(max(1, min(limit, 500)))).all()

    def is_test_email(email: str) -> bool:
        e = (email or '').strip().lower()
        return e.startswith('qa+') or e.startswith('test@') or e.endswith('@example.com')

    q_norm = (q or '').strip().lower()
    out = []
    seen = set()
    for l in rows:
        if not include_tests and is_test_email(l.email):
            continue
        if source and (l.source or '') != source:
            continue
        if campaign and (l.utm_campaign or '') != campaign:
            continue
        if status and (l.status or '') != status:
            continue
        if q_norm:
            hay = ' '.join([
                (l.email or '').lower(),
                (l.source or '').lower(),
                (l.utm_campaign or '').lower(),
                (l.utm_source or '').lower(),
                (l.utm_medium or '').lower(),
            ])
            if q_norm not in hay:
                continue

        if dedupe:
            dedupe_key = ((l.email or '').strip().lower(), (l.source or '').strip(), (l.utm_campaign or '').strip())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

        out.append({
            'id': l.id,
            'email': l.email,
            'source': l.source,
            'status': l.status,
            'utm_source': l.utm_source,
            'utm_medium': l.utm_medium,
            'utm_campaign': l.utm_campaign,
            'created_at': l.created_at.isoformat(),
        })

    if sort == 'oldest':
        out.sort(key=lambda x: x['id'])
    else:
        out.sort(key=lambda x: x['id'], reverse=True)

    return out[: max(1, min(limit, 500))]


@router.get('/v1/leads/activity')
def list_lead_activity(
    lead_id: Optional[int] = None,
    event_type: str = '',
    limit: int = 200,
    session: Session = Depends(get_session),
):
    rows = session.exec(select(LeadActivityEvent).order_by(LeadActivityEvent.id.desc()).limit(max(1, min(limit, 1000)))).all()
    out = []
    for r in rows:
        if lead_id is not None and r.lead_id != lead_id:
            continue
        if event_type and r.event_type != event_type:
            continue
        try:
            meta = json.loads(r.metadata_json or '{}')
        except Exception:
            meta = {}
        out.append({
            'id': r.id,
            'lead_id': r.lead_id,
            'event_type': r.event_type,
            'metadata': meta,
            'created_at': r.created_at.isoformat(),
        })
    return out


@router.get('/v1/leads/export.csv', response_class=PlainTextResponse)
def export_leads_csv(
    source: str = '',
    campaign: str = '',
    include_tests: bool = False,
    limit: int = 1000,
    session: Session = Depends(get_session),
):
    rows = list_leads(source=source, campaign=campaign, include_tests=include_tests, limit=limit, session=session)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=['id', 'email', 'source', 'utm_source', 'utm_medium', 'utm_campaign', 'status', 'created_at'])
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, '') for k in writer.fieldnames})
    return PlainTextResponse(
        content=buf.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="demandorchestrator-leads.csv"'},
    )


@router.post('/v1/leads/reset')
def reset_leads(
    token: str = Query(default=''),
    session: Session = Depends(get_session),
):
    expected = (os.getenv('WAITLIST_APPROVAL_TOKEN') or '').strip()
    if not expected or token.strip() != expected:
        raise HTTPException(status_code=403, detail='invalid reset token')

    leads = session.exec(select(Lead)).all()
    lead_ids = [l.id for l in leads]

    events = session.exec(select(LeadActivityEvent)).all()
    deleted_events = 0
    for e in events:
        if e.lead_id in lead_ids:
            session.delete(e)
            deleted_events += 1

    deleted_leads = 0
    for l in leads:
        session.delete(l)
        deleted_leads += 1

    session.commit()
    return {'ok': True, 'deleted_leads': deleted_leads, 'deleted_activity_events': deleted_events}


@router.get('/v1/leads/stats')
def lead_stats(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()

    def is_test_email(email: str) -> bool:
        e = (email or '').strip().lower()
        return e.startswith('qa+') or e.startswith('test@') or e.endswith('@example.com')

    production_leads = [l for l in leads if not is_test_email(l.email)]
    total = len(production_leads)

    today = datetime.now(timezone.utc).date()
    today_count = sum(1 for l in production_leads if l.created_at.date() == today)

    source_counts: dict[str, int] = {}
    campaign_counts: dict[str, int] = {}
    for l in production_leads:
        source_key = (l.source or 'unknown').strip() or 'unknown'
        source_counts[source_key] = source_counts.get(source_key, 0) + 1

        campaign_key = (l.utm_campaign or 'unknown').strip() or 'unknown'
        campaign_counts[campaign_key] = campaign_counts.get(campaign_key, 0) + 1

    top_sources = [
        {'source': k, 'count': v}
        for k, v in sorted(source_counts.items(), key=lambda kv: kv[1], reverse=True)
    ]
    top_campaigns = [
        {'campaign': k, 'count': v}
        for k, v in sorted(campaign_counts.items(), key=lambda kv: kv[1], reverse=True)
    ]

    return {
        'total': total,
        'today': today_count,
        'sources': top_sources,
        'campaigns': top_campaigns,
        'excluded_test_leads': len(leads) - len(production_leads),
    }

from __future__ import annotations

import json
from datetime import datetime, timedelta, date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models.analytics import ContentPerformanceEvent, ContentDailyMetric
from app.models.mvp import MVPContentItem

router = APIRouter(prefix='/analytics', tags=['analytics'])


class IngestEventRequest(BaseModel):
    workspaceId: str
    contentItemId: str
    scheduleId: str = ''
    channel: str = 'x'
    eventType: str = Field(default='impression')
    value: float = 1.0
    occurredAt: datetime | None = None
    metadata: dict = Field(default_factory=dict)


def _event_key(event_type: str) -> str:
    e = (event_type or '').strip().lower()
    if e in {'impression', 'engagement', 'click', 'lead', 'publish_succeeded', 'publish_failed'}:
        return e
    raise HTTPException(status_code=400, detail='unsupported eventType')


@router.post('/events')
def ingest_event(payload: IngestEventRequest, session: Session = Depends(get_session)):
    content = session.get(MVPContentItem, payload.contentItemId)
    if not content or content.workspace_id != payload.workspaceId:
        raise HTTPException(status_code=404, detail='content item not found')

    evt_type = _event_key(payload.eventType)
    when = payload.occurredAt or datetime.utcnow()

    evt = ContentPerformanceEvent(
        id=f'cpe_{uuid4().hex[:14]}',
        workspace_id=payload.workspaceId,
        content_item_id=payload.contentItemId,
        schedule_id=(payload.scheduleId or '').strip(),
        channel=(payload.channel or content.channel or 'x').strip().lower(),
        event_type=evt_type,
        value=float(payload.value or 1.0),
        metadata_json=json.dumps(payload.metadata or {}),
        occurred_at=when,
        created_at=datetime.utcnow(),
    )
    session.add(evt)
    session.commit()
    return {'ok': True, 'id': evt.id}


@router.post('/rollups/rebuild')
def rebuild_rollups(
    workspaceId: str,
    days: int = Query(default=30, ge=1, le=365),
    session: Session = Depends(get_session),
):
    since = datetime.utcnow() - timedelta(days=days)
    events = session.exec(
        select(ContentPerformanceEvent)
        .where(ContentPerformanceEvent.workspace_id == workspaceId, ContentPerformanceEvent.occurred_at >= since)
        .order_by(ContentPerformanceEvent.occurred_at.asc())
    ).all()

    # Drop existing rows for rebuild window
    metric_rows = session.exec(
        select(ContentDailyMetric).where(ContentDailyMetric.workspace_id == workspaceId)
    ).all()
    cutoff_date = since.date()
    for m in metric_rows:
        if m.metric_date >= cutoff_date:
            session.delete(m)
    session.commit()

    agg: dict[tuple[str, date, str], ContentDailyMetric] = {}

    for e in events:
        d = e.occurred_at.date()
        key = (e.content_item_id, d, e.channel)
        row = agg.get(key)
        if not row:
            row = ContentDailyMetric(
                id=f'cdm_{uuid4().hex[:14]}',
                workspace_id=workspaceId,
                content_item_id=e.content_item_id,
                metric_date=d,
                channel=e.channel,
                updated_at=datetime.utcnow(),
            )
            agg[key] = row

        val = int(max(0, round(e.value or 1)))
        if e.event_type == 'impression':
            row.impressions += val
        elif e.event_type == 'engagement':
            row.engagements += val
        elif e.event_type == 'click':
            row.clicks += val
        elif e.event_type == 'lead':
            row.leads += val
        elif e.event_type == 'publish_succeeded':
            row.publish_succeeded += val
        elif e.event_type == 'publish_failed':
            row.publish_failed += val
        row.updated_at = datetime.utcnow()

    for row in agg.values():
        session.add(row)
    session.commit()

    return {'ok': True, 'rows': len(agg), 'events': len(events), 'since': since.isoformat()}


@router.get('/summary')
def analytics_summary(
    workspaceId: str,
    days: int = Query(default=30, ge=1, le=365),
    session: Session = Depends(get_session),
):
    since = (datetime.utcnow() - timedelta(days=days)).date()
    rows = session.exec(
        select(ContentDailyMetric)
        .where(ContentDailyMetric.workspace_id == workspaceId, ContentDailyMetric.metric_date >= since)
    ).all()

    totals = {
        'impressions': 0,
        'engagements': 0,
        'clicks': 0,
        'leads': 0,
        'publishSucceeded': 0,
        'publishFailed': 0,
    }
    by_content: dict[str, dict] = {}
    for r in rows:
        totals['impressions'] += int(r.impressions or 0)
        totals['engagements'] += int(r.engagements or 0)
        totals['clicks'] += int(r.clicks or 0)
        totals['leads'] += int(r.leads or 0)
        totals['publishSucceeded'] += int(r.publish_succeeded or 0)
        totals['publishFailed'] += int(r.publish_failed or 0)

        c = by_content.setdefault(r.content_item_id, {
            'contentItemId': r.content_item_id,
            'impressions': 0,
            'engagements': 0,
            'clicks': 0,
            'leads': 0,
        })
        c['impressions'] += int(r.impressions or 0)
        c['engagements'] += int(r.engagements or 0)
        c['clicks'] += int(r.clicks or 0)
        c['leads'] += int(r.leads or 0)

    top = sorted(by_content.values(), key=lambda x: (x['leads'], x['clicks'], x['engagements'], x['impressions']), reverse=True)[:5]

    engagement_rate = 0.0
    if totals['impressions'] > 0:
        engagement_rate = round((totals['engagements'] / totals['impressions']) * 100.0, 2)

    return {
        'workspaceId': workspaceId,
        'windowDays': days,
        'totals': totals,
        'engagementRatePct': engagement_rate,
        'topContent': top,
    }

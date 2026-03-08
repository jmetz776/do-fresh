from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models.repurpose import RepurposeJob, RepurposeVariant, RepurposeQualityEvent

router = APIRouter(prefix='/v1/repurpose', tags=['repurpose'])


class TargetRequest(BaseModel):
    channel: str
    formats: list[str] = []


class SourceRequest(BaseModel):
    type: str = 'idea'
    title: str = ''
    body: str = ''


class IntentRequest(BaseModel):
    goal: str = 'awareness'
    audience: str = ''
    cta: str = ''


class CreateRepurposeJobRequest(BaseModel):
    workspaceId: str = 'default'
    source: SourceRequest
    intent: IntentRequest
    targets: list[TargetRequest] = []
    constraints: dict[str, Any] = {}


class RegenerateVariantRequest(BaseModel):
    guidance: str = ''


class ApproveRequest(BaseModel):
    variantIds: list[str] = []


def _score_stub(body: str) -> dict[str, float]:
    base = 0.82 if body.strip() else 0.0
    return {
        'overall': base,
        'brandFit': max(0.0, base - 0.02),
        'clarity': max(0.0, base - 0.01),
        'originality': max(0.0, base - 0.05),
        'compliance': 0.97 if body.strip() else 0.0,
    }


@router.post('/jobs')
def create_job(payload: CreateRepurposeJobRequest, session: Session = Depends(get_session)):
    if not payload.targets:
        raise HTTPException(status_code=400, detail='at least one target required')

    job_id = str(uuid4())
    threshold = float(payload.constraints.get('qualityThreshold', 0.78))

    job = RepurposeJob(
        id=job_id,
        workspace_id=payload.workspaceId,
        source_type=payload.source.type,
        source_title=payload.source.title,
        source_body=payload.source.body,
        intent_goal=payload.intent.goal,
        intent_audience=payload.intent.audience,
        status='running',
        quality_gate_threshold=threshold,
        updated_at=datetime.utcnow(),
    )
    session.add(job)
    session.commit()

    generated = 0
    failed_ids: list[str] = []
    for t in payload.targets:
        for f in t.formats:
            vid = str(uuid4())
            body = f"{payload.source.title}\n\n{payload.source.body}".strip() or 'Repurpose draft pending.'
            scores = _score_stub(body)
            status = 'draft' if (scores['overall'] >= threshold and scores['compliance'] >= 0.95) else 'needs_review'
            if status != 'draft':
                failed_ids.append(vid)
            v = RepurposeVariant(
                id=vid,
                job_id=job_id,
                workspace_id=payload.workspaceId,
                channel=t.channel,
                format=f,
                title=f"{t.channel.upper()} · {f}",
                body=body,
                cta=payload.intent.cta,
                payload_json=json.dumps({'sourceType': payload.source.type}),
                quality_overall=scores['overall'],
                quality_brand_fit=scores['brandFit'],
                quality_clarity=scores['clarity'],
                quality_originality=scores['originality'],
                quality_compliance=scores['compliance'],
                status=status,
                flags_json=json.dumps(['quality_gate_warning'] if status == 'needs_review' else []),
                updated_at=datetime.utcnow(),
            )
            session.add(v)
            session.add(
                RepurposeQualityEvent(
                    workspace_id=payload.workspaceId,
                    job_id=job_id,
                    variant_id=vid,
                    event_type='scored',
                    metadata_json=json.dumps(scores),
                )
            )
            generated += 1

    job.status = 'succeeded' if not failed_ids else 'partial'
    job.quality_gate_passed = len(failed_ids) == 0
    job.errors_json = json.dumps([] if not failed_ids else ['some_variants_failed_quality_gate'])
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()

    return {'jobId': job.id, 'status': job.status, 'variantsGenerated': generated, 'qualityGatePassed': job.quality_gate_passed}


@router.get('/jobs/{job_id}')
def get_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(RepurposeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail='job not found')

    variants = session.exec(
        select(RepurposeVariant)
        .where(RepurposeVariant.job_id == job_id)
        .order_by(RepurposeVariant.created_at.asc())
    ).all()

    return {
        'job': {
            'id': job.id,
            'workspaceId': job.workspace_id,
            'status': job.status,
            'qualityGatePassed': job.quality_gate_passed,
            'qualityGateThreshold': job.quality_gate_threshold,
            'createdAt': job.created_at.isoformat(),
            'updatedAt': job.updated_at.isoformat(),
        },
        'variants': [
            {
                'id': v.id,
                'channel': v.channel,
                'format': v.format,
                'title': v.title,
                'body': v.body,
                'cta': v.cta,
                'status': v.status,
                'quality': {
                    'overall': v.quality_overall,
                    'brandFit': v.quality_brand_fit,
                    'clarity': v.quality_clarity,
                    'originality': v.quality_originality,
                    'compliance': v.quality_compliance,
                },
                'flags': json.loads(v.flags_json or '[]'),
            }
            for v in variants
        ],
    }


@router.post('/jobs/{job_id}/regenerate-variant/{variant_id}')
def regenerate_variant(job_id: str, variant_id: str, payload: RegenerateVariantRequest, session: Session = Depends(get_session)):
    v = session.get(RepurposeVariant, variant_id)
    if not v or v.job_id != job_id:
        raise HTTPException(status_code=404, detail='variant not found')

    v.body = (v.body + '\n\n' + payload.guidance).strip()[:5000]
    scores = _score_stub(v.body)
    v.quality_overall = scores['overall']
    v.quality_brand_fit = scores['brandFit']
    v.quality_clarity = scores['clarity']
    v.quality_originality = scores['originality']
    v.quality_compliance = scores['compliance']
    v.status = 'draft' if scores['overall'] >= 0.78 and scores['compliance'] >= 0.95 else 'needs_review'
    v.flags_json = json.dumps([] if v.status == 'draft' else ['quality_gate_warning'])
    v.updated_at = datetime.utcnow()
    session.add(v)
    session.add(
        RepurposeQualityEvent(
            workspace_id=v.workspace_id,
            job_id=job_id,
            variant_id=variant_id,
            event_type='regenerated',
            metadata_json=json.dumps({'guidance': payload.guidance[:180]}),
        )
    )
    session.commit()

    return {'ok': True, 'variantId': v.id, 'status': v.status}


@router.post('/jobs/{job_id}/approve')
def approve_variants(job_id: str, payload: ApproveRequest, session: Session = Depends(get_session)):
    if not payload.variantIds:
        raise HTTPException(status_code=400, detail='variantIds required')

    approved = 0
    for variant_id in payload.variantIds:
        v = session.get(RepurposeVariant, variant_id)
        if not v or v.job_id != job_id:
            continue
        v.status = 'approved'
        v.updated_at = datetime.utcnow()
        session.add(v)
        session.add(
            RepurposeQualityEvent(
                workspace_id=v.workspace_id,
                job_id=job_id,
                variant_id=variant_id,
                event_type='approved',
                metadata_json='{}',
            )
        )
        approved += 1

    session.commit()
    return {'ok': True, 'approved': approved}


@router.get('/jobs')
def list_jobs(
    workspaceId: str = Query(default='default'),
    limit: int = Query(default=20, ge=1, le=200),
    status: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(RepurposeJob)
        .where(RepurposeJob.workspace_id == workspaceId)
        .order_by(RepurposeJob.created_at.desc())
        .limit(limit)
    ).all()

    out = []
    for r in rows:
        if status and r.status != status:
            continue
        out.append(
            {
                'id': r.id,
                'status': r.status,
                'sourceType': r.source_type,
                'intentGoal': r.intent_goal,
                'qualityGatePassed': r.quality_gate_passed,
                'createdAt': r.created_at.isoformat(),
                'updatedAt': r.updated_at.isoformat(),
            }
        )
    return {'items': out}

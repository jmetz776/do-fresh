from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models.consent import VoiceProfile, ConsentRecord, VoiceRenderJob
from app.services.elevenlabs_client import ElevenLabsClient

router = APIRouter(prefix='/v1/voice', tags=['voice'])

DATA_ROOT = Path(os.getenv('DO_DATA_ROOT', './data')).resolve()
AUDIO_DIR = Path(os.getenv('DO_AUDIO_ROOT', str(DATA_ROOT / 'audio' / 'renders'))).resolve()
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class CreateVoiceRenderRequest(BaseModel):
    workspaceId: str = 'default'
    voiceProfileId: str
    scriptText: str


def _estimate_cost(text: str) -> float:
    return round((max(1, len(text)) / 1000.0) * 0.18, 4)


@router.post('/render-jobs')
def create_voice_render_job(payload: CreateVoiceRenderRequest, session: Session = Depends(get_session)):
    vp = session.get(VoiceProfile, payload.voiceProfileId)
    if not vp:
        raise HTTPException(status_code=404, detail='voice profile not found')
    if vp.workspace_id != payload.workspaceId:
        raise HTTPException(status_code=400, detail='workspace mismatch')
    if vp.status != 'active':
        raise HTTPException(status_code=400, detail='voice profile not active')

    rec = session.get(ConsentRecord, vp.consent_record_id)
    if not rec or rec.status != 'signed':
        raise HTTPException(status_code=400, detail='active consent required')

    job = VoiceRenderJob(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        voice_profile_id=vp.id,
        script_text=payload.scriptText.strip(),
        provider='elevenlabs',
        status='queued',
        estimated_cost_usd=_estimate_cost(payload.scriptText),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(job)
    session.commit()

    client = ElevenLabsClient()
    if not client.configured():
        job.status = 'failed'
        job.error = 'ELEVENLABS_API_KEY missing'
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()
        raise HTTPException(status_code=400, detail='ELEVENLABS_API_KEY missing')

    try:
        audio = client.text_to_speech(vp.provider_voice_id, payload.scriptText)
        out = AUDIO_DIR / f'{job.id}.mp3'
        out.write_bytes(audio)
        job.audio_uri = str(out)
        job.status = 'succeeded'
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()
    except RuntimeError as e:
        job.status = 'failed'
        job.error = str(e)
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()
        raise HTTPException(status_code=502, detail=str(e))

    return {
        'id': job.id,
        'status': job.status,
        'audioUri': job.audio_uri,
        'estimatedCostUsd': job.estimated_cost_usd,
    }


@router.get('/render-jobs')
def list_voice_render_jobs(
    workspaceId: str = Query(default='default'),
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(VoiceRenderJob)
        .where(VoiceRenderJob.workspace_id == workspaceId)
        .order_by(VoiceRenderJob.created_at.desc())
        .limit(limit)
    ).all()
    return {
        'items': [
            {
                'id': r.id,
                'voiceProfileId': r.voice_profile_id,
                'status': r.status,
                'audioUri': r.audio_uri,
                'estimatedCostUsd': r.estimated_cost_usd,
                'createdAt': r.created_at.isoformat(),
                'error': r.error,
            }
            for r in rows
        ]
    }


@router.post('/render-jobs/{job_id}/approve')
def approve_voice_render_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(VoiceRenderJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail='voice render job not found')
    if job.status != 'succeeded':
        raise HTTPException(status_code=400, detail='only succeeded jobs can be approved')
    job.status = 'approved'
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    return {'ok': True, 'id': job.id, 'status': job.status}

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from app.db import get_session
from app.models.consent import (
    ConsentRecord,
    IdentityVerification,
    VoiceProfile,
    AvatarProfile,
    VoiceRenderJob,
    VideoRenderJob,
    VideoRenderBackground,
)
from app.models.auth import WorkspaceSetting
from app.services.elevenlabs_client import ElevenLabsClient
from app.services.heygen_client import HeyGenClient
from app.services.model_registry import pick_model_with_policy

router = APIRouter(prefix='/v1/consent', tags=['consent'])


class CreateConsentRequest(BaseModel):
    workspaceId: str = 'default'
    subjectFullName: str
    subjectEmail: EmailStr
    consentType: str = 'both'  # voice|likeness|both
    scope: dict = {}
    evidenceUri: str = ''


class VerifyIdentityRequest(BaseModel):
    provider: str = 'manual'
    status: str = 'verified'  # pending|verified|failed
    score: float = 1.0
    metadata: dict = {}


class RevokeConsentRequest(BaseModel):
    reason: str = 'revoked_by_subject'


class CreateVoiceProfileRequest(BaseModel):
    workspaceId: str = 'default'
    consentRecordId: str
    provider: str = 'elevenlabs'
    providerVoiceId: str = ''
    displayName: str = 'Custom Voice'


class CreateAvatarProfileRequest(BaseModel):
    workspaceId: str = 'default'
    consentRecordId: str
    provider: str = 'heygen'
    providerAvatarId: str = ''
    displayName: str = 'Custom Avatar'


class CreateHeyGenAvatarRequest(BaseModel):
    workspaceId: str = 'default'
    fullName: str
    email: EmailStr
    avatarName: str
    trainingFootageUrl: str
    consentVideoUrl: str


class CreateVoiceRenderRequest(BaseModel):
    workspaceId: str = 'default'
    voiceProfileId: str
    scriptText: str


class CreateVideoRenderRequest(BaseModel):
    workspaceId: str = 'default'
    voiceRenderId: str
    scriptText: str = ''
    backgroundTemplateId: str = ''


class FacelessRenderTopRequest(BaseModel):
    workspaceId: str = 'default'
    scripts: list[str] = []
    topN: int = 3
    selectedBackgroundTemplateId: str = ''


DATA_ROOT = Path(os.getenv('DO_DATA_ROOT', './data')).resolve()
AUDIO_ROOT = Path(os.getenv('DO_AUDIO_ROOT', str(DATA_ROOT / 'audio' / 'renders'))).resolve()
VIDEO_ROOT = Path(os.getenv('DO_VIDEO_ROOT', str(DATA_ROOT / 'video' / 'renders'))).resolve()
BACKGROUND_TEMPLATES_FILE = Path(__file__).resolve().parents[1] / 'config' / 'background_templates.json'


def _estimate_voice_cost_usd(script: str) -> float:
    chars = max(1, len(script or ''))
    return round((chars / 1000.0) * 0.18, 4)


def _estimate_video_cost_usd(script: str) -> float:
    chars = max(1, len(script or ''))
    # Stub baseline for planning until provider billing is integrated.
    return round((chars / 1000.0) * 1.8, 4)


def _workspace_avatar_limit(session: Session, workspace_id: str) -> int:
    row = session.exec(
        select(WorkspaceSetting).where(
            WorkspaceSetting.workspace_id == workspace_id,
            WorkspaceSetting.key == 'account.type',
        )
    ).first()
    acct = 'personal'
    if row and row.value_json:
        try:
            acct = str(json.loads(row.value_json) or 'personal').strip().lower()
        except Exception:
            acct = 'personal'
    return 10 if acct == 'corporate' else 3


def _workspace_video_limits(session: Session, workspace_id: str) -> dict:
    # v1 policy: simple plan-based caps.
    # starter/personal: 10/mo, 1 concurrent
    # pro/corporate: 40/mo, 2 concurrent
    # top_tier: 150/mo, 5 concurrent
    plan = 'starter'
    acct = 'personal'

    acct_row = session.exec(
        select(WorkspaceSetting).where(
            WorkspaceSetting.workspace_id == workspace_id,
            WorkspaceSetting.key == 'account.type',
        )
    ).first()
    if acct_row and acct_row.value_json:
        try:
            acct = str(json.loads(acct_row.value_json) or 'personal').strip().lower()
        except Exception:
            acct = 'personal'

    tier_row = session.exec(
        select(WorkspaceSetting).where(
            WorkspaceSetting.workspace_id == workspace_id,
            WorkspaceSetting.key == 'plan.tier',
        )
    ).first()
    if tier_row and tier_row.value_json:
        try:
            plan = str(json.loads(tier_row.value_json) or 'starter').strip().lower()
        except Exception:
            plan = 'starter'
    elif acct == 'corporate':
        plan = 'pro'

    if plan in ('top', 'top_tier', 'enterprise'):
        return {'plan': 'top_tier', 'monthly_video_cap': 150, 'concurrency_cap': 5}
    if plan in ('pro', 'corporate'):
        return {'plan': 'pro', 'monthly_video_cap': 40, 'concurrency_cap': 2}
    return {'plan': 'starter', 'monthly_video_cap': 10, 'concurrency_cap': 1}


def _workspace_video_usage(session: Session, workspace_id: str) -> dict:
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    rows = session.exec(
        select(VideoRenderJob).where(VideoRenderJob.workspace_id == workspace_id)
    ).all()

    monthly_count = sum(1 for r in rows if (r.created_at and r.created_at >= month_start))
    active_count = sum(1 for r in rows if (r.status or '').lower() in ('queued', 'processing', 'rendering'))
    return {'monthly_count': monthly_count, 'active_count': active_count, 'month_start': month_start.isoformat()}


def _video_queue_timeout_seconds() -> int:
    try:
        return max(120, int((os.getenv('DO_VIDEO_QUEUE_TIMEOUT_SECONDS') or '600').strip()))
    except Exception:
        return 600


def _apply_queue_timeout(row: VideoRenderJob, session: Session) -> bool:
    if (row.status or '').lower() not in ('queued', 'processing', 'rendering'):
        return False
    base_ts = row.updated_at or row.created_at or datetime.utcnow()
    age_sec = (datetime.utcnow() - base_ts).total_seconds()
    if age_sec < _video_queue_timeout_seconds():
        return False
    row.status = 'failed'
    row.error = f'provider_delayed_timeout_after_{int(age_sec)}s'
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    return True


def _load_background_templates() -> list[dict]:
    if not BACKGROUND_TEMPLATES_FILE.exists():
        return []
    try:
        return json.loads(BACKGROUND_TEMPLATES_FILE.read_text(encoding='utf-8'))
    except Exception:
        return []


def _validate_background_template_for_render(template_id: str) -> None:
    tid = str(template_id or '').strip()
    if not tid:
        return
    rows = _load_background_templates()
    row = next((r for r in rows if str(r.get('id')) == tid), None)
    if not row:
        raise HTTPException(status_code=400, detail=f'background template not found: {tid}')
    if str(row.get('status', 'approved')).lower() != 'approved':
        raise HTTPException(status_code=400, detail='background template is not approved')
    if float(row.get('readabilityScore') or 0.85) < 0.7:
        raise HTTPException(status_code=400, detail='background template failed readability threshold')


def _persist_render_background(session: Session, workspace_id: str, render_id: str, template_id: str) -> None:
    tid = str(template_id or '').strip()
    if not tid:
        return
    row = session.exec(select(VideoRenderBackground).where(VideoRenderBackground.render_id == render_id)).first()
    if not row:
        row = VideoRenderBackground(
            id=str(uuid4()),
            workspace_id=workspace_id,
            render_id=render_id,
            background_template_id=tid,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    else:
        row.background_template_id = tid
        row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()


def _background_for_render(session: Session, render_id: str) -> Optional[str]:
    row = session.exec(select(VideoRenderBackground).where(VideoRenderBackground.render_id == render_id)).first()
    return row.background_template_id if row else None


def _background_url_for_render(session: Session, render_id: str, platform_variant: str = 'vertical_9_16') -> str:
    tid = _background_for_render(session, render_id)
    if not tid:
        return ''
    rows = _load_background_templates()
    tpl = next((r for r in rows if str(r.get('id')) == tid), None)
    if not tpl:
        return ''
    variants = tpl.get('platformVariants') or {}
    url = str(variants.get(platform_variant) or '').strip()
    return url if (url.startswith('http://') or url.startswith('https://')) else ''


def _execute_video_render(job: VideoRenderJob, voice_render: VoiceRenderJob, session: Session) -> None:
    chosen = pick_model_with_policy(
        capability='video',
        task_tag='faceless_video_render',
        preference='quality',
        scores={
            'hook_score': 0.8,
            'clarity_score': 0.8,
            'narrative_score': 0.8,
            'cta_fit_score': 0.75,
            'policy_safety_score': 1.0,
            'visual_beatmap_score': 0.8,
            'render_readiness': 0.8,
        },
    )

    # Always prefer real provider render when configured.
    heygen = HeyGenClient()
    if heygen.configured():
        try:
            audio_url = (voice_render.audio_uri or '').strip()
            if not (audio_url.startswith('http://') or audio_url.startswith('https://')):
                audio_url = ''
            background_url = _background_url_for_render(session, job.id, platform_variant='vertical_9_16')
            resp = heygen.create_video(script_text=job.script_text, audio_url=audio_url, background_url=background_url)
            data = resp.get('data') if isinstance(resp, dict) else None
            if isinstance(data, dict) and data.get('video_id'):
                job.provider = 'heygen'
                job.provider_job_id = str(data.get('video_id'))
                job.status = 'queued'
                job.error = ''
                job.updated_at = datetime.utcnow()
                session.add(job)
                session.commit()
                return
            job.error = f"heygen_unexpected_response: {str(resp)[:300]}"
        except Exception as e:
            job.error = f"{chosen.get('id')} provider_error: {e}"

    # Default to fail-closed (no fake 'succeeded' stub in production path).
    allow_stub = os.getenv('DO_VIDEO_STUB_FALLBACK', 'false').strip().lower() == 'true'
    if not allow_stub:
        job.provider = 'stub-video'
        job.status = 'failed'
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()
        return

    # Optional stub output artifact for local/dev continuity.
    VIDEO_ROOT.mkdir(parents=True, exist_ok=True)
    out = VIDEO_ROOT / f'{job.id}.txt'
    out.write_text(
        '\n'.join([
            'VIDEO_RENDER_STUB',
            f'voice_render_id={voice_render.id}',
            f'audio_uri={voice_render.audio_uri}',
            f'script={job.script_text}',
        ]),
        encoding='utf-8',
    )

    job.provider = 'stub-video'
    job.video_uri = str(out)
    job.status = 'succeeded'
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()


@router.post('/records')
def create_consent_record(payload: CreateConsentRequest, session: Session = Depends(get_session)):
    rec = ConsentRecord(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        subject_full_name=payload.subjectFullName.strip(),
        subject_email=payload.subjectEmail.strip().lower(),
        consent_type=payload.consentType,
        scope_json=json.dumps(payload.scope or {}),
        evidence_uri=payload.evidenceUri.strip(),
    )
    session.add(rec)
    session.commit()
    return {'id': rec.id, 'status': rec.status}


@router.post('/records/{record_id}/verify-identity')
def verify_identity(record_id: str, payload: VerifyIdentityRequest, session: Session = Depends(get_session)):
    rec = session.get(ConsentRecord, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail='consent record not found')

    iv = IdentityVerification(
        id=str(uuid4()),
        consent_record_id=record_id,
        provider=payload.provider,
        status=payload.status,
        score=payload.score,
        metadata_json=json.dumps(payload.metadata or {}),
        updated_at=datetime.utcnow(),
    )
    session.add(iv)
    session.commit()
    return {'ok': True, 'verificationId': iv.id, 'status': iv.status}


@router.post('/records/{record_id}/revoke')
def revoke_consent(record_id: str, payload: RevokeConsentRequest, session: Session = Depends(get_session)):
    rec = session.get(ConsentRecord, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail='consent record not found')
    rec.status = 'revoked'
    rec.revoked_at = datetime.utcnow()
    rec.scope_json = json.dumps({'revocation_reason': payload.reason})
    session.add(rec)
    session.commit()
    return {'ok': True, 'id': record_id, 'status': rec.status}


@router.get('/records')
def list_consent_records(
    workspaceId: str = Query(default='default'),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(ConsentRecord)
        .where(ConsentRecord.workspace_id == workspaceId)
        .order_by(ConsentRecord.created_at.desc())
        .limit(limit)
    ).all()

    out = []
    for r in rows:
        if status and r.status != status:
            continue
        out.append({
            'id': r.id,
            'subjectFullName': r.subject_full_name,
            'subjectEmail': r.subject_email,
            'consentType': r.consent_type,
            'status': r.status,
            'signedAt': r.signed_at.isoformat(),
            'revokedAt': r.revoked_at.isoformat() if r.revoked_at else None,
            'evidenceUri': r.evidence_uri,
        })
    return {'items': out}


def _assert_consent_verified(session: Session, consent_record_id: str):
    rec = session.get(ConsentRecord, consent_record_id)
    if not rec:
        raise HTTPException(status_code=404, detail='consent record not found')
    if rec.status != 'signed':
        raise HTTPException(status_code=400, detail='consent record not active/signed')

    ver = session.exec(
        select(IdentityVerification)
        .where(IdentityVerification.consent_record_id == consent_record_id)
        .order_by(IdentityVerification.created_at.desc())
    ).first()
    if not ver or ver.status != 'verified':
        raise HTTPException(status_code=400, detail='identity verification required before profile creation')


@router.post('/voice/profiles')
def create_voice_profile(payload: CreateVoiceProfileRequest, session: Session = Depends(get_session)):
    _assert_consent_verified(session, payload.consentRecordId)
    vp = VoiceProfile(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        consent_record_id=payload.consentRecordId,
        provider=payload.provider,
        provider_voice_id=payload.providerVoiceId,
        display_name=payload.displayName,
        status='active' if payload.providerVoiceId else 'pending',
        updated_at=datetime.utcnow(),
    )
    session.add(vp)
    session.commit()
    return {'id': vp.id, 'status': vp.status}


@router.get('/voice/profiles')
def list_voice_profiles(
    workspaceId: str = Query(default='default'),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(VoiceProfile)
        .where(VoiceProfile.workspace_id == workspaceId)
        .order_by(VoiceProfile.created_at.desc())
        .limit(limit)
    ).all()
    out = []
    for r in rows:
        if status and r.status != status:
            continue
        out.append({
            'id': r.id,
            'displayName': r.display_name,
            'provider': r.provider,
            'providerVoiceId': r.provider_voice_id,
            'status': r.status,
            'consentRecordId': r.consent_record_id,
        })
    return {'items': out}


@router.post('/voice/profiles/{profile_id}/delete')
def delete_voice_profile(profile_id: str, session: Session = Depends(get_session)):
    vp = session.get(VoiceProfile, profile_id)
    if not vp:
        raise HTTPException(status_code=404, detail='voice profile not found')

    vp.status = 'disabled'
    vp.provider_voice_id = ''
    vp.updated_at = datetime.utcnow()
    session.add(vp)
    session.commit()
    return {'ok': True, 'id': vp.id, 'status': vp.status}


def _execute_voice_render(job: VoiceRenderJob, vp: VoiceProfile, session: Session) -> None:
    client = ElevenLabsClient()
    if not client.configured():
        job.status = 'failed'
        job.error = 'ELEVENLABS_API_KEY not configured'
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()
        raise HTTPException(status_code=400, detail='ELEVENLABS_API_KEY not configured')

    try:
        audio = client.text_to_speech(voice_id=vp.provider_voice_id, text=job.script_text)
        AUDIO_ROOT.mkdir(parents=True, exist_ok=True)
        out_path = AUDIO_ROOT / f'{job.id}.mp3'
        out_path.write_bytes(audio)
        job.audio_uri = str(out_path)
        job.status = 'succeeded'
        job.error = ''
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()
    except Exception as e:
        job.status = 'failed'
        job.error = str(e)
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()
        raise HTTPException(status_code=502, detail=f'voice render failed: {e}')


@router.post('/voice/renders')
def create_voice_render(payload: CreateVoiceRenderRequest, session: Session = Depends(get_session)):
    vp = session.get(VoiceProfile, payload.voiceProfileId)
    if not vp:
        raise HTTPException(status_code=404, detail='voice profile not found')
    if vp.workspace_id != payload.workspaceId:
        raise HTTPException(status_code=400, detail='voice profile workspace mismatch')
    if vp.status != 'active' or not vp.provider_voice_id:
        raise HTTPException(status_code=400, detail='voice profile not active or missing provider voice id')

    # re-assert consent is still valid at render time
    _assert_consent_verified(session, vp.consent_record_id)

    job = VoiceRenderJob(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        voice_profile_id=vp.id,
        script_text=payload.scriptText.strip(),
        provider=vp.provider,
        status='queued',
        estimated_cost_usd=_estimate_voice_cost_usd(payload.scriptText),
        updated_at=datetime.utcnow(),
    )
    session.add(job)
    session.commit()

    _execute_voice_render(job=job, vp=vp, session=session)

    return {
        'id': job.id,
        'status': job.status,
        'audioUri': job.audio_uri,
        'estimatedCostUsd': job.estimated_cost_usd,
    }


@router.get('/voice/renders')
def list_voice_renders(
    workspaceId: str = Query(default='default'),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(VoiceRenderJob)
        .where(VoiceRenderJob.workspace_id == workspaceId)
        .order_by(VoiceRenderJob.created_at.desc())
        .limit(limit)
    ).all()

    out = []
    for r in rows:
        if status and r.status != status:
            continue
        out.append({
            'id': r.id,
            'voiceProfileId': r.voice_profile_id,
            'status': r.status,
            'audioUri': r.audio_uri,
            'error': r.error,
            'estimatedCostUsd': r.estimated_cost_usd,
            'createdAt': r.created_at.isoformat(),
            'updatedAt': r.updated_at.isoformat(),
        })
    return {'items': out}


@router.get('/voice/renders/{render_id}/audio')
def get_voice_render_audio(render_id: str, session: Session = Depends(get_session)):
    r = session.get(VoiceRenderJob, render_id)
    if not r:
        raise HTTPException(status_code=404, detail='voice render not found')
    if not r.audio_uri:
        raise HTTPException(status_code=404, detail='audio not available')

    p = Path(r.audio_uri)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail='audio file missing')

    return FileResponse(path=str(p), media_type='audio/mpeg', filename=f'{render_id}.mp3')


@router.post('/voice/renders/{render_id}/retry')
def retry_voice_render(render_id: str, session: Session = Depends(get_session)):
    r = session.get(VoiceRenderJob, render_id)
    if not r:
        raise HTTPException(status_code=404, detail='voice render not found')
    if r.status != 'failed':
        raise HTTPException(status_code=400, detail='only failed renders can be retried')

    vp = session.get(VoiceProfile, r.voice_profile_id)
    if not vp:
        raise HTTPException(status_code=404, detail='voice profile not found for render')

    r.status = 'queued'
    r.error = ''
    r.updated_at = datetime.utcnow()
    session.add(r)
    session.commit()

    _execute_voice_render(job=r, vp=vp, session=session)
    return {'id': r.id, 'status': r.status, 'audioUri': r.audio_uri}


@router.post('/voice/renders/{render_id}/approve')
def approve_voice_render(render_id: str, session: Session = Depends(get_session)):
    r = session.get(VoiceRenderJob, render_id)
    if not r:
        raise HTTPException(status_code=404, detail='voice render not found')
    if r.status != 'succeeded':
        raise HTTPException(status_code=400, detail='only succeeded renders can be approved')
    r.status = 'approved'
    r.updated_at = datetime.utcnow()
    session.add(r)
    session.commit()
    return {'id': r.id, 'status': r.status}


@router.post('/video/renders/faceless/render-top')
def render_top_faceless(payload: FacelessRenderTopRequest, session: Session = Depends(get_session)):
    scripts = [str(s or '').strip() for s in (payload.scripts or []) if str(s or '').strip()]
    if not scripts:
        raise HTTPException(status_code=400, detail='scripts required')

    limits = _workspace_video_limits(session, payload.workspaceId)
    usage = _workspace_video_usage(session, payload.workspaceId)
    if usage['monthly_count'] >= limits['monthly_video_cap']:
        raise HTTPException(status_code=402, detail=f"monthly video limit reached ({limits['monthly_video_cap']}). Upgrade to increase cap.")
    if usage['active_count'] >= limits['concurrency_cap']:
        raise HTTPException(status_code=429, detail=f"concurrency limit reached ({limits['concurrency_cap']}). Wait for current renders to finish.")

    vr = session.exec(
        select(VoiceRenderJob)
        .where(VoiceRenderJob.workspace_id == payload.workspaceId, VoiceRenderJob.status.in_(['approved', 'succeeded']))
        .order_by(VoiceRenderJob.created_at.desc())
    ).first()

    # Voice render is optional: prefer audio-first when available, otherwise use HeyGen text+voice_id mode.
    if not vr:
        vr = VoiceRenderJob(
            id='transient',
            workspace_id=payload.workspaceId,
            voice_profile_id='transient',
            script_text='',
            provider='transient',
            provider_job_id='',
            audio_uri='',
            status='succeeded',
            error='',
            estimated_cost_usd=0.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    _validate_background_template_for_render(payload.selectedBackgroundTemplateId)

    top_n = max(1, min(int(payload.topN or 3), 5))
    remaining_monthly = max(0, limits['monthly_video_cap'] - usage['monthly_count'])
    allowed_now = max(0, min(top_n, remaining_monthly, limits['concurrency_cap'] - usage['active_count']))
    if allowed_now <= 0:
        raise HTTPException(status_code=429, detail='render capacity unavailable right now under current plan limits')

    created = []
    for script in scripts[:allowed_now]:
        job = VideoRenderJob(
            id=str(uuid4()),
            workspace_id=payload.workspaceId,
            voice_render_id=vr.id,
            provider='heygen',
            script_text=script,
            status='queued',
            estimated_cost_usd=_estimate_video_cost_usd(script),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(job)
        session.commit()

        if payload.selectedBackgroundTemplateId:
            _persist_render_background(
                session=session,
                workspace_id=payload.workspaceId,
                render_id=job.id,
                template_id=payload.selectedBackgroundTemplateId,
            )

        _execute_video_render(job=job, voice_render=vr, session=session)
        session.refresh(job)
        created.append({
            'id': job.id,
            'status': job.status,
            'provider': job.provider,
            'providerJobId': job.provider_job_id,
            'videoUri': job.video_uri,
            'backgroundTemplateId': _background_for_render(session, job.id),
        })

    latest_usage = _workspace_video_usage(session, payload.workspaceId)
    return {
        'ok': True,
        'count': len(created),
        'items': created,
        'limits': limits,
        'usage': latest_usage,
    }


@router.get('/video/limits')
def video_limits(
    workspaceId: str = Query(default='default'),
    session: Session = Depends(get_session),
):
    limits = _workspace_video_limits(session, workspaceId)
    usage = _workspace_video_usage(session, workspaceId)
    return {'workspaceId': workspaceId, 'limits': limits, 'usage': usage}


@router.post('/video/renders')
def create_video_render(payload: CreateVideoRenderRequest, session: Session = Depends(get_session)):
    vr = session.get(VoiceRenderJob, payload.voiceRenderId)
    if not vr:
        raise HTTPException(status_code=404, detail='voice render not found')
    if vr.workspace_id != payload.workspaceId:
        raise HTTPException(status_code=400, detail='voice render workspace mismatch')
    if vr.status != 'approved':
        raise HTTPException(status_code=400, detail='voice render must be approved before video render')

    _validate_background_template_for_render(payload.backgroundTemplateId)

    # Queue hygiene: avoid duplicate inflight jobs and cap active inflight jobs per workspace.
    inflight = session.exec(
        select(VideoRenderJob).where(
            VideoRenderJob.workspace_id == payload.workspaceId,
            VideoRenderJob.status.in_(['queued', 'processing', 'rendering']),
        )
    ).all()

    # Auto-expire stale queued jobs before enforcing caps.
    for row in inflight:
        _apply_queue_timeout(row, session)

    inflight = session.exec(
        select(VideoRenderJob).where(
            VideoRenderJob.workspace_id == payload.workspaceId,
            VideoRenderJob.status.in_(['queued', 'processing', 'rendering']),
        )
    ).all()

    max_inflight = int((os.getenv('DO_VIDEO_MAX_INFLIGHT_PER_WORKSPACE') or '1').strip() or '1')
    if len(inflight) >= max_inflight:
        raise HTTPException(status_code=429, detail=f'video queue busy: {len(inflight)} inflight (cap {max_inflight})')

    duplicate = session.exec(
        select(VideoRenderJob).where(
            VideoRenderJob.workspace_id == payload.workspaceId,
            VideoRenderJob.voice_render_id == payload.voiceRenderId,
            VideoRenderJob.status.in_(['queued', 'processing', 'rendering']),
        )
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail=f'duplicate inflight render exists: {duplicate.id}')

    job = VideoRenderJob(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        voice_render_id=vr.id,
        provider='stub-video',
        script_text=(payload.scriptText or vr.script_text).strip(),
        status='queued',
        estimated_cost_usd=_estimate_video_cost_usd(payload.scriptText or vr.script_text),
        updated_at=datetime.utcnow(),
    )
    session.add(job)
    session.commit()

    if payload.backgroundTemplateId:
        _persist_render_background(
            session=session,
            workspace_id=payload.workspaceId,
            render_id=job.id,
            template_id=payload.backgroundTemplateId,
        )

    _execute_video_render(job=job, voice_render=vr, session=session)

    return {
        'id': job.id,
        'status': job.status,
        'videoUri': job.video_uri,
        'estimatedCostUsd': job.estimated_cost_usd,
        'provider': job.provider,
        'providerJobId': job.provider_job_id,
        'backgroundTemplateId': _background_for_render(session, job.id),
    }


@router.get('/video/renders')
def list_video_renders(
    workspaceId: str = Query(default='default'),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(VideoRenderJob)
        .where(VideoRenderJob.workspace_id == workspaceId)
        .order_by(VideoRenderJob.created_at.desc())
        .limit(limit)
    ).all()
    out = []
    for r in rows:
        _apply_queue_timeout(r, session)
        if status and r.status != status:
            continue
        out.append({
            'id': r.id,
            'voiceRenderId': r.voice_render_id,
            'status': r.status,
            'provider': r.provider,
            'providerJobId': r.provider_job_id,
            'videoUri': r.video_uri,
            'error': r.error,
            'estimatedCostUsd': r.estimated_cost_usd,
            'backgroundTemplateId': _background_for_render(session, r.id),
            'createdAt': r.created_at.isoformat(),
            'updatedAt': r.updated_at.isoformat(),
        })
    return {'items': out}


@router.get('/video/background-analytics')
def background_analytics(
    workspaceId: str = Query(default='default'),
    limit: int = Query(default=200, ge=1, le=2000),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(VideoRenderJob)
        .where(VideoRenderJob.workspace_id == workspaceId)
        .order_by(VideoRenderJob.created_at.desc())
        .limit(limit)
    ).all()

    stats: dict[str, dict] = {}
    for r in rows:
        tid = _background_for_render(session, r.id) or 'unassigned'
        s = stats.get(tid) or {
            'backgroundTemplateId': tid,
            'total': 0,
            'succeeded': 0,
            'approved': 0,
            'failed': 0,
        }
        s['total'] += 1
        st = str(r.status or '').lower()
        if st == 'succeeded':
            s['succeeded'] += 1
        elif st == 'approved':
            s['approved'] += 1
        elif st == 'failed':
            s['failed'] += 1
        stats[tid] = s

    items = list(stats.values())
    for i in items:
        total = max(1, i['total'])
        i['passRate'] = round((i['succeeded'] + i['approved']) / total, 3)
        i['approvalRate'] = round(i['approved'] / total, 3)

    items.sort(key=lambda x: (x['approvalRate'], x['passRate'], x['total']), reverse=True)
    return {'workspaceId': workspaceId, 'count': len(items), 'items': items}


@router.post('/video/renders/{render_id}/retry')
def retry_video_render(render_id: str, session: Session = Depends(get_session)):
    r = session.get(VideoRenderJob, render_id)
    if not r:
        raise HTTPException(status_code=404, detail='video render not found')
    if r.status != 'failed':
        raise HTTPException(status_code=400, detail='only failed renders can be retried')

    r.status = 'queued'
    r.error = ''
    r.updated_at = datetime.utcnow()
    session.add(r)
    session.commit()

    vr = session.get(VoiceRenderJob, r.voice_render_id)
    if not vr:
        raise HTTPException(status_code=404, detail='linked voice render not found')

    _execute_video_render(job=r, voice_render=vr, session=session)
    return {'id': r.id, 'status': r.status, 'videoUri': r.video_uri, 'provider': r.provider, 'providerJobId': r.provider_job_id}


def _refresh_video_render_status(row: VideoRenderJob, session: Session) -> dict:
    if _apply_queue_timeout(row, session):
        return {
            'id': row.id,
            'status': row.status,
            'videoUri': row.video_uri,
            'provider': row.provider,
            'providerJobId': row.provider_job_id,
            'error': row.error,
        }

    if row.provider != 'heygen' or not row.provider_job_id:
        return {'id': row.id, 'status': row.status, 'provider': row.provider, 'providerJobId': row.provider_job_id}

    client = HeyGenClient()
    if not client.configured():
        raise HTTPException(status_code=400, detail='HEYGEN_API_KEY not configured')

    resp = client.get_video(row.provider_job_id)
    data = resp.get('data') if isinstance(resp, dict) else None
    status = (data or {}).get('status') if isinstance(data, dict) else None
    video_url = (data or {}).get('video_url') if isinstance(data, dict) else None

    if status in ('completed', 'success', 'succeeded'):
        row.status = 'succeeded'
        row.video_uri = video_url or row.video_uri
    elif status in ('failed', 'error'):
        row.status = 'failed'
        row.error = str((data or {}).get('error') or 'provider failed')
    else:
        row.status = 'queued'
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()

    return {'id': row.id, 'status': row.status, 'videoUri': row.video_uri, 'provider': row.provider, 'providerJobId': row.provider_job_id}


@router.post('/video/renders/{render_id}/refresh')
def refresh_video_render(render_id: str, session: Session = Depends(get_session)):
    r = session.get(VideoRenderJob, render_id)
    if not r:
        raise HTTPException(status_code=404, detail='video render not found')

    try:
        return _refresh_video_render_status(r, session)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'heygen refresh failed: {e}')


@router.post('/video/renders/refresh-queued')
def refresh_queued_video_renders(
    workspaceId: str = Query(default='default'),
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(VideoRenderJob)
        .where(VideoRenderJob.workspace_id == workspaceId, VideoRenderJob.status == 'queued')
        .order_by(VideoRenderJob.created_at.asc())
        .limit(limit)
    ).all()

    updated = []
    for r in rows:
        try:
            updated.append(_refresh_video_render_status(r, session))
        except Exception as e:
            updated.append({'id': r.id, 'status': r.status, 'error': str(e)})

    return {'workspaceId': workspaceId, 'count': len(updated), 'items': updated}


@router.post('/video/renders/{render_id}/approve')
def approve_video_render(render_id: str, session: Session = Depends(get_session)):
    r = session.get(VideoRenderJob, render_id)
    if not r:
        raise HTTPException(status_code=404, detail='video render not found')
    if r.status != 'succeeded':
        raise HTTPException(status_code=400, detail='only succeeded renders can be approved')
    r.status = 'approved'
    r.updated_at = datetime.utcnow()
    session.add(r)
    session.commit()
    return {'id': r.id, 'status': r.status}


@router.post('/avatar/profiles')
def create_avatar_profile(payload: CreateAvatarProfileRequest, session: Session = Depends(get_session)):
    _assert_consent_verified(session, payload.consentRecordId)

    avatar_count = session.exec(
        select(AvatarProfile)
        .where(AvatarProfile.workspace_id == payload.workspaceId)
    ).all()
    limit = _workspace_avatar_limit(session, payload.workspaceId)
    if len(avatar_count) >= limit:
        raise HTTPException(status_code=400, detail=f'avatar limit reached ({limit}) for this workspace tier')

    ap = AvatarProfile(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        consent_record_id=payload.consentRecordId,
        provider=payload.provider,
        provider_avatar_id=payload.providerAvatarId,
        display_name=payload.displayName,
        status='active' if payload.providerAvatarId else 'pending',
        updated_at=datetime.utcnow(),
    )
    session.add(ap)
    session.commit()
    return {'id': ap.id, 'status': ap.status}


@router.post('/avatar/heygen/create')
def create_heygen_avatar(payload: CreateHeyGenAvatarRequest, session: Session = Depends(get_session)):
    client = HeyGenClient()
    if not client.configured():
        raise HTTPException(status_code=400, detail='HEYGEN_API_KEY not configured')

    avatar_count = session.exec(
        select(AvatarProfile)
        .where(AvatarProfile.workspace_id == payload.workspaceId)
    ).all()
    limit = _workspace_avatar_limit(session, payload.workspaceId)
    if len(avatar_count) >= limit:
        raise HTTPException(status_code=400, detail=f'avatar limit reached ({limit}) for this workspace tier')

    rec = ConsentRecord(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        subject_full_name=payload.fullName.strip(),
        subject_email=payload.email.strip().lower(),
        consent_type='likeness',
        scope_json=json.dumps({'usage': 'avatar_generation', 'provider': 'heygen'}),
        evidence_uri=payload.consentVideoUrl.strip(),
    )
    session.add(rec)
    session.commit()

    ver = IdentityVerification(
        id=str(uuid4()),
        consent_record_id=rec.id,
        provider='manual',
        status='verified',
        score=1.0,
        metadata_json=json.dumps({'source': 'avatar-studio-heygen-create'}),
        updated_at=datetime.utcnow(),
    )
    session.add(ver)
    session.commit()

    try:
        resp = client.create_digital_twin(
            avatar_name=payload.avatarName.strip() or 'Custom Avatar',
            training_footage_url=payload.trainingFootageUrl.strip(),
            consent_video_url=payload.consentVideoUrl.strip(),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'heygen avatar create failed: {e}')

    data = resp.get('data') if isinstance(resp, dict) else {}
    provider_avatar_id = str((data or {}).get('avatar_id') or '')
    provider_status = str((data or {}).get('status') or 'in_progress')

    ap = AvatarProfile(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        consent_record_id=rec.id,
        provider='heygen',
        provider_avatar_id=provider_avatar_id,
        display_name=payload.avatarName.strip() or 'Custom Avatar',
        status='active' if provider_status == 'complete' else 'pending',
        updated_at=datetime.utcnow(),
    )
    session.add(ap)
    session.commit()

    return {
        'ok': True,
        'avatarProfileId': ap.id,
        'consentRecordId': rec.id,
        'providerAvatarId': provider_avatar_id,
        'providerStatus': provider_status,
        'status': ap.status,
        'raw': resp,
    }


@router.post('/avatar/heygen/{avatar_profile_id}/refresh')
def refresh_heygen_avatar(avatar_profile_id: str, session: Session = Depends(get_session)):
    row = session.get(AvatarProfile, avatar_profile_id)
    if not row:
        raise HTTPException(status_code=404, detail='avatar profile not found')
    if row.provider != 'heygen' or not row.provider_avatar_id:
        raise HTTPException(status_code=400, detail='avatar profile is not linked to HeyGen')

    client = HeyGenClient()
    if not client.configured():
        raise HTTPException(status_code=400, detail='HEYGEN_API_KEY not configured')

    try:
        resp = client.get_digital_twin(row.provider_avatar_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'heygen avatar refresh failed: {e}')

    data = resp.get('data') if isinstance(resp, dict) else {}
    provider_status = str((data or {}).get('status') or '').lower()
    if provider_status == 'complete':
        row.status = 'active'
    elif provider_status == 'failed':
        row.status = 'disabled'
    else:
        row.status = 'pending'
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()

    return {
        'ok': True,
        'avatarProfileId': row.id,
        'providerAvatarId': row.provider_avatar_id,
        'providerStatus': provider_status,
        'status': row.status,
        'raw': resp,
    }

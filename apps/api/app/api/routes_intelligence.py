from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models.intelligence import (
    SuggestionFeedbackEvent,
    TrendSuggestion,
    WorkspaceLearningProfile,
    SignalFeature,
    SignalScore,
)
from app.models.mvp import MVPSource, MVPSourceItem
from app.services.authz import actor_user_id

router = APIRouter(prefix='/intelligence', tags=['intelligence'])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _get_profile(session: Session, workspace_id: str) -> WorkspaceLearningProfile:
    p = session.get(WorkspaceLearningProfile, workspace_id)
    if not p:
        p = WorkspaceLearningProfile(workspace_id=workspace_id, updated_at=now_utc())
        session.add(p)
        session.commit()
        session.refresh(p)
    return p


class SeedSuggestionRequest(BaseModel):
    workspaceId: str
    topic: str
    source: str = 'manual'
    whyNow: str = ''
    trendScore: float = 0.5
    brandFitScore: float = 0.5
    policyRiskScore: float = 0.1


class FeedbackRequest(BaseModel):
    workspaceId: str
    suggestionId: str
    eventType: str  # viewed|accepted|rejected|edited|published
    editDistance: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ImportFromSourceRequest(BaseModel):
    workspaceId: str
    sourceId: str
    limit: int = 100


@router.post('/suggestions/seed')
def seed_suggestion(payload: SeedSuggestionRequest, session: Session = Depends(get_session)):
    p = _get_profile(session, payload.workspaceId)
    final = max(0.0, min(1.0, p.trend_weight * payload.trendScore + p.brand_fit_weight * payload.brandFitScore + p.source_weight * (1.0 - payload.policyRiskScore)))
    s = TrendSuggestion(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        topic=payload.topic,
        source=payload.source,
        why_now=payload.whyNow,
        trend_score=payload.trendScore,
        brand_fit_score=payload.brandFitScore,
        policy_risk_score=payload.policyRiskScore,
        final_score=final,
        created_at=now_utc(),
    )
    session.add(s)

    features, final_v2, confidence, explanation = _v2_feature_score(payload.topic, payload.whyNow, payload.trendScore, payload.brandFitScore, payload.policyRiskScore)
    sf = SignalFeature(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        suggestion_id=s.id,
        trend_velocity=float(features['trendVelocity']),
        freshness=float(features['freshness']),
        brand_relevance=float(features['brandRelevance']),
        saturation_penalty=float(features['saturationPenalty']),
        risk_penalty=float(features['riskPenalty']),
        created_at=now_utc(),
    )
    ss = SignalScore(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        suggestion_id=s.id,
        score_version='v2',
        final_score=float(final_v2),
        confidence=float(confidence),
        explanation_json=json.dumps(explanation),
        created_at=now_utc(),
    )
    session.add(sf)
    session.add(ss)

    # Use v2 score as displayed final for newly seeded suggestions.
    s.final_score = float(final_v2)
    session.add(s)
    session.commit()
    return {'ok': True, 'id': s.id, 'finalScore': s.final_score, 'confidence': confidence, 'explanation': explanation}


@router.post('/feedback')
def submit_feedback(
    payload: FeedbackRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
):
    s = session.get(TrendSuggestion, payload.suggestionId)
    if not s or s.workspace_id != payload.workspaceId:
        raise HTTPException(status_code=404, detail='suggestion not found')

    evt = SuggestionFeedbackEvent(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        suggestion_id=payload.suggestionId,
        user_id=user_id,
        event_type=payload.eventType,
        edit_distance=payload.editDistance,
        metadata_json=json.dumps(payload.metadata or {}),
        created_at=now_utc(),
    )
    session.add(evt)

    p = _get_profile(session, payload.workspaceId)
    lr = 0.03
    if payload.eventType == 'accepted':
        p.brand_fit_weight = min(0.7, p.brand_fit_weight + lr)
        p.trend_weight = min(0.7, p.trend_weight + lr / 2)
        s.status = 'accepted'
    elif payload.eventType == 'rejected':
        p.reject_penalty = min(0.4, p.reject_penalty + lr)
        p.brand_fit_weight = max(0.1, p.brand_fit_weight - lr / 2)
        s.status = 'rejected'
    elif payload.eventType == 'published':
        p.source_weight = max(0.1, p.source_weight - lr / 3)
        s.status = 'published'

    total = p.source_weight + p.trend_weight + p.brand_fit_weight
    p.source_weight /= total
    p.trend_weight /= total
    p.brand_fit_weight /= total
    p.updated_at = now_utc()

    session.add(p)
    session.add(s)
    session.commit()

    return {
        'ok': True,
        'profile': {
            'sourceWeight': p.source_weight,
            'trendWeight': p.trend_weight,
            'brandFitWeight': p.brand_fit_weight,
            'rejectPenalty': p.reject_penalty,
        },
        'suggestionStatus': s.status,
    }


def _canon_topic(v: str) -> str:
    return ' '.join((v or '').strip().lower().split())


def _score_from_source_item(title: str, body: str) -> tuple[float, float, float, str]:
    txt = f"{title} {body}".lower()
    trend_markers = ['breaking', 'today', 'new', 'launch', 'announces', 'update', 'trend', 'just', 'released']
    risk_markers = ['guarantee', 'never fail', 'secret', 'insider', 'hack', 'get rich quick']
    brand_markers = ['brand', 'content', 'marketing', 'audience', 'campaign', 'creator', 'growth', 'customer', 'product']

    trend_hits = sum(1 for t in trend_markers if t in txt)
    brand_hits = sum(1 for t in brand_markers if t in txt)
    risk_hits = sum(1 for t in risk_markers if t in txt)

    # Raise baseline so relevant items can clear operator quality gates.
    trend = 0.5 + 0.08 * trend_hits
    brand = 0.45 + 0.07 * brand_hits
    risk = 0.05 + 0.09 * risk_hits

    # Penalize thin/generic records.
    if len((title or '').strip()) < 12:
        brand -= 0.08
    if len((body or '').strip()) < 80:
        trend -= 0.06

    trend = max(0.0, min(1.0, trend))
    brand = max(0.0, min(1.0, brand))
    risk = max(0.0, min(1.0, risk))

    why = 'Live signal scored for recency, brand relevance, and policy risk.'
    return trend, brand, risk, why


def _v2_feature_score(topic: str, body: str, trend: float, brand: float, risk: float) -> tuple[dict, float, float, dict]:
    txt = f"{topic} {body}".lower()
    velocity_markers = ['breaking', 'just', 'today', 'now', 'launch', 'released']
    hype_markers = ['viral', 'everyone', 'top 10', 'ultimate', 'best ever']

    trend_velocity = min(1.0, 0.35 + 0.12 * sum(1 for t in velocity_markers if t in txt))
    freshness = 0.82 if any(t in txt for t in ('today', 'just', 'new', 'released')) else 0.58
    brand_relevance = max(0.0, min(1.0, brand))
    saturation_penalty = min(0.45, 0.07 * sum(1 for t in hype_markers if t in txt))
    risk_penalty = max(0.0, min(1.0, risk))

    # Weighted quality score v2
    base = (0.32 * trend_velocity) + (0.24 * freshness) + (0.34 * brand_relevance) + (0.10 * max(0.0, trend))
    final = max(0.0, min(1.0, base - (0.55 * saturation_penalty) - (0.65 * risk_penalty)))

    confidence = max(0.2, min(0.98, 0.45 + 0.25 * freshness + 0.2 * brand_relevance + 0.1 * trend_velocity))
    explanation = {
        'whyNow': f"Velocity {trend_velocity:.2f} and freshness {freshness:.2f} indicate current audience pull.",
        'whyBrand': f"Brand relevance scored {brand_relevance:.2f} for this workspace context.",
        'whyChannel': 'Best used for short-form social with clear hook and CTA.',
        'riskNote': f"Risk penalty {risk_penalty:.2f}, saturation penalty {saturation_penalty:.2f}.",
    }
    features = {
        'trendVelocity': trend_velocity,
        'freshness': freshness,
        'brandRelevance': brand_relevance,
        'saturationPenalty': saturation_penalty,
        'riskPenalty': risk_penalty,
    }
    return features, final, confidence, explanation


@router.post('/suggestions/import-from-source')
def import_suggestions_from_source(payload: ImportFromSourceRequest, session: Session = Depends(get_session)):
    src = session.get(MVPSource, payload.sourceId)
    if not src:
        raise HTTPException(status_code=404, detail='source not found')
    if src.workspace_id != payload.workspaceId:
        raise HTTPException(status_code=403, detail='source/workspace mismatch')

    lim = max(1, min(payload.limit, 500))
    rows = session.exec(
        select(MVPSourceItem)
        .where(MVPSourceItem.source_id == payload.sourceId)
        .order_by(MVPSourceItem.created_at.desc())
        .limit(lim)
    ).all()

    if not rows:
        return {'ok': True, 'imported': 0, 'reason': 'no source items found'}

    profile = _get_profile(session, payload.workspaceId)
    imported = 0
    skippedDuplicates = 0

    existing_rows = session.exec(
        select(TrendSuggestion.topic, TrendSuggestion.source)
        .where(TrendSuggestion.workspace_id == payload.workspaceId)
        .limit(5000)
    ).all()
    seen = {(_canon_topic(t), (s or '').strip().lower()) for t, s in existing_rows}

    for r in rows:
        topic = (r.title or '').strip() or (r.body or '').strip()[:120] or 'Untitled signal'
        body = (r.body or '').strip()
        if topic.lower() in {'apify source item', 'signal item', 'untitled signal'} and body:
            topic = ' '.join(body.split())[:120]

        source_tag = f'apify:{payload.sourceId}'
        dedupe_key = (_canon_topic(topic[:220]), source_tag)
        if dedupe_key in seen:
            skippedDuplicates += 1
            continue

        trend, brand, risk, why = _score_from_source_item(topic, body)
        baseline = max(0.0, min(1.0, profile.trend_weight * trend + profile.brand_fit_weight * brand + profile.source_weight * (1.0 - risk)))
        features, final_v2, confidence, explanation = _v2_feature_score(topic, body, trend, brand, risk)

        s = TrendSuggestion(
            id=str(uuid4()),
            workspace_id=payload.workspaceId,
            topic=topic[:220],
            source=source_tag,
            why_now=why,
            trend_score=trend,
            brand_fit_score=brand,
            policy_risk_score=risk,
            final_score=max(0.0, min(1.0, (0.35 * baseline) + (0.65 * final_v2))),
            created_at=now_utc(),
        )
        session.add(s)

        sf = SignalFeature(
            id=str(uuid4()),
            workspace_id=payload.workspaceId,
            suggestion_id=s.id,
            trend_velocity=float(features['trendVelocity']),
            freshness=float(features['freshness']),
            brand_relevance=float(features['brandRelevance']),
            saturation_penalty=float(features['saturationPenalty']),
            risk_penalty=float(features['riskPenalty']),
            created_at=now_utc(),
        )
        ss = SignalScore(
            id=str(uuid4()),
            workspace_id=payload.workspaceId,
            suggestion_id=s.id,
            score_version='v2',
            final_score=float(s.final_score),
            confidence=float(confidence),
            explanation_json=json.dumps(explanation),
            created_at=now_utc(),
        )
        session.add(sf)
        session.add(ss)

        imported += 1
        seen.add(dedupe_key)

    session.commit()
    return {'ok': True, 'imported': imported, 'skippedDuplicates': skippedDuplicates, 'sourceId': payload.sourceId}


@router.get('/suggestions')
def list_suggestions(
    workspaceId: str = Query(...),
    limit: int = Query(default=20, ge=1, le=200),
    minFinalScore: float = Query(default=0.55, ge=0.0, le=1.0),
    maxPolicyRisk: float = Query(default=0.30, ge=0.0, le=1.0),
    includeBelowThreshold: bool = Query(default=False),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(TrendSuggestion)
        .where(TrendSuggestion.workspace_id == workspaceId)
        .order_by(TrendSuggestion.final_score.desc(), TrendSuggestion.created_at.desc())
        .limit(1000)
    ).all()

    score_rows = session.exec(
        select(SignalScore)
        .where(SignalScore.workspace_id == workspaceId)
        .order_by(SignalScore.created_at.desc())
        .limit(5000)
    ).all()
    score_map: dict[str, SignalScore] = {}
    for sr in score_rows:
        if sr.suggestion_id not in score_map:
            score_map[sr.suggestion_id] = sr

    out = []
    seen: set[tuple[str, str]] = set()
    for r in rows:
        if not includeBelowThreshold and (r.final_score < minFinalScore or r.policy_risk_score > maxPolicyRisk):
            continue

        key = (_canon_topic(r.topic), (r.source or '').strip().lower())
        if key in seen:
            continue
        seen.add(key)

        sr = score_map.get(r.id)
        explanation = {}
        confidence = None
        if sr and sr.explanation_json:
            try:
                explanation = json.loads(sr.explanation_json or '{}')
            except Exception:
                explanation = {}
            confidence = sr.confidence

        out.append({
            'id': r.id,
            'topic': r.topic,
            'source': r.source,
            'whyNow': r.why_now,
            'trendScore': r.trend_score,
            'brandFitScore': r.brand_fit_score,
            'policyRiskScore': r.policy_risk_score,
            'finalScore': r.final_score,
            'status': r.status,
            'confidence': confidence,
            'explanation': explanation,
        })
        if len(out) >= limit:
            break

    return out

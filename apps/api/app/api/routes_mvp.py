from __future__ import annotations

import csv
import io
import json
import os
import re
import hashlib
from datetime import datetime, timezone
from html import unescape
from typing import Any, Literal, Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from pathlib import Path
from uuid import uuid4


def _json_post(url: str, payload: dict, headers: dict[str, str], timeout: int = 12) -> dict:
    body = json.dumps(payload).encode('utf-8')
    req = Request(url, data=body, headers={**headers, 'Content-Type': 'application/json'})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode('utf-8')
    return json.loads(raw)

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models.mvp import (
    MVPContentItem,
    MVPPublishJob,
    MVPSchedule,
    MVPSource,
    MVPSourceItem,
    MVPWorkspace,
)

try:
    from app.models.mvp import MVPGenerationCostEvent
except Exception:  # pragma: no cover - startup compatibility fallback
    MVPGenerationCostEvent = None  # type: ignore
from app.models.auth import User, Workspace, WorkspaceMembership, WorkspaceSetting
from app.services.publish_provider import publish_content
from app.services.authz import actor_user_id, actor_user_email, require_workspace_role, require_corporate_email_domain
from app.services.model_preferences import get_workspace_prefs
from app.services.model_registry import pick_model, pick_model_with_policy, estimate_text_cost_usd as estimate_text_cost_with_registry
from app.services.usage_guardrails import evaluate_generation_guardrail
from app.services.entitlements import require_feature, workspace_account_type

router = APIRouter(tags=["mvp-core-flow"])

CONNECTIONS_FILE = Path(__file__).resolve().parents[2] / 'integrations_connections.json'
BACKGROUND_TEMPLATES_FILE = Path(__file__).resolve().parents[1] / 'config' / 'background_templates.json'


def _load_connections() -> dict[str, Any]:
    if not CONNECTIONS_FILE.exists():
        return {'workspaces': {}}
    try:
        return json.loads(CONNECTIONS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {'workspaces': {}}


def _actor_can_publish(workspace_id: str, channel: str, user_id: str) -> bool:
    data = _load_connections()
    ws = (data.get('workspaces') or {}).get(workspace_id) or {}
    authz = ws.get('publish_authorizations') or {}
    allowed = authz.get((channel or '').lower().strip()) or []
    return user_id in set(str(x).strip() for x in allowed)


def _load_background_templates() -> list[dict[str, Any]]:
    if not BACKGROUND_TEMPLATES_FILE.exists():
        return []
    try:
        return json.loads(BACKGROUND_TEMPLATES_FILE.read_text(encoding='utf-8'))
    except Exception:
        return []


def _save_background_templates(rows: list[dict[str, Any]]) -> None:
    BACKGROUND_TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    BACKGROUND_TEMPLATES_FILE.write_text(json.dumps(rows, indent=2), encoding='utf-8')


def _score_background_template(template: dict[str, Any], topic_text: str, mood: str, audience: str) -> float:
    score = 0.0
    tags = [str(t).lower() for t in (template.get('tags') or [])]
    topic_blob = f"{topic_text} {audience}".lower()

    if (template.get('mood') or '').lower() == (mood or '').lower():
        score += 0.25

    token_hits = sum(1 for t in tags if t and t in topic_blob)
    score += min(0.45, token_hits * 0.12)

    category = (template.get('category') or '').lower()
    if 'trend' in topic_blob and category in {'promo', 'news'}:
        score += 0.12
    if 'explain' in topic_blob and category in {'edu', 'minimal'}:
        score += 0.12
    if 'market' in topic_blob and 'markets' in tags:
        score += 0.15

    motion = (template.get('motionLevel') or 'none').lower()
    if mood == 'urgent' and motion in {'low', 'medium'}:
        score += 0.1
    if mood in {'calm', 'premium'} and motion == 'none':
        score += 0.08

    return round(min(1.0, score), 3)


def recommend_background_templates(topic_text: str, mood: str, audience: str, limit: int = 3) -> list[dict[str, Any]]:
    templates = [
        t for t in _load_background_templates()
        if str(t.get('status', 'approved')).lower() == 'approved' and float(t.get('readabilityScore') or 0.85) >= 0.7
    ]
    ranked = []
    for t in templates:
        ranked.append({
            'template': t,
            'score': _score_background_template(t, topic_text=topic_text, mood=mood, audience=audience),
        })
    ranked.sort(key=lambda x: x['score'], reverse=True)
    out = []
    for row in ranked[: max(1, limit)]:
        tpl = row['template']
        out.append({
            'id': tpl.get('id'),
            'name': tpl.get('name'),
            'tier': tpl.get('tier'),
            'category': tpl.get('category'),
            'mood': tpl.get('mood'),
            'assetType': tpl.get('assetType'),
            'motionLevel': tpl.get('motionLevel'),
            'platformVariants': tpl.get('platformVariants', {}),
            'score': row['score'],
        })
    return out


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


def _voice_dna(workspace_id: str, style: str) -> dict[str, float | str]:
    seed = hashlib.sha256(f"{workspace_id}:{style}".encode('utf-8')).hexdigest()
    a = int(seed[0:8], 16) / 0xFFFFFFFF
    b = int(seed[8:16], 16) / 0xFFFFFFFF
    c = int(seed[16:24], 16) / 0xFFFFFFFF
    return {
        'seed': seed[:12],
        'style': style,
        'pace': round(0.9 + a * 0.35, 3),
        'energy': round(0.45 + b * 0.45, 3),
        'pause': round(0.1 + c * 0.25, 3),
    }


def ensure_workspace_identity(session: Session, workspace_id: str, user_id: str, user_email: str, min_role: str = 'viewer') -> None:
    ts = now_utc()

    ws = session.exec(select(Workspace).where(Workspace.id == workspace_id)).first()
    if not ws:
        ws = Workspace(id=workspace_id, name='Default Workspace', plan_tier='starter', owner_user_id=user_id, created_at=ts)
        session.add(ws)

    # Bootstrap workspace allowed corporate domains from env once, then enforce from DB setting.
    allowed_stmt = select(WorkspaceSetting).where(
        WorkspaceSetting.workspace_id == workspace_id,
        WorkspaceSetting.key == 'auth.allowed_domains',
    )
    allowed_row = session.exec(allowed_stmt).first()
    if not allowed_row:
        env_domains = [d.strip().lower() for d in os.getenv('CORP_ALLOWED_DOMAINS', '').split(',') if d.strip()]
        if env_domains:
            allowed_row = WorkspaceSetting(
                id=str(uuid4()),
                workspace_id=workspace_id,
                key='auth.allowed_domains',
                value_json=json.dumps(env_domains),
                created_at=ts,
                updated_at=ts,
            )
            session.add(allowed_row)

    acct_type = 'personal'
    acct_row = session.exec(
        select(WorkspaceSetting).where(
            WorkspaceSetting.workspace_id == workspace_id,
            WorkspaceSetting.key == 'account.type',
        )
    ).first()
    if acct_row and acct_row.value_json:
        try:
            v = json.loads(acct_row.value_json)
            acct_type = str(v or 'personal').strip().lower()
        except Exception:
            acct_type = 'personal'

    if acct_type == 'corporate':
        require_corporate_email_domain(session, workspace_id, user_email)

    u = session.get(User, user_id)
    if not u:
        u = User(id=user_id, email=user_email, email_verified=True, created_at=ts)
        session.add(u)
    else:
        u.email = user_email
        u.email_verified = True
        session.add(u)

    m = session.exec(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
    ).first()
    if not m:
        m = WorkspaceMembership(
            id=str(uuid4()),
            workspace_id=workspace_id,
            user_id=user_id,
            role='owner',
            status='active',
            created_at=ts,
        )
        session.add(m)

    session.commit()
    require_workspace_role(session, workspace_id=workspace_id, min_role=min_role, user_id=user_id)


def parse_iso(ts: str) -> datetime:
    normalized = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_idempotency_key(channel: str, content_item_id: str, publish_at_iso: str) -> str:
    return "%s:%s:%s" % (channel, content_item_id, publish_at_iso)


def estimate_text_cost_usd(model: dict, text: str) -> tuple[float, int, int]:
    # Approximation: 4 chars/token; split 65/35 input/output.
    chars = max(1, len(text or ''))
    approx_tokens = int(chars / 4)
    input_tokens = int(approx_tokens * 0.65)
    output_tokens = max(1, approx_tokens - input_tokens)
    cost = estimate_text_cost_with_registry(model, input_tokens=input_tokens, output_tokens=output_tokens)
    return cost, input_tokens, output_tokens


def _clean_text(v: str) -> str:
    s = unescape(v or '')
    s = re.sub(r'<[^>]+>', ' ', s)
    s = ' '.join(s.split())
    return s.strip()


def _soft_limit(text: str, limit: int = 300) -> str:
    t = (text or '').strip()
    if len(t) <= limit:
        return t

    # Prefer ending on a complete sentence to avoid awkward cut-offs.
    window = t[:limit]
    last_stop = max(window.rfind('. '), window.rfind('? '), window.rfind('! '))
    if last_stop > int(limit * 0.55):
        return window[: last_stop + 1].strip()

    cut = window.rsplit(' ', 1)[0].strip()
    return cut


def _cleanup_caption_text(text: str) -> str:
    t = _clean_text(text or '')
    # Remove awkward scare quotes and quote artifacts.
    t = t.replace('“', '"').replace('”', '"').replace("'", "")
    t = re.sub(r'"([A-Za-z\- ]{1,24})"', r'\1', t)

    # Normalize sentence spacing.
    t = re.sub(r'\s+', ' ', t).strip()

    # Deduplicate near-identical adjacent sentence starts.
    parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', t) if p.strip()]
    kept: list[str] = []
    seen_prefixes: set[str] = set()
    for p in parts:
        prefix = ' '.join(p.lower().split()[:6])
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)
        kept.append(p)

    return ' '.join(kept).strip()


def fetch_research_brief(query: str, max_results: int = 4) -> list[str]:
    token = os.getenv('BRAVE_API_KEY', '').strip()
    if not token or not query.strip():
        return []

    try:
        url = f"https://api.search.brave.com/res/v1/web/search?q={quote_plus(query)}&count={max_results}"
        req = Request(url, headers={
            'Accept': 'application/json',
            'X-Subscription-Token': token,
            'User-Agent': 'DemandOrchestrator/1.0',
        })
        with urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
        results = ((payload or {}).get('web') or {}).get('results') or []
        bullets: list[str] = []
        for r in results[:max_results]:
            title = _clean_text(r.get('title') or '')
            desc = _clean_text(r.get('description') or '')
            line = ' — '.join([p for p in [title, desc] if p])
            if line:
                bullets.append(' '.join(line.split())[:160])
        return bullets
    except Exception:
        return []


def draft_with_llm(topic: str, source_text: str, research: list[str], model: dict) -> str | None:
    provider = (model.get('provider') or '').strip().lower()
    model_id = (model.get('id') or '').split(':', 1)[-1]

    # Support low-cost providers for draft generation.
    if provider not in {'openai', 'openrouter'}:
        return None

    if provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY', '').strip()
    else:
        api_key = os.getenv('OPENROUTER_API_KEY', '').strip()

    if not api_key or not model_id:
        return None

    research_block = '\n'.join([f"- {r}" for r in (research or [])[:4]]) or '- No external research available'
    banned = [
        'clarity vs volume',
        'optimize for attention',
        'game changer',
        'leverage',
        'synergy',
        '"trapped"',
    ]
    prompt = (
        "Purpose: Write insightful social media drafts for X that are specific, useful, and thought-provoking.\n"
        "Audience: operators/founders/parents depending on topic context.\n"
        "Constraints:\n"
        "- Use concrete topic details from source/research.\n"
        "- Take a clear stance (not neutral summary).\n"
        "- No generic business jargon.\n"
        "- No hashtags, no emojis.\n"
        "- Exactly 4 short lines: context, implication, practical action, pointed question.\n"
        "- Keep total length under 260 characters so output never cuts off.\n"
        "- Each line must add new information (no repetition).\n"
        "- Line 2 must begin with one of: 'The real issue is', 'What matters most is', or 'The mistake clubs make is'.\n"
        f"- Never use these phrases: {', '.join(banned)}.\n\n"
        f"Topic: {topic}\n"
        f"Source notes: {source_text[:260]}\n"
        f"Research signals:\n{research_block}\n"
    )

    try:
        payload = {
            'model': model_id,
            'messages': [
                {'role': 'system', 'content': 'You write concise, topic-specific X drafts with zero fluff.'},
                {'role': 'user', 'content': prompt},
            ],
            'max_tokens': 220,
            'temperature': 0.4,
        }

        if provider == 'openrouter':
            data = _json_post(
                'https://openrouter.ai/api/v1/chat/completions',
                payload,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'HTTP-Referer': 'https://demandorchestrator.ai',
                    'X-Title': 'DemandOrchestrator',
                },
            )
        else:
            data = _json_post(
                'https://api.openai.com/v1/chat/completions',
                payload,
                headers={'Authorization': f'Bearer {api_key}'},
            )

        choices = data.get('choices') or []
        text = ''
        if choices:
            text = (((choices[0] or {}).get('message') or {}).get('content') or '').strip()

        text = _cleanup_caption_text(text)
        text = _soft_limit(text, 280)
        if not text:
            return None

        low = text.lower()
        if any(p in low for p in banned):
            return None

        return text
    except Exception:
        return None


def compose_caption_for_channel(
    channel: str,
    title_seed: str,
    body_seed: str,
    variant: int,
    guidance: str | None = None,
    research: list[str] | None = None,
    llm_caption: str | None = None,
) -> str:
    c = (channel or 'x').lower().strip()
    base = _clean_text(body_seed or title_seed or '')
    topic = _clean_text(title_seed or 'Topic')

    if c == 'linkedin':
      text = (
        f"{topic}: what changed, why it matters, and what to do next.\n\n"
        f"Key point: {base[:120]}\n\n"
        "Practical move: publish a clear team update with one action owners can take today.\n\n"
        "What are you seeing on the ground?"
      )
      return _soft_limit(_cleanup_caption_text(text), 520)

    if c == 'instagram':
      text = (
        f"{topic}\n\n"
        f"Context: {base[:95]}\n"
        "Visual direction: clean speaking-head + on-screen text for the 3 key takeaways.\n\n"
        "Caption CTA: Comment ‘guide’ and I’ll share the framework."
      )
      return _soft_limit(_cleanup_caption_text(text), 420)

    if c in {'tiktok', 'youtube', 'youtube_shorts'}:
      mode = 'avatar'
      m = re.search(r'\[video_mode:([^\]]+)\]', base.lower())
      if m:
          mode = m.group(1).strip()

      if mode == 'cinematic':
          text = (
            f"HOOK (0-3s): \"{topic} just changed the playbook.\"\n"
            f"VOICEOVER (25-40s): {base[:125]}\n"
            "SCENES: cinematic b-roll, contextual closeups, motion text overlays, final emotional beat.\n"
            "CTA: End with one high-stakes question viewers can’t ignore."
          )
      elif mode == 'faceless':
          text = (
            f"HOOK TEXT: {topic} in 30 seconds.\n"
            f"SCRIPT: {base[:125]}\n"
            "FORMAT: faceless explainer, kinetic captions, icon overlays, stock/b-roll support.\n"
            "CTA: Ask for comments with one specific follow-up question."
          )
      else:
          text = (
            f"HOOK (0-3s): \"{topic} is changing faster than most people realize.\"\n"
            f"SCRIPT (20-40s): {base[:130]}\n"
            "SHOT LIST: close-up opener, cutaway to bullet list, direct CTA to camera.\n"
            "CTA: Ask viewers the one question they still have."
          )

      return _soft_limit(_cleanup_caption_text(text), 520)

    return compose_x_caption(
        title_seed=title_seed,
        body_seed=body_seed,
        variant=variant,
        guidance=guidance,
        research=research,
        llm_caption=llm_caption,
    )


def compose_x_caption(title_seed: str, body_seed: str, variant: int, guidance: str | None = None, research: list[str] | None = None, llm_caption: str | None = None) -> str:
    if llm_caption and llm_caption.strip():
        return _soft_limit(_cleanup_caption_text(llm_caption), 280)

    lead = _clean_text(title_seed or 'New update')
    seed = _clean_text(body_seed or lead)
    research = research or []

    def short_topic(s: str) -> str:
        base = s.strip().rstrip('.!?')
        words = base.split()
        return ' '.join(words[:8]) if words else 'this update'

    topic = short_topic(lead)

    # Build topic-specific anchor phrases from source/research.
    body_lower = seed.lower()
    research_blob = ' '.join(research).lower()

    detail_a = 'timeline changes'
    detail_b = 'team placement impact'
    detail_c = 'player development path'

    if 'tryout' in body_lower or 'tryout' in research_blob:
        detail_a = 'tryout timeline changes'
    elif 'age' in body_lower or 'school-year' in body_lower or 'school year' in body_lower:
        detail_a = 'age-group timeline changes'

    if 'roster' in body_lower or 'placement' in body_lower:
        detail_b = 'roster placement impact'

    if 'development' in body_lower:
        detail_c = 'development pathway changes'

    source_line = _clean_text(research[0]) if research else ''
    source_hint = ''
    if source_line:
        source_hint = _soft_limit(source_line, 72)

    context_options = [
        f"{topic} is a major shift for families and clubs.",
        f"{topic} will change how parents and teams plan this season.",
        f"{topic} affects decisions families and coaches make right now.",
    ]
    matters_options = [
        f"Families need clear guidance on {detail_a}, {detail_b}, and {detail_c}.",
        f"Without specifics on {detail_a} and {detail_b}, confusion grows fast.",
        f"Trust goes up when clubs explain {detail_a} and {detail_c} in plain language.",
    ]
    action_options = [
        f"Publish one concise update covering {detail_a}, {detail_b}, and {detail_c}.",
        f"Send a parent FAQ this week with concrete answers on {detail_a} and {detail_b}.",
        f"Have every coach repeat the same 3 points: {detail_a}, {detail_b}, {detail_c}.",
    ]
    question_options = [
        f"What question about {detail_a} are families asking most?",
        f"Where is confusion highest right now: {detail_a} or {detail_b}?",
        f"What part of {detail_c} still needs a clearer explanation?",
    ]

    i = (variant - 1) % 3
    context = context_options[i]
    matters = matters_options[i]
    question = question_options[i]

    base = "\n\n".join([context, matters])
    suffix = f"\n\n{question}"
    max_total = 280
    room_for_action = max(48, max_total - len(base) - len(suffix) - 4)
    action = _soft_limit(action_options[i], room_for_action)

    lines = [context, matters, action]
    if source_hint:
        lines.append(f"Source cue: {source_hint}")
    lines.append(question)

    caption = "\n\n".join(lines)
    if guidance:
        caption += f"\n\nContext: {_clean_text(guidance)[:36]}"

    return _soft_limit(caption, max_total)


class CreateSourceRequest(BaseModel):
    workspaceId: str
    type: Literal["csv", "url"]
    rawPayload: str


class CreateSourceResponse(BaseModel):
    id: str
    status: Literal["pending", "normalized", "failed"]


class NormalizeSourceResponse(BaseModel):
    sourceId: str
    status: Literal["pending", "normalized", "failed"]
    itemsCreated: int


class GenerateContentRequest(BaseModel):
    workspaceId: str
    sourceItemId: str
    channels: list[str] = Field(min_length=1)
    variantCount: int = Field(default=1, ge=1, le=10)


class FacelessBatchGenerateRequest(BaseModel):
    workspaceId: str = 'default'
    niche: str
    audience: str
    goal: str = 'leads'
    cadence: str = 'daily'
    template: str = 'cinematic'
    voiceStyle: str = 'authority'
    preferredMood: str = 'premium'
    platform: str = 'vertical_9_16'
    sources: list[str] = Field(default_factory=list)
    batchSize: int = Field(default=10, ge=1, le=20)


class BackgroundRecommendationsRequest(BaseModel):
    workspaceId: str = 'default'
    topic: str
    audience: str = ''
    mood: str = 'premium'
    limit: int = Field(default=3, ge=1, le=10)


class BackgroundTemplateIngestRequest(BaseModel):
    id: str
    name: str
    tier: str = 'free'
    category: str = 'minimal'
    tags: list[str] = Field(default_factory=list)
    mood: str = 'premium'
    motionLevel: str = 'none'
    assetType: str = 'image'
    platformVariants: dict[str, str] = Field(default_factory=dict)
    readabilityScore: float = Field(default=0.85, ge=0.0, le=1.0)
    provenance: dict[str, Any] = Field(default_factory=dict)


class UpdateContentRequest(BaseModel):
    title: Optional[str] = None
    hook: Optional[str] = None
    caption: Optional[str] = None


class RegenerateContentRequest(BaseModel):
    guidance: Optional[str] = None


class ApproveContentResponse(BaseModel):
    id: str
    status: Literal["approved"]


class ScheduleRequest(BaseModel):
    contentItemId: str
    publishAt: str
    timezone: str = "America/New_York"


class ScheduleResponse(BaseModel):
    id: str
    status: Literal["scheduled"]


class PublishRunResponse(BaseModel):
    processed: int
    succeeded: int
    failed: int


class DashboardResponse(BaseModel):
    draft: int
    approved: int
    scheduled: int
    published: int
    failed: int
    recentPublishes: list[dict[str, Any]]


@router.post("/sources", response_model=CreateSourceResponse, status_code=201)
def create_source(
    payload: CreateSourceRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    ts = now_utc()
    ensure_workspace_identity(session, payload.workspaceId, user_id, user_email, min_role='editor')

    ws = session.get(MVPWorkspace, payload.workspaceId)
    if not ws:
        ws = MVPWorkspace(id=payload.workspaceId, name="MVP Workspace", created_at=ts)
        session.add(ws)

    src = MVPSource(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        type=payload.type,
        raw_payload=payload.rawPayload,
        status="pending",
        created_at=ts,
        updated_at=ts,
    )
    session.add(src)
    session.commit()

    return {"id": src.id, "status": src.status}


@router.post("/sources/{source_id}/normalize", response_model=NormalizeSourceResponse)
def normalize_source(
    source_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    src = session.get(MVPSource, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="source not found")
    ensure_workspace_identity(session, src.workspace_id, user_id, user_email, min_role='editor')

    existing = session.exec(select(MVPSourceItem).where(MVPSourceItem.source_id == source_id)).all()
    if existing:
        return {"sourceId": source_id, "status": "normalized", "itemsCreated": len(existing)}

    created = 0
    if src.type == "csv":
        try:
            reader = csv.DictReader(io.StringIO(src.raw_payload))
            for row in reader:
                item = MVPSourceItem(
                    id=str(uuid4()),
                    source_id=source_id,
                    external_ref=row.get("id") or row.get("sku"),
                    title=row.get("title") or row.get("name"),
                    body=row.get("body") or row.get("description"),
                    metadata_json=json.dumps(row),
                    created_at=now_utc(),
                )
                session.add(item)
                created += 1
        except Exception as e:
            src.status = "failed"
            src.error = str(e)
            src.updated_at = now_utc()
            session.add(src)
            session.commit()
            raise HTTPException(status_code=400, detail="csv normalize failed: %s" % str(e))
    else:
        item = MVPSourceItem(
            id=str(uuid4()),
            source_id=source_id,
            external_ref=src.raw_payload,
            title="Imported URL",
            body=src.raw_payload,
            metadata_json=json.dumps({"url": src.raw_payload}),
            created_at=now_utc(),
        )
        session.add(item)
        created = 1

    src.status = "normalized"
    src.updated_at = now_utc()
    session.add(src)
    session.commit()

    return {"sourceId": source_id, "status": "normalized", "itemsCreated": created}


@router.post("/content/generate")
def generate_content(
    payload: GenerateContentRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    ensure_workspace_identity(session, payload.workspaceId, user_id, user_email, min_role='editor')
    source_item = session.get(MVPSourceItem, payload.sourceItemId)
    if not source_item:
        raise HTTPException(status_code=404, detail="source item not found")

    prefs = get_workspace_prefs(payload.workspaceId)
    mode = prefs.get('mode', 'auto')
    text_override = (prefs.get('overrides') or {}).get('text') if mode == 'advanced' else None

    title_seed = source_item.title or "Untitled"
    body_seed = source_item.body or ""
    research_query = f"{title_seed}. {body_seed}"[:280]
    research_brief = fetch_research_brief(research_query, max_results=4)
    created_items = []
    guardrail_warnings = []

    for channel in payload.channels:
        chosen = pick_model(capability='text', task_tag='draft', preference='speed', override_model_id=text_override)
        model_id = chosen.get('id', 'internal:stub-text')

        sample_caption = compose_caption_for_channel(
            channel=channel,
            title_seed=title_seed,
            body_seed=body_seed,
            variant=1,
            research=research_brief,
        )
        est_single, _, _ = estimate_text_cost_usd(chosen, sample_caption)
        projected_channel_cost = est_single * payload.variantCount
        guard = evaluate_generation_guardrail(
            session=session,
            workspace_id=payload.workspaceId,
            model=chosen,
            projected_cost=projected_channel_cost,
            mode=mode,
        )
        beta_permissive = os.getenv('DO_BETA_PERMISSIVE_GENERATION', 'true').strip().lower() == 'true'
        if not guard.get('allowed', False):
            if beta_permissive:
                guardrail_warnings.append(f"BETA_BYPASS: {guard.get('reason', 'generation guardrail blocked request')}")
            else:
                raise HTTPException(status_code=402, detail=guard)
        if guard.get('warning'):
            guardrail_warnings.append(guard['warning'])

        for variant in range(1, payload.variantCount + 1):
            llm_caption = draft_with_llm(
                topic=title_seed,
                source_text=body_seed,
                research=research_brief,
                model=chosen,
            )
            if channel in {'tiktok', 'youtube', 'youtube_shorts'}:
                llm_caption = None
            caption = compose_caption_for_channel(
                channel=channel,
                title_seed=title_seed,
                body_seed=body_seed,
                variant=variant,
                research=research_brief,
                llm_caption=llm_caption,
            )
            item = MVPContentItem(
                id=str(uuid4()),
                workspace_id=payload.workspaceId,
                source_item_id=payload.sourceItemId,
                channel=channel,
                title="%s v%s" % (title_seed, variant),
                hook="%s: angle %s" % (title_seed, variant),
                caption=caption,
                variant_no=variant,
                status="draft",
                created_at=now_utc(),
                updated_at=now_utc(),
            )
            session.add(item)

            est_cost, input_tokens, output_tokens = estimate_text_cost_usd(chosen, caption)
            if MVPGenerationCostEvent is not None:
                cost_evt = MVPGenerationCostEvent(
                    id=str(uuid4()),
                    workspace_id=payload.workspaceId,
                    capability='text',
                    model_id=model_id,
                    provider=chosen.get('provider', 'unknown'),
                    estimated_cost_usd=est_cost,
                    metadata_json=json.dumps({
                        'channel': channel,
                        'variant': variant,
                        'contentItemId': item.id,
                        'inputTokensEst': input_tokens,
                        'outputTokensEst': output_tokens,
                        'pricing': chosen.get('pricing', {}),
                        'plan': guard.get('plan'),
                    }),
                    created_at=now_utc(),
                )
                session.add(cost_evt)

            created_items.append({
                "id": item.id,
                "status": "draft",
                "channel": channel,
                "model": model_id,
                "provider": chosen.get('provider'),
                "estimatedCostUsd": est_cost,
            })

    session.commit()
    return {"contentItems": created_items, "mode": mode, "warnings": list(dict.fromkeys(guardrail_warnings))}


@router.get('/video/background-templates')
def list_background_templates(
    tier: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    mood: Optional[str] = Query(default=None),
    includePending: bool = Query(default=False),
):
    rows = _load_background_templates()
    out = []
    for row in rows:
        status = str(row.get('status', 'approved')).lower()
        if not includePending and status != 'approved':
            continue
        if tier and str(row.get('tier', '')).lower() != tier.lower():
            continue
        if category and str(row.get('category', '')).lower() != category.lower():
            continue
        if mood and str(row.get('mood', '')).lower() != mood.lower():
            continue
        out.append(row)
    return {'count': len(out), 'items': out}


@router.post('/video/background-templates/ingest', status_code=201)
def ingest_background_template(payload: BackgroundTemplateIngestRequest):
    rows = _load_background_templates()
    incoming_id = payload.id.strip()
    if not incoming_id:
        raise HTTPException(status_code=400, detail='id required')

    existing = next((r for r in rows if str(r.get('id')) == incoming_id), None)
    if existing:
        raise HTTPException(status_code=409, detail='template id already exists')

    required_variants = {'vertical_9_16', 'square_1_1', 'landscape_16_9'}
    missing_variants = [k for k in required_variants if not str((payload.platformVariants or {}).get(k) or '').strip()]
    if missing_variants:
        raise HTTPException(status_code=400, detail=f'missing platform variants: {", ".join(missing_variants)}')

    prov = payload.provenance or {}
    source = str(prov.get('source') or '').strip()
    license_type = str(prov.get('licenseType') or '').strip().lower()
    license_ref = str(prov.get('licenseRef') or '').strip()
    allowed_license = {'commercial', 'royalty_free', 'owned', 'custom_contract'}
    if not source or not license_type or not license_ref:
        raise HTTPException(status_code=400, detail='provenance requires source, licenseType, and licenseRef')
    if license_type not in allowed_license:
        raise HTTPException(status_code=400, detail='licenseType invalid; use commercial|royalty_free|owned|custom_contract')

    row = {
        'id': incoming_id,
        'name': payload.name.strip() or incoming_id,
        'tier': payload.tier,
        'category': payload.category,
        'tags': payload.tags,
        'mood': payload.mood,
        'motionLevel': payload.motionLevel,
        'assetType': payload.assetType,
        'platformVariants': payload.platformVariants,
        'readabilityScore': payload.readabilityScore,
        'provenance': {
            'source': source,
            'licenseType': license_type,
            'licenseRef': license_ref,
            'creator': str(prov.get('creator') or '').strip(),
            'costUsd': float(prov.get('costUsd') or 0.0),
        },
        'status': 'pending_review',
        'createdAt': now_iso(),
        'updatedAt': now_iso(),
    }
    rows.append(row)
    _save_background_templates(rows)
    return {'ok': True, 'item': row}


@router.post('/video/background-templates/{template_id}/approve')
def approve_background_template(template_id: str):
    rows = _load_background_templates()
    found = None
    for r in rows:
        if str(r.get('id')) == template_id:
            prov = r.get('provenance') or {}
            if not str(prov.get('source') or '').strip() or not str(prov.get('licenseRef') or '').strip():
                raise HTTPException(status_code=400, detail='cannot approve without provenance source + licenseRef')
            if float(r.get('readabilityScore') or 0.0) < 0.7:
                raise HTTPException(status_code=400, detail='cannot approve: readabilityScore below 0.7')
            r['status'] = 'approved'
            r['updatedAt'] = now_iso()
            found = r
            break
    if not found:
        raise HTTPException(status_code=404, detail='template not found')
    _save_background_templates(rows)
    return {'ok': True, 'item': found}


@router.post('/video/background-recommendations')
def video_background_recommendations(payload: BackgroundRecommendationsRequest):
    recs = recommend_background_templates(
        topic_text=payload.topic,
        mood=payload.mood,
        audience=payload.audience,
        limit=payload.limit,
    )
    return {
        'workspaceId': payload.workspaceId,
        'count': len(recs),
        'items': recs,
    }


@router.post('/faceless/batch/generate')
def generate_faceless_batch(
    payload: FacelessBatchGenerateRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    ensure_workspace_identity(session, payload.workspaceId, user_id, user_email, min_role='editor')

    base_topic = f"{payload.niche} for {payload.audience}".strip()
    active_sources = payload.sources or ['firstParty']
    voice_dna = _voice_dna(payload.workspaceId, payload.voiceStyle)
    batch_background_recs = recommend_background_templates(
        topic_text=base_topic,
        mood=payload.preferredMood,
        audience=payload.audience,
        limit=3,
    )
    out = []

    for i in range(payload.batchSize):
        variant = i + 1
        chosen = pick_model_with_policy(capability='text', task_tag='draft', preference='speed')

        hook = f"Most {payload.audience} miss this about {payload.niche}."
        angle = f"Use {active_sources[i % len(active_sources)]} signal to frame a {payload.template} narrative."
        script = (
            f"[0-2s] {hook}\\n"
            f"[3-12s] Problem: execution gap around {payload.niche}.\\n"
            f"[13-24s] Angle: {angle}\\n"
            f"[25-35s] CTA: {payload.goal} via one clear next step."
        )

        hook_score = min(0.95, 0.62 + ((variant % 5) * 0.07))
        clarity_score = min(0.95, 0.64 + ((variant % 4) * 0.06))
        narrative_score = min(0.95, 0.63 + ((variant % 3) * 0.08))
        cta_fit_score = min(0.95, 0.62 + ((variant % 5) * 0.05))
        policy_safety_score = 0.95
        visual_beatmap_score = min(0.95, 0.65 + ((variant % 4) * 0.06))
        render_readiness = round(
            0.22 * hook_score
            + 0.18 * clarity_score
            + 0.2 * narrative_score
            + 0.12 * cta_fit_score
            + 0.13 * policy_safety_score
            + 0.15 * visual_beatmap_score,
            3,
        )

        video_choice = pick_model_with_policy(
            capability='video',
            task_tag='faceless_video_render',
            preference='quality',
            scores={
                'hook_score': hook_score,
                'clarity_score': clarity_score,
                'narrative_score': narrative_score,
                'cta_fit_score': cta_fit_score,
                'policy_safety_score': policy_safety_score,
                'visual_beatmap_score': visual_beatmap_score,
                'render_readiness': render_readiness,
            },
        )

        lane = 'premium_render' if video_choice.get('id') != 'internal:gate-blocked' else 'intelligence'

        out.append({
            'rank': variant,
            'title': f"{payload.template.title()} · {payload.niche} · #{variant}",
            'hook': hook,
            'script': script,
            'lane': lane,
            'scores': {
                'hook_score': round(hook_score, 3),
                'clarity_score': round(clarity_score, 3),
                'narrative_score': round(narrative_score, 3),
                'cta_fit_score': round(cta_fit_score, 3),
                'policy_safety_score': policy_safety_score,
                'visual_beatmap_score': round(visual_beatmap_score, 3),
                'render_readiness': render_readiness,
            },
            'textModel': {
                'id': chosen.get('id'),
                'provider': chosen.get('provider'),
                'decision': chosen.get('_decision'),
            },
            'videoModel': {
                'id': video_choice.get('id'),
                'provider': video_choice.get('provider'),
                'decision': video_choice.get('_decision'),
            },
            'sourceCue': active_sources[i % len(active_sources)],
            'createdAt': now_iso(),
            'workspaceId': payload.workspaceId,
            'goal': payload.goal,
            'cadence': payload.cadence,
            'topic': base_topic,
            'voiceDna': voice_dna,
            'backgroundRecommendations': batch_background_recs,
            'selectedBackgroundTemplateId': (batch_background_recs[0]['id'] if batch_background_recs else None),
            'platform': payload.platform,
        })

    out.sort(key=lambda x: x['scores']['render_readiness'], reverse=True)
    for i, r in enumerate(out):
        r['rank'] = i + 1

    return {
        'workspaceId': payload.workspaceId,
        'voiceDna': voice_dna,
        'backgroundRecommendations': batch_background_recs,
        'count': len(out),
        'items': out,
        'promotedCount': len([x for x in out if x['lane'] == 'premium_render']),
    }


@router.patch("/content/{content_id}")
def update_content(
    content_id: str,
    payload: UpdateContentRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    item = session.get(MVPContentItem, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="content not found")
    ensure_workspace_identity(session, item.workspace_id, user_id, user_email, min_role='editor')

    if payload.title is not None:
        item.title = payload.title
    if payload.hook is not None:
        item.hook = payload.hook
    if payload.caption is not None:
        item.caption = payload.caption
    item.updated_at = now_utc()

    session.add(item)
    session.commit()
    session.refresh(item)

    return {
        "id": item.id,
        "workspaceId": item.workspace_id,
        "sourceItemId": item.source_item_id,
        "channel": item.channel,
        "title": item.title,
        "hook": item.hook,
        "caption": item.caption,
        "variantNo": item.variant_no,
        "status": item.status,
        "providerPostId": item.provider_post_id,
        "createdAt": item.created_at.isoformat(),
        "updatedAt": item.updated_at.isoformat(),
    }


@router.post("/content/{content_id}/regenerate")
def regenerate_content(
    content_id: str,
    payload: RegenerateContentRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    item = session.get(MVPContentItem, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="content not found")
    ensure_workspace_identity(session, item.workspace_id, user_id, user_email, min_role='editor')

    guidance = (payload.guidance or '').strip()
    item.hook = (item.hook or item.title or "New angle") + " (regen)"
    research_query = f"{item.title or ''}. {guidance or item.caption or ''}"[:280]
    research_brief = fetch_research_brief(research_query, max_results=3)
    chosen = pick_model(capability='text', task_tag='draft', preference='speed')
    llm_caption = draft_with_llm(
        topic=item.title or 'New idea',
        source_text=guidance or item.caption or item.hook or '',
        research=research_brief,
        model=chosen,
    )
    item.caption = compose_caption_for_channel(
        channel=item.channel,
        title_seed=item.title or 'New idea',
        body_seed=guidance or item.caption or item.hook or '',
        variant=max(1, item.variant_no or 1),
        guidance=guidance or None,
        research=research_brief,
        llm_caption=llm_caption,
    )
    item.status = "draft"
    item.updated_at = now_utc()
    session.add(item)
    session.commit()
    session.refresh(item)
    return _content_out(item)


@router.post("/content/{content_id}/approve", response_model=ApproveContentResponse)
def approve_content(
    content_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    item = session.get(MVPContentItem, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="content not found")
    ensure_workspace_identity(session, item.workspace_id, user_id, user_email, min_role='publisher')
    item.status = "approved"
    item.updated_at = now_utc()
    session.add(item)
    session.commit()
    return {"id": content_id, "status": "approved"}


@router.post("/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    payload: ScheduleRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    item = session.get(MVPContentItem, payload.contentItemId)
    if not item:
        raise HTTPException(status_code=404, detail="content not found")
    ensure_workspace_identity(session, item.workspace_id, user_id, user_email, min_role='publisher')
    acct = workspace_account_type(session, item.workspace_id)
    if acct == 'corporate' and item.status != "approved":
        raise HTTPException(status_code=400, detail="content must be approved before scheduling")
    if acct == 'personal' and item.status == 'draft':
        item.status = 'approved'

    existing = session.exec(
        select(MVPSchedule).where(
            MVPSchedule.content_item_id == payload.contentItemId,
            MVPSchedule.publish_at == parse_iso(payload.publishAt),
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="duplicate schedule")

    schedule = MVPSchedule(
        id=str(uuid4()),
        content_item_id=payload.contentItemId,
        publish_at=parse_iso(payload.publishAt),
        timezone=payload.timezone,
        status="scheduled",
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    item.status = "scheduled"
    item.updated_at = now_utc()

    session.add(schedule)
    session.add(item)
    session.commit()

    return {"id": schedule.id, "status": "scheduled"}


def _run_publish_for_schedules(schedules_to_process: list[MVPSchedule], session: Session, actor_user_id: str) -> dict[str, int]:
    processed = 0
    succeeded = 0
    failed = 0

    for sched in schedules_to_process:
        processed += 1
        content = session.get(MVPContentItem, sched.content_item_id)
        if not content:
            sched.status = "failed"
            sched.updated_at = now_utc()
            session.add(sched)
            failed += 1
            continue

        acct = workspace_account_type(session, content.workspace_id)
        if acct == 'corporate' and not _actor_can_publish(content.workspace_id, content.channel, actor_user_id):
            sched.status = "failed"
            content.status = "failed"
            content.last_error = f'publish authorization missing for user {actor_user_id} on channel {content.channel}'
            sched.updated_at = now_utc()
            content.updated_at = now_utc()
            session.add(sched)
            session.add(content)
            failed += 1
            continue

        if content.provider_post_id:
            sched.status = "published"
            sched.updated_at = now_utc()
            session.add(sched)
            continue

        sched.status = "processing"
        sched.updated_at = now_utc()
        session.add(sched)

        idem = build_idempotency_key(content.channel, content.id, sched.publish_at.isoformat())

        prior_attempts = session.exec(
            select(MVPPublishJob.attempt).where(MVPPublishJob.idempotency_key == idem)
        ).all()
        attempt_base = (max(prior_attempts) if prior_attempts else 0)

        ok = False
        last_error = None
        for idx, attempt in enumerate((1, 2, 3), start=1):
            persisted_attempt = attempt_base + idx
            success, provider_resp, provider_error = publish_content(
                {
                    "id": content.id,
                    "channel": content.channel,
                    "title": content.title,
                    "caption": content.caption,
                },
                idem,
                persisted_attempt,
            )
            job = MVPPublishJob(
                id=str(uuid4()),
                schedule_id=sched.id,
                attempt=persisted_attempt,
                idempotency_key=idem,
                status="succeeded" if success else "failed",
                provider_response_json=json.dumps(provider_resp),
                error=None if success else (provider_error or "publish failure"),
                created_at=now_utc(),
                updated_at=now_utc(),
            )
            session.add(job)

            if success:
                ok = True
                content.provider_post_id = provider_resp.get("post_id")
                break
            last_error = provider_error or "publish failure"

        if ok:
            sched.status = "published"
            content.status = "published"
            succeeded += 1
        else:
            sched.status = "failed"
            content.status = "failed"
            content.last_error = last_error
            failed += 1

        sched.updated_at = now_utc()
        content.updated_at = now_utc()
        session.add(sched)
        session.add(content)

    session.commit()
    return {"processed": processed, "succeeded": succeeded, "failed": failed}


@router.post("/publish/run", response_model=PublishRunResponse)
def publish_run(
    workspaceId: str = Query(...),
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    ensure_workspace_identity(session, workspaceId, user_id, user_email, min_role='publisher')
    due_rows = session.exec(
        select(MVPSchedule, MVPContentItem)
        .join(MVPContentItem, MVPContentItem.id == MVPSchedule.content_item_id)
        .where(
            MVPContentItem.workspace_id == workspaceId,
            MVPSchedule.status == "scheduled",
            MVPSchedule.publish_at <= now_utc(),
        )
    ).all()
    due = [sched for sched, _ in due_rows]
    return _run_publish_for_schedules(due, session, user_id)


@router.get("/publish/jobs")
def list_publish_jobs(
    workspaceId: str = Query(...),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
):
    require_feature(session, workspaceId, 'full_audit_log')
    rows = session.exec(
        select(MVPPublishJob, MVPSchedule, MVPContentItem)
        .join(MVPSchedule, MVPSchedule.id == MVPPublishJob.schedule_id)
        .join(MVPContentItem, MVPContentItem.id == MVPSchedule.content_item_id)
        .where(MVPContentItem.workspace_id == workspaceId)
        .order_by(MVPPublishJob.created_at.desc())
        .limit(limit)
    ).all()

    payload = []
    for job, sched, content in rows:
        try:
            provider_resp = json.loads(job.provider_response_json or "{}")
        except Exception:
            provider_resp = {}
        payload.append(
            {
                "job": {
                    "id": job.id,
                    "attempt": job.attempt,
                    "idempotencyKey": job.idempotency_key,
                    "status": job.status,
                    "error": job.error,
                    "createdAt": job.created_at.isoformat(),
                },
                "schedule": _schedule_out(sched),
                "content": _content_out(content),
                "providerResponse": provider_resp,
            }
        )
    return payload


@router.get("/publish/failed")
def list_failed_publishes(
    workspaceId: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    require_feature(session, workspaceId, 'full_audit_log')
    rows = session.exec(
        select(MVPSchedule, MVPContentItem)
        .join(MVPContentItem, MVPContentItem.id == MVPSchedule.content_item_id)
        .where(
            MVPContentItem.workspace_id == workspaceId,
            MVPSchedule.status == "failed",
        )
        .order_by(MVPSchedule.updated_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "schedule": _schedule_out(s),
            "content": _content_out(c),
        }
        for s, c in rows
    ]


@router.post("/publish/retry-failed", response_model=PublishRunResponse)
def retry_failed_publishes(
    workspaceId: str = Query(...),
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    ensure_workspace_identity(session, workspaceId, user_id, user_email, min_role='publisher')
    rows = session.exec(
        select(MVPSchedule, MVPContentItem)
        .join(MVPContentItem, MVPContentItem.id == MVPSchedule.content_item_id)
        .where(
            MVPContentItem.workspace_id == workspaceId,
            MVPSchedule.status == "failed",
        )
        .order_by(MVPSchedule.updated_at.asc())
    ).all()

    failed_schedules = []
    for sched, content in rows:
        sched.status = "scheduled"
        sched.updated_at = now_utc()
        content.status = "scheduled"
        content.updated_at = now_utc()
        session.add(sched)
        session.add(content)
        failed_schedules.append(sched)

    session.commit()
    return _run_publish_for_schedules(failed_schedules, session, user_id)


@router.post("/publish/retry/{schedule_id}", response_model=PublishRunResponse)
def retry_one_failed_publish(
    schedule_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
    user_email: str = Depends(actor_user_email),
):
    sched = session.get(MVPSchedule, schedule_id)
    if not sched:
        raise HTTPException(status_code=404, detail="schedule not found")
    if sched.status != "failed":
        raise HTTPException(status_code=400, detail="schedule is not failed")

    content = session.get(MVPContentItem, sched.content_item_id)
    if not content:
        raise HTTPException(status_code=404, detail="content not found")
    ensure_workspace_identity(session, content.workspace_id, user_id, user_email, min_role='publisher')

    sched.status = "scheduled"
    sched.updated_at = now_utc()
    content.status = "scheduled"
    content.updated_at = now_utc()
    session.add(sched)
    session.add(content)
    session.commit()

    return _run_publish_for_schedules([sched], session, user_id)


def _source_out(src: MVPSource) -> dict[str, Any]:
    return {
        "id": src.id,
        "workspaceId": src.workspace_id,
        "type": src.type,
        "rawPayload": src.raw_payload,
        "status": src.status,
        "error": src.error,
        "createdAt": src.created_at.isoformat(),
        "updatedAt": src.updated_at.isoformat(),
    }


def _source_item_out(item: MVPSourceItem) -> dict[str, Any]:
    try:
        metadata = json.loads(item.metadata_json or "{}")
    except Exception:
        metadata = {}
    return {
        "id": item.id,
        "sourceId": item.source_id,
        "externalRef": item.external_ref,
        "title": item.title,
        "body": item.body,
        "metadata": metadata,
        "createdAt": item.created_at.isoformat(),
    }


def _content_out(item: MVPContentItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "workspaceId": item.workspace_id,
        "sourceItemId": item.source_item_id,
        "channel": item.channel,
        "title": item.title,
        "hook": item.hook,
        "caption": item.caption,
        "variantNo": item.variant_no,
        "status": item.status,
        "providerPostId": item.provider_post_id,
        "lastError": item.last_error,
        "createdAt": item.created_at.isoformat(),
        "updatedAt": item.updated_at.isoformat(),
    }


def _schedule_out(s: MVPSchedule) -> dict[str, Any]:
    return {
        "id": s.id,
        "contentItemId": s.content_item_id,
        "publishAt": s.publish_at.isoformat(),
        "timezone": s.timezone,
        "status": s.status,
        "createdAt": s.created_at.isoformat(),
        "updatedAt": s.updated_at.isoformat(),
    }


@router.get("/sources")
def list_sources(
    workspaceId: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(MVPSource)
        .where(MVPSource.workspace_id == workspaceId)
        .order_by(MVPSource.created_at.desc())
        .limit(limit)
    ).all()
    return [_source_out(r) for r in rows]


@router.get("/sources/{source_id}")
def get_source(source_id: str, session: Session = Depends(get_session)):
    src = session.get(MVPSource, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="source not found")
    return _source_out(src)


@router.get("/sources/{source_id}/items")
def list_source_items(source_id: str, session: Session = Depends(get_session)):
    src = session.get(MVPSource, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="source not found")
    rows = session.exec(
        select(MVPSourceItem)
        .where(MVPSourceItem.source_id == source_id)
        .order_by(MVPSourceItem.created_at.asc())
    ).all()
    return [_source_item_out(r) for r in rows]


@router.get("/content")
def list_content(
    workspaceId: str = Query(...),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
):
    q = select(MVPContentItem).where(MVPContentItem.workspace_id == workspaceId)
    if status:
        q = q.where(MVPContentItem.status == status)
    rows = session.exec(q.order_by(MVPContentItem.created_at.desc()).limit(limit)).all()
    return [_content_out(r) for r in rows]


@router.get("/content/{content_id}")
def get_content(content_id: str, session: Session = Depends(get_session)):
    item = session.get(MVPContentItem, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="content not found")
    return _content_out(item)


@router.get("/schedules")
def list_schedules(
    workspaceId: str = Query(...),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
):
    q = (
        select(MVPSchedule, MVPContentItem)
        .join(MVPContentItem, MVPContentItem.id == MVPSchedule.content_item_id)
        .where(MVPContentItem.workspace_id == workspaceId)
    )
    if status:
        q = q.where(MVPSchedule.status == status)

    rows = session.exec(q.order_by(MVPSchedule.publish_at.asc()).limit(limit)).all()
    return [
        {
            **_schedule_out(s),
            "channel": c.channel,
            "contentStatus": c.status,
        }
        for s, c in rows
    ]


@router.get("/schedules/{schedule_id}")
def get_schedule(schedule_id: str, session: Session = Depends(get_session)):
    s = session.get(MVPSchedule, schedule_id)
    if not s:
        raise HTTPException(status_code=404, detail="schedule not found")
    return _schedule_out(s)


@router.get("/costs/summary")
def costs_summary(
    workspaceId: str = Query(...),
    limit: int = Query(default=500, ge=1, le=5000),
    session: Session = Depends(get_session),
):
    if MVPGenerationCostEvent is None:
        return {
            'workspaceId': workspaceId,
            'events': 0,
            'estimatedCostUsd': 0.0,
            'byModel': {},
            'byCapability': {},
        }

    rows = session.exec(
        select(MVPGenerationCostEvent)
        .where(MVPGenerationCostEvent.workspace_id == workspaceId)
        .order_by(MVPGenerationCostEvent.created_at.desc())
        .limit(limit)
    ).all()

    total = round(sum(r.estimated_cost_usd for r in rows), 6)
    by_model: dict[str, float] = {}
    by_cap: dict[str, float] = {}
    for r in rows:
        by_model[r.model_id] = round(by_model.get(r.model_id, 0.0) + r.estimated_cost_usd, 6)
        by_cap[r.capability] = round(by_cap.get(r.capability, 0.0) + r.estimated_cost_usd, 6)

    return {
        'workspaceId': workspaceId,
        'events': len(rows),
        'estimatedCostUsd': total,
        'byModel': by_model,
        'byCapability': by_cap,
    }


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(workspaceId: str = Query(...), session: Session = Depends(get_session)):
    # Dashboard is available to all, but audit-heavy recent publishes are enterprise-only detail.
    scoped = session.exec(select(MVPContentItem).where(MVPContentItem.workspace_id == workspaceId)).all()

    def count(status: str) -> int:
        return sum(1 for c in scoped if c.status == status)

    recent = [c for c in scoped if c.provider_post_id]
    recent.sort(key=lambda x: x.updated_at, reverse=True)

    acct = workspace_account_type(session, workspaceId)
    recent_payload = [
        {
            "contentItemId": c.id,
            "channel": c.channel,
            "publishedAt": c.updated_at.isoformat(),
            "providerPostId": c.provider_post_id if acct == 'corporate' else None,
        }
        for c in recent[:10]
    ]

    return {
        "draft": count("draft"),
        "approved": count("approved"),
        "scheduled": count("scheduled"),
        "published": count("published"),
        "failed": count("failed"),
        "recentPublishes": recent_payload,
    }

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models.mvp import MVPSource, MVPSourceItem, MVPWorkspace
from app.services.apify_client import ApifyClient
from app.services.x_client import reply_to_tweet
from app.services.model_registry import ModelRegistry
from app.services.model_preferences import get_workspace_prefs, set_workspace_prefs
from app.services.entitlements import require_feature

CONNECTIONS_FILE = Path(__file__).resolve().parents[2] / 'integrations_connections.json'


def _load_connections() -> dict[str, Any]:
    if not CONNECTIONS_FILE.exists():
        return {'workspaces': {}}
    try:
        return json.loads(CONNECTIONS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {'workspaces': {}}


def _save_connections(data: dict[str, Any]) -> None:
    CONNECTIONS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _oauth_cfg(platform: str) -> dict[str, str]:
    p = platform.upper()
    return {
        'client_id': os.getenv(f'{p}_CLIENT_ID', '').strip(),
        'client_secret': os.getenv(f'{p}_CLIENT_SECRET', '').strip(),
        'auth_url': os.getenv(f'{p}_AUTH_URL', '').strip(),
        'token_url': os.getenv(f'{p}_TOKEN_URL', '').strip(),
        'redirect_uri': os.getenv(f'{p}_REDIRECT_URI', '').strip(),
        'scope': os.getenv(f'{p}_SCOPE', 'post:write').strip(),
    }

router = APIRouter(prefix='/integrations', tags=['integrations'])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class ApifyRunRequest(BaseModel):
    actorId: str
    input: Optional[dict[str, Any]] = None
    build: Optional[str] = None
    memoryMbytes: Optional[int] = None
    timeoutSecs: Optional[int] = None


class ApifyImportRequest(BaseModel):
    workspaceId: str = 'default'
    limit: int = 100


def _normalize_record(rec: dict[str, Any]) -> tuple[str, str, str, str]:
    external_ref = (
        rec.get('id')
        or rec.get('url')
        or rec.get('postUrl')
        or rec.get('tweetId')
        or rec.get('itemUrl')
        or str(uuid4())
    )

    body = (
        rec.get('text')
        or rec.get('caption')
        or rec.get('content')
        or rec.get('snippet')
        or rec.get('description')
        or rec.get('headline')
        or rec.get('summary')
        or json.dumps(rec, ensure_ascii=False)
    )

    title = (
        rec.get('title')
        or rec.get('name')
        or rec.get('headline')
        or rec.get('author')
        or rec.get('query')
    )

    if not title:
        # Derive a meaningful topic from content instead of generic placeholders.
        compact = ' '.join(str(body).split())
        title = compact[:120] if compact else 'Signal item'

    metadata_json = json.dumps(rec, ensure_ascii=False)
    return str(external_ref), str(title)[:280], str(body)[:4000], metadata_json


@router.get('/apify/health')
def apify_health():
    client = ApifyClient()
    return {
        'configured': client.configured(),
        'baseUrl': client.base_url,
        'timeoutSeconds': client.timeout,
    }


@router.get('/heygen/health')
def heygen_health():
    configured = bool((os.getenv('HEYGEN_API_KEY') or '').strip())
    base = (os.getenv('HEYGEN_API_BASE') or 'https://api.heygen.com').rstrip('/')
    return {
        'configured': configured,
        'baseUrl': base,
        'avatarId': (os.getenv('HEYGEN_AVATAR_ID') or '').strip() or None,
        'voiceId': (os.getenv('HEYGEN_VOICE_ID') or '').strip() or None,
    }


@router.get('/models')
def list_models(capability: Optional[str] = Query(default=None)):
    reg = ModelRegistry()
    models = reg.models()
    if capability:
        models = [m for m in models if capability in (m.get('capabilities') or []) and m.get('status') == 'active']
    return {'items': models}


class ModelPrefsRequest(BaseModel):
    workspaceId: str = 'default'
    mode: str = 'auto'
    textModelId: Optional[str] = None
    imageModelId: Optional[str] = None
    videoModelId: Optional[str] = None


class AccountConnectRequest(BaseModel):
    workspaceId: str = 'default'
    platform: str


class AccountDisconnectRequest(BaseModel):
    workspaceId: str = 'default'
    platform: str


class LinkedInOrgSelectRequest(BaseModel):
    workspaceId: str = 'default'
    orgUrn: str


class PublishAuthorizationRequest(BaseModel):
    workspaceId: str = 'default'
    platform: str
    userId: str


@router.get('/models/preferences')
def get_model_preferences(workspaceId: str = Query(default='default')):
    prefs = get_workspace_prefs(workspaceId)
    return {'workspaceId': workspaceId, **prefs}


@router.post('/models/preferences')
def save_model_preferences(payload: ModelPrefsRequest):
    overrides = {
        'text': payload.textModelId or '',
        'image': payload.imageModelId or '',
        'video': payload.videoModelId or '',
    }
    saved = set_workspace_prefs(payload.workspaceId, payload.mode, overrides)
    return {'workspaceId': payload.workspaceId, **saved}


@router.get('/accounts')
def list_accounts(workspaceId: str = Query(default='default')):
    data = _load_connections()
    ws = (data.get('workspaces') or {}).get(workspaceId) or {}
    platforms = ws.get('platforms') or {}

    publish_auth = ws.get('publish_authorizations') or {}
    out = []
    for p in ['x', 'linkedin', 'instagram', 'youtube']:
        row = platforms.get(p) or {}
        out.append({
            'platform': p,
            'connected': bool(row.get('connected')),
            'connectedAt': row.get('connectedAt'),
            'scope': row.get('scope') or 'post:write',
            'authorizedPublishers': publish_auth.get(p) or [],
        })
    return {'workspaceId': workspaceId, 'items': out}


@router.post('/accounts/connect')
def connect_account(payload: AccountConnectRequest):
    platform = (payload.platform or '').strip().lower()
    if platform not in {'x', 'linkedin', 'instagram', 'youtube'}:
        raise HTTPException(status_code=400, detail='unsupported platform')

    cfg = _oauth_cfg(platform)
    if not cfg.get('client_id') or not cfg.get('auth_url') or not cfg.get('redirect_uri'):
        raise HTTPException(status_code=400, detail=f'{platform} oauth not configured')

    state = str(uuid4())
    data = _load_connections()
    ws = (data.setdefault('workspaces', {})).setdefault(payload.workspaceId, {})
    ws.setdefault('oauth_state', {})[platform] = state
    _save_connections(data)

    query = urlencode({
        'client_id': cfg['client_id'],
        'redirect_uri': cfg['redirect_uri'],
        'response_type': 'code',
        'scope': cfg['scope'],
        'state': state,
    })
    return {
        'workspaceId': payload.workspaceId,
        'platform': platform,
        'connected': False,
        'authUrl': f"{cfg['auth_url']}?{query}",
    }


@router.get('/oauth/{platform}/callback')
def oauth_callback(platform: str, code: str = Query(default=''), state: str = Query(default=''), workspaceId: str = Query(default='default')):
    platform = (platform or '').strip().lower()
    if platform not in {'x', 'linkedin', 'instagram', 'youtube'}:
        raise HTTPException(status_code=400, detail='unsupported platform')

    data = _load_connections()
    ws = (data.setdefault('workspaces', {})).setdefault(workspaceId, {})
    expected = ((ws.get('oauth_state') or {}).get(platform) or '').strip()
    if not expected or state != expected:
        raise HTTPException(status_code=400, detail='invalid oauth state')

    # Token exchange wiring point (provider-specific). For now we persist the auth code receipt.
    platforms = ws.setdefault('platforms', {})
    platforms[platform] = {
        'connected': True,
        'connectedAt': now_utc().isoformat(),
        'scope': _oauth_cfg(platform).get('scope') or 'post:write',
        'authMode': 'oauth-code-received',
        'codePresent': bool(code),
    }
    _save_connections(data)

    web_base = os.getenv('WEB_APP_BASE', 'http://127.0.0.1:3000').rstrip('/')
    return RedirectResponse(url=f'{web_base}/onboarding?started=1&phase=setup&step=0&oauth=connected&platform={platform}')


@router.get('/linkedin/orgs')
def list_linkedin_orgs(workspaceId: str = Query(default='default'), session: Session = Depends(get_session)):
    # Corporate feature: org-level LinkedIn controls.
    require_feature(session, workspaceId, 'publish_authorization_matrix')
    # v1 stub list; replace with LinkedIn org lookup using token.
    data = _load_connections()
    ws = (data.get('workspaces') or {}).get(workspaceId) or {}
    selected = ((ws.get('linkedin') or {}).get('selectedOrgUrn') or '').strip()
    items = [
        {'orgUrn': 'urn:li:organization:107479374', 'name': 'Demand Orchestrator'},
    ]
    return {'workspaceId': workspaceId, 'items': items, 'selectedOrgUrn': selected}


@router.post('/linkedin/orgs/select')
def select_linkedin_org(payload: LinkedInOrgSelectRequest, session: Session = Depends(get_session)):
    require_feature(session, payload.workspaceId, 'publish_authorization_matrix')
    if not payload.orgUrn.startswith('urn:li:organization:'):
        raise HTTPException(status_code=400, detail='invalid organization urn')

    data = _load_connections()
    ws = (data.setdefault('workspaces', {})).setdefault(payload.workspaceId, {})
    l = ws.setdefault('linkedin', {})
    l['selectedOrgUrn'] = payload.orgUrn
    _save_connections(data)
    return {'workspaceId': payload.workspaceId, 'selectedOrgUrn': payload.orgUrn}


@router.post('/accounts/authorize-publisher')
def authorize_publisher(payload: PublishAuthorizationRequest, session: Session = Depends(get_session)):
    require_feature(session, payload.workspaceId, 'publish_authorization_matrix')
    platform = (payload.platform or '').strip().lower()
    if platform not in {'x', 'linkedin', 'instagram', 'youtube'}:
        raise HTTPException(status_code=400, detail='unsupported platform')
    user_id = (payload.userId or '').strip()
    if not user_id:
        raise HTTPException(status_code=400, detail='userId required')

    data = _load_connections()
    ws = (data.setdefault('workspaces', {})).setdefault(payload.workspaceId, {})
    authz = ws.setdefault('publish_authorizations', {})
    allowed = set(str(x).strip() for x in (authz.get(platform) or []) if str(x).strip())
    allowed.add(user_id)
    authz[platform] = sorted(allowed)
    _save_connections(data)

    return {'workspaceId': payload.workspaceId, 'platform': platform, 'authorizedPublishers': authz[platform]}


@router.post('/accounts/disconnect')
def disconnect_account(payload: AccountDisconnectRequest):
    platform = (payload.platform or '').strip().lower()
    if platform not in {'x', 'linkedin', 'instagram', 'youtube'}:
        raise HTTPException(status_code=400, detail='unsupported platform')

    data = _load_connections()
    ws = (data.setdefault('workspaces', {})).setdefault(payload.workspaceId, {})
    platforms = ws.setdefault('platforms', {})
    platforms[platform] = {'connected': False, 'connectedAt': None, 'scope': 'post:write'}
    _save_connections(data)

    return {'workspaceId': payload.workspaceId, 'platform': platform, 'connected': False}


@router.post('/apify/run')
def apify_run(payload: ApifyRunRequest):
    client = ApifyClient()
    if not client.configured():
        raise HTTPException(status_code=400, detail='APIFY_TOKEN is not configured')

    try:
        run = client.run_actor(
            actor_id=payload.actorId,
            actor_input=payload.input,
            build=payload.build,
            memory_mbytes=payload.memoryMbytes,
            timeout_secs=payload.timeoutSecs,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        'runId': run.get('id'),
        'status': run.get('status'),
        'actorId': run.get('actId'),
        'defaultDatasetId': run.get('defaultDatasetId'),
        'startedAt': run.get('startedAt'),
    }


@router.get('/apify/runs/{run_id}')
def apify_run_status(run_id: str):
    client = ApifyClient()
    if not client.configured():
        raise HTTPException(status_code=400, detail='APIFY_TOKEN is not configured')

    try:
        run = client.get_run(run_id)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        'runId': run.get('id'),
        'status': run.get('status'),
        'statusMessage': run.get('statusMessage'),
        'defaultDatasetId': run.get('defaultDatasetId'),
        'startedAt': run.get('startedAt'),
        'finishedAt': run.get('finishedAt'),
    }


@router.post('/apify/import/{run_id}')
def apify_import_run(
    run_id: str,
    payload: ApifyImportRequest,
    session: Session = Depends(get_session),
):
    client = ApifyClient()
    if not client.configured():
        raise HTTPException(status_code=400, detail='APIFY_TOKEN is not configured')

    try:
        run = client.get_run(run_id)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    dataset_id = run.get('defaultDatasetId')
    if not dataset_id:
        raise HTTPException(status_code=400, detail='Run has no default dataset')

    if payload.limit < 1 or payload.limit > 1000:
        raise HTTPException(status_code=400, detail='limit must be between 1 and 1000')

    try:
        items = client.get_dataset_items(dataset_id, limit=payload.limit)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    ts = now_utc()
    ws = session.get(MVPWorkspace, payload.workspaceId)
    if not ws:
        ws = MVPWorkspace(id=payload.workspaceId, name='MVP Workspace', created_at=ts)
        session.add(ws)

    src = MVPSource(
        id=str(uuid4()),
        workspace_id=payload.workspaceId,
        type='apify',
        raw_payload=json.dumps(
            {
                'runId': run_id,
                'datasetId': dataset_id,
                'actorId': run.get('actId'),
                'itemCount': len(items),
            },
            ensure_ascii=False,
        ),
        status='normalized',
        created_at=ts,
        updated_at=ts,
    )
    session.add(src)

    created = 0
    for rec in items:
        if not isinstance(rec, dict):
            continue
        external_ref, title, body, metadata_json = _normalize_record(rec)
        item = MVPSourceItem(
            id=str(uuid4()),
            source_id=src.id,
            external_ref=external_ref,
            title=title,
            body=body,
            metadata_json=metadata_json,
            created_at=now_utc(),
        )
        session.add(item)
        created += 1

    session.commit()

    return {
        'ok': True,
        'workspaceId': payload.workspaceId,
        'sourceId': src.id,
        'runId': run_id,
        'datasetId': dataset_id,
        'importedItems': created,
    }


def _x_queue_path() -> Path:
    return Path(os.getenv('X_REPLY_DRAFT_QUEUE_PATH', './x_reply_drafts.ndjson'))


def _load_x_draft_queue() -> list[dict[str, Any]]:
    p = _x_queue_path()
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def _save_x_draft_queue(rows: list[dict[str, Any]]) -> None:
    p = _x_queue_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


class XSendDraftRequest(BaseModel):
    dryRun: bool = False


@router.get('/x/drafts')
def x_list_drafts(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    rows = _load_x_draft_queue()
    if status:
        rows = [r for r in rows if str(r.get('status', 'draft')) == status]
    rows.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return {
        'items': rows[:limit],
        'count': len(rows),
        'queuePath': str(_x_queue_path()),
        'autoReplyEnabled': os.getenv('X_AUTO_REPLY_ENABLED', 'false').lower() == 'true',
    }


@router.post('/x/drafts/{tweet_id}/send')
def x_send_draft(tweet_id: str, payload: XSendDraftRequest):
    rows = _load_x_draft_queue()
    target = None
    for r in rows:
        if str(r.get('tweet_id', '')) == tweet_id:
            target = r
            break

    if not target:
        raise HTTPException(status_code=404, detail='draft not found')

    if payload.dryRun:
        target['status'] = 'approved'
        target['approved_at'] = now_utc().isoformat()
        _save_x_draft_queue(rows)
        return {'ok': True, 'tweet_id': tweet_id, 'dryRun': True, 'status': target['status']}

    text = str(target.get('draft') or '').strip()
    if not text:
        raise HTTPException(status_code=400, detail='draft text empty')

    try:
        resp = reply_to_tweet(tweet_id=tweet_id, text=text)
    except RuntimeError as e:
        target['status'] = 'error'
        target['last_error'] = str(e)
        target['updated_at'] = now_utc().isoformat()
        _save_x_draft_queue(rows)
        raise HTTPException(status_code=502, detail=str(e))

    target['status'] = 'sent'
    target['sent_at'] = now_utc().isoformat()
    target['provider_response'] = resp
    target['updated_at'] = now_utc().isoformat()
    _save_x_draft_queue(rows)

    return {
        'ok': True,
        'tweet_id': tweet_id,
        'status': 'sent',
        'provider': resp,
    }

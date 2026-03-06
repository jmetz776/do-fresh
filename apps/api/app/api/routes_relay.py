from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.services.channel_publishers import publish_by_channel

router = APIRouter(prefix="/relay", tags=["relay"])


class RelayPublishRequest(BaseModel):
    idempotency_key: str
    attempt: int
    channel: str
    title: Optional[str] = None
    caption: str


@router.get('/health')
def relay_health():
    mode = os.getenv('PUBLISH_PROVIDER_MODE', 'stub').strip().lower()
    return {
        'mode': mode,
        'webhookConfigured': bool(os.getenv('PUBLISH_PROVIDER_URL', '').strip()),
        'relayTokenRequired': bool(os.getenv('RELAY_SHARED_TOKEN', '').strip()),
        'xConfigured': bool(os.getenv('X_BEARER_TOKEN', '').strip()),
        'linkedinConfigured': bool(os.getenv('LINKEDIN_ACCESS_TOKEN', '').strip()) and bool(os.getenv('LINKEDIN_AUTHOR_URN', '').strip()),
    }


@router.post('/publish')
def relay_publish(payload: RelayPublishRequest, authorization: Optional[str] = Header(default=None)):
    shared = os.getenv('RELAY_SHARED_TOKEN', '').strip()
    if shared:
        expected = f"Bearer {shared}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail='unauthorized relay call')

    ok, provider_resp, err = publish_by_channel(payload.channel, payload.title or '', payload.caption)
    if not ok:
        raise HTTPException(status_code=502, detail={"error": err, "provider": provider_resp})

    return {
        "ok": True,
        "post_id": provider_resp.get("post_id"),
        "post_url": provider_resp.get("post_url"),
        "provider": provider_resp,
        "idempotency_key": payload.idempotency_key,
        "attempt": payload.attempt,
    }

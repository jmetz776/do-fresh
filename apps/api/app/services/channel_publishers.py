from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional
from urllib import request, error
from urllib.parse import quote


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _http_json(url: str, method: str, payload: dict[str, Any], headers: Optional[dict[str, str]] = None) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)

    try:
        with request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8") if resp else "{}"
            return resp.status, json.loads(raw) if raw else {}
    except error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            parsed = json.loads(raw) if raw else {"error": str(e)}
        except Exception:
            parsed = {"error": raw or str(e)}
        return e.code, parsed


def publish_to_x(caption: str) -> tuple[bool, dict[str, Any], Optional[str]]:
    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        return False, {"provider": "x", "timestamp": _now_iso()}, "X_BEARER_TOKEN missing"

    status, resp = _http_json(
        "https://api.x.com/2/tweets",
        "POST",
        {"text": caption[:280]},
        headers={"Authorization": f"Bearer {token}"},
    )

    post_id = ((resp or {}).get("data") or {}).get("id")
    if status in (200, 201) and post_id:
        return True, {
            "provider": "x",
            "timestamp": _now_iso(),
            "post_id": post_id,
            "post_url": f"https://x.com/i/web/status/{post_id}",
            "raw": resp,
        }, None

    return False, {"provider": "x", "timestamp": _now_iso(), "raw": resp}, f"x publish failed ({status})"


def publish_to_linkedin(caption: str) -> tuple[bool, dict[str, Any], Optional[str]]:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    author = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()  # urn:li:person:... or urn:li:organization:...
    if not token or not author:
        return False, {"provider": "linkedin", "timestamp": _now_iso()}, "LINKEDIN_ACCESS_TOKEN or LINKEDIN_AUTHOR_URN missing"

    payload = {
        "author": author,
        "commentary": caption,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    status, resp = _http_json(
        "https://api.linkedin.com/rest/posts",
        "POST",
        payload,
        headers={
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": "202401",
            "X-Restli-Protocol-Version": "2.0.0",
        },
    )

    post_urn = resp.get("id") if isinstance(resp, dict) else None
    if status in (200, 201) and post_urn:
        encoded = quote(post_urn, safe="")
        return True, {
            "provider": "linkedin",
            "timestamp": _now_iso(),
            "post_id": post_urn,
            "post_url": f"https://www.linkedin.com/feed/update/{encoded}",
            "raw": resp,
        }, None

    return False, {"provider": "linkedin", "timestamp": _now_iso(), "raw": resp}, f"linkedin publish failed ({status})"


def publish_by_channel(channel: str, title: str, caption: str) -> tuple[bool, dict[str, Any], Optional[str]]:
    c = (channel or "").strip().lower()
    full_text = caption if not title else f"{title}\n\n{caption}"

    if c in ("x", "twitter"):
        return publish_to_x(full_text)
    if c in ("linkedin", "li"):
        return publish_to_linkedin(full_text)

    return False, {"provider": "relay", "timestamp": _now_iso()}, f"unsupported channel: {channel}"

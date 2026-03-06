from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional
from urllib import request


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def publish_content(content: dict[str, Any], idempotency_key: str, attempt: int) -> tuple[bool, dict[str, Any], Optional[str]]:
    mode = os.getenv("PUBLISH_PROVIDER_MODE", "stub").lower()
    channel = (content.get("channel") or "").lower().strip()

    # Hard safety rail: never publish to LinkedIn unless explicitly enabled for org-only mode.
    if channel == "linkedin":
        allow_linkedin = os.getenv("ALLOW_LINKEDIN_PUBLISH", "false").lower() == "true"
        allowed_org = os.getenv("LINKEDIN_ALLOWED_ORG_URN", "").strip()
        if not allow_linkedin or not allowed_org:
            return False, {
                "provider": mode,
                "timestamp": now_iso(),
                "channel": channel,
            }, "LinkedIn publishing locked. Set ALLOW_LINKEDIN_PUBLISH=true and LINKEDIN_ALLOWED_ORG_URN to enable org-only posting."

    if mode == "webhook":
        endpoint = os.getenv("PUBLISH_PROVIDER_URL", "").strip()
        token = os.getenv("PUBLISH_PROVIDER_TOKEN", "").strip()
        if not endpoint:
            return False, {"provider": "webhook", "timestamp": now_iso()}, "PUBLISH_PROVIDER_URL missing"

        payload = {
            "idempotency_key": idempotency_key,
            "attempt": attempt,
            "channel": content.get("channel"),
            "title": content.get("title"),
            "caption": content.get("caption"),
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(endpoint, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")

        try:
            with request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8") if resp else "{}"
                parsed = json.loads(raw) if raw else {}
                post_id = parsed.get("post_id") or parsed.get("id")
                ok = bool(post_id)
                return ok, {"provider": "webhook", "timestamp": now_iso(), "post_id": post_id, "raw": parsed}, None if ok else "webhook missing post_id"
        except Exception as e:
            return False, {"provider": "webhook", "timestamp": now_iso()}, str(e)

    if mode == "mock-social":
        forced_fail = "[FAIL]" in (content.get("caption") or "")
        if forced_fail:
            return False, {"provider": "mock-social", "timestamp": now_iso(), "post_id": None}, "mock-social rejected content"
        channel = (content.get("channel") or "generic").lower()
        post_id = f"{channel}-{idempotency_key}-{attempt}"
        return True, {
            "provider": "mock-social",
            "timestamp": now_iso(),
            "post_id": post_id,
            "post_url": f"https://social.local/{channel}/posts/{post_id}",
        }, None

    # default: stub
    forced_fail = "[FAIL]" in (content.get("caption") or "")
    if forced_fail:
        return False, {"provider": "stub", "timestamp": now_iso(), "post_id": None}, "stub publish failure"
    return True, {"provider": "stub", "timestamp": now_iso(), "post_id": f"stub-{idempotency_key}-{attempt}"}, None

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request

BASE = "https://api.x.com/2"


def _pct(v: str) -> str:
    return parse.quote(str(v), safe='~')


def _oauth1_auth_header(method: str, url: str) -> str:
    consumer_key = os.getenv('X_CONSUMER_KEY', '').strip()
    consumer_secret = os.getenv('X_CONSUMER_SECRET', '').strip()
    access_token = os.getenv('X_ACCESS_TOKEN', '').strip()
    access_secret = os.getenv('X_ACCESS_TOKEN_SECRET', '').strip()
    if not (consumer_key and consumer_secret and access_token and access_secret):
        raise SystemExit('Missing OAuth1 credentials (X_CONSUMER_KEY/SECRET, X_ACCESS_TOKEN/SECRET)')

    nonce = secrets.token_hex(16)
    ts = str(int(time.time()))
    params = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': nonce,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': ts,
        'oauth_token': access_token,
        'oauth_version': '1.0',
    }

    base_params = '&'.join(f"{_pct(k)}={_pct(params[k])}" for k in sorted(params))
    base_string = '&'.join([method.upper(), _pct(url), _pct(base_params)])
    signing_key = f"{_pct(consumer_secret)}&{_pct(access_secret)}"

    sig = hmac.new(signing_key.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha1).digest()
    params['oauth_signature'] = base64.b64encode(sig).decode('utf-8')

    hdr = 'OAuth ' + ', '.join([
        f'{k}="{_pct(params[k])}"'
        for k in ['oauth_consumer_key', 'oauth_nonce', 'oauth_signature', 'oauth_signature_method', 'oauth_timestamp', 'oauth_token', 'oauth_version']
    ])
    return hdr


def _bearer_headers() -> dict[str, str]:
    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing X_BEARER_TOKEN")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _http_json(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, method=method)
    for k, v in _bearer_headers().items():
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


def post_tweet(text: str) -> dict:
    url = f"{BASE}/tweets"
    body = json.dumps({'text': text}).encode('utf-8')
    headers = {
        'Authorization': _oauth1_auth_header('POST', url),
        'Content-Type': 'application/json',
    }
    req = request.Request(url, data=body, method='POST')
    for k, v in headers.items():
        req.add_header(k, v)

    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode('utf-8') if resp else '{}'
            payload = json.loads(raw) if raw else {}
            if resp.status not in (200, 201):
                raise SystemExit(f"post failed ({resp.status}): {payload}")
            return payload
    except error.HTTPError as e:
        raw = e.read().decode('utf-8') if e.fp else ''
        try:
            parsed = json.loads(raw) if raw else {'error': str(e)}
        except Exception:
            parsed = {'error': raw or str(e)}
        raise SystemExit(f"post failed ({e.code}): {parsed}")


def _state_path() -> Path:
    p = os.getenv("X_MENTION_STATE_PATH", "./x_mentions_state.json")
    return Path(p)


def _draft_queue_path() -> Path:
    p = os.getenv("X_REPLY_DRAFT_QUEUE_PATH", "./x_reply_drafts.ndjson")
    return Path(p)


def _load_state() -> dict:
    p = _state_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2))


def fetch_mentions_payload(limit: int = 10) -> dict:
    user_id = os.getenv("X_USER_ID", "").strip()
    if not user_id:
        raise SystemExit("Missing X_USER_ID")

    state = _load_state()
    params = {
        "max_results": str(max(5, min(limit, 100))),
        "tweet.fields": "author_id,created_at,conversation_id",
    }
    if state.get("since_id"):
        params["since_id"] = str(state["since_id"])

    url = f"{BASE}/users/{user_id}/mentions?{parse.urlencode(params)}"
    status, payload = _http_json(url)
    if status != 200:
        raise SystemExit(f"mentions fetch failed ({status}): {payload}")

    data = payload.get("data", [])
    newest = None
    for t in data:
        tid = int(t.get("id", 0))
        newest = max(newest or tid, tid)

    if newest:
        state["since_id"] = str(newest)
        _save_state(state)

    return payload


def fetch_mentions(limit: int = 10) -> None:
    print(json.dumps(fetch_mentions_payload(limit), indent=2))


def draft_reply_templates_from_payload(payload: dict) -> dict:
    tweets = payload.get("data", [])

    drafts = []
    for t in tweets:
        text = (t.get("text") or "").strip().replace("\n", " ")
        drafts.append(
            {
                "tweet_id": t.get("id"),
                "draft": (
                    "Great point. Execution reliability is usually the hidden bottleneck — "
                    "handoffs, approvals, and post-publish follow-through."
                ),
                "context": text[:280],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "draft",
            }
        )

    return {"drafts": drafts}


def draft_reply_templates(input_json_path: str) -> None:
    p = Path(input_json_path)
    payload = json.loads(p.read_text())
    print(json.dumps(draft_reply_templates_from_payload(payload), indent=2))


def run_cycle(limit: int = 20, mentions_input: str | None = None, out_json: str | None = None) -> None:
    if mentions_input:
        payload = json.loads(Path(mentions_input).read_text())
    else:
        payload = fetch_mentions_payload(limit)

    draft_payload = draft_reply_templates_from_payload(payload)

    queue_path = _draft_queue_path()
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    existing_ids = set()
    if queue_path.exists():
        for line in queue_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("tweet_id"):
                    existing_ids.add(str(rec["tweet_id"]))
            except Exception:
                continue

    new_items = []
    for d in draft_payload.get("drafts", []):
        tid = str(d.get("tweet_id") or "")
        if not tid or tid in existing_ids:
            continue
        new_items.append(d)

    if new_items:
        with queue_path.open("a", encoding="utf-8") as f:
            for d in new_items:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")

    summary = {
        "mentions_seen": len(payload.get("data", [])),
        "drafts_generated": len(draft_payload.get("drafts", [])),
        "new_drafts_queued": len(new_items),
        "queue_path": str(queue_path),
        "auto_reply_enabled": os.getenv("X_AUTO_REPLY_ENABLED", "false").lower() == "true",
    }

    if out_json:
        Path(out_json).write_text(json.dumps({"mentions": payload, "drafts": draft_payload, "summary": summary}, indent=2))

    print(json.dumps(summary, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="DemandOrchestrator X assistant")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_post = sub.add_parser("post", help="Post a tweet")
    p_post.add_argument("--text", required=True)

    p_mentions = sub.add_parser("mentions", help="Fetch mentions with since_id state")
    p_mentions.add_argument("--limit", type=int, default=10)

    p_draft = sub.add_parser("draft-replies", help="Generate conservative reply drafts from mentions json")
    p_draft.add_argument("--input", required=True, help="Path to mentions payload json")

    p_cycle = sub.add_parser("run-cycle", help="Fetch mentions + generate draft queue")
    p_cycle.add_argument("--limit", type=int, default=20)
    p_cycle.add_argument("--mentions-input", help="Use existing mentions payload instead of live fetch")
    p_cycle.add_argument("--out-json", help="Optional output file with mentions+drafts+summary")

    args = ap.parse_args()
    if args.cmd == "post":
        print(json.dumps(post_tweet(args.text), indent=2))
    elif args.cmd == "mentions":
        fetch_mentions(args.limit)
    elif args.cmd == "draft-replies":
        draft_reply_templates(args.input)
    elif args.cmd == "run-cycle":
        run_cycle(limit=args.limit, mentions_input=args.mentions_input, out_json=args.out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

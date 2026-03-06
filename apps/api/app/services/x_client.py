from __future__ import annotations

import json
import os
from urllib import error, request

BASE = 'https://api.x.com/2'


def _bearer_headers() -> dict[str, str]:
    token = os.getenv('X_BEARER_TOKEN', '').strip()
    if not token:
        raise RuntimeError('Missing X_BEARER_TOKEN')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


def _http_json(url: str, method: str = 'GET', payload: dict | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=body, method=method)
    for k, v in _bearer_headers().items():
        req.add_header(k, v)

    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode('utf-8') if resp else '{}'
            return resp.status, json.loads(raw) if raw else {}
    except error.HTTPError as e:
        raw = e.read().decode('utf-8') if e.fp else ''
        try:
            parsed = json.loads(raw) if raw else {'error': str(e)}
        except Exception:
            parsed = {'error': raw or str(e)}
        return e.code, parsed


def reply_to_tweet(tweet_id: str, text: str) -> dict:
    payload = {'text': text, 'reply': {'in_reply_to_tweet_id': tweet_id}}
    status, data = _http_json(f'{BASE}/tweets', method='POST', payload=payload)
    if status not in (200, 201):
        raise RuntimeError(f'X reply failed ({status}): {data}')
    return data

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Optional
from uuid import uuid4

from app.services.security_state import is_revoked


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_decode(data: str) -> bytes:
    pad = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + pad).encode('ascii'))


def _secret() -> str:
    return os.getenv('DO_SESSION_SECRET', 'dev-insecure-change-me')


def issue_token(user_id: str, email: str, workspace_id: str, role: str, ttl_seconds: int = 60 * 60 * 12) -> str:
    now = int(time.time())
    payload = {
        'sub': user_id,
        'email': email,
        'workspace_id': workspace_id,
        'role': role,
        'jti': uuid4().hex,
        'iat': now,
        'exp': now + ttl_seconds,
    }
    header = {'alg': 'HS256', 'typ': 'JWT'}

    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    signing_input = f'{header_b64}.{payload_b64}'.encode('ascii')
    sig = hmac.new(_secret().encode('utf-8'), signing_input, hashlib.sha256).digest()
    return f'{header_b64}.{payload_b64}.{_b64url_encode(sig)}'


def verify_token(token: str) -> Optional[dict[str, Any]]:
    try:
        header_b64, payload_b64, sig_b64 = token.split('.', 2)
        signing_input = f'{header_b64}.{payload_b64}'.encode('ascii')
        expected = hmac.new(_secret().encode('utf-8'), signing_input, hashlib.sha256).digest()
        got = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected, got):
            return None

        payload = json.loads(_b64url_decode(payload_b64).decode('utf-8'))
        if int(payload.get('exp', 0)) < int(time.time()):
            return None
        if is_revoked(str(payload.get('jti') or '')):
            return None
        return payload
    except Exception:
        return None

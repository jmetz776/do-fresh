from __future__ import annotations

import json
import os
import time
from typing import Optional

_MEM_RATE: dict[str, list[float]] = {}
_MEM_REVOKED: dict[str, float] = {}


def _redis_client():
    url = os.getenv('REDIS_URL', '').strip()
    if not url:
        return None
    try:
        import redis  # type: ignore

        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def rate_limit_hit(key: str, limit: int, window_seconds: int) -> bool:
    now = time.time()
    r = _redis_client()
    if r:
        bucket = f'rl:{key}'
        try:
            pipe = r.pipeline()
            pipe.zremrangebyscore(bucket, 0, now - window_seconds)
            pipe.zadd(bucket, {str(now): now})
            pipe.zcard(bucket)
            pipe.expire(bucket, window_seconds)
            _, _, count, _ = pipe.execute()
            return int(count) > int(limit)
        except Exception:
            pass

    arr = [t for t in _MEM_RATE.get(key, []) if now - t <= window_seconds]
    arr.append(now)
    _MEM_RATE[key] = arr
    return len(arr) > limit


def clear_rate_limit(key: str) -> None:
    r = _redis_client()
    if r:
        try:
            r.delete(f'rl:{key}')
            return
        except Exception:
            pass
    _MEM_RATE.pop(key, None)


def revoke_jti(jti: str, exp_ts: int) -> None:
    ttl = max(1, int(exp_ts - time.time()))
    r = _redis_client()
    if r:
        try:
            r.setex(f'revoked:{jti}', ttl, '1')
            return
        except Exception:
            pass
    _MEM_REVOKED[jti] = float(exp_ts)


def is_revoked(jti: Optional[str]) -> bool:
    if not jti:
        return True
    r = _redis_client()
    if r:
        try:
            return bool(r.get(f'revoked:{jti}'))
        except Exception:
            pass
    now = time.time()
    expired = [k for k, exp in _MEM_REVOKED.items() if exp < now]
    for k in expired:
        _MEM_REVOKED.pop(k, None)
    return jti in _MEM_REVOKED

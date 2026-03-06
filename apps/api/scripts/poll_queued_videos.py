#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.main import app

OUT = Path('/Users/jaredmetz/.openclaw/workspace/business/demandorchestrator/quality/video-poller-log.jsonl')


def main() -> int:
    c = TestClient(app)
    r = c.post('/v1/consent/video/renders/refresh-queued', params={'workspaceId': 'default', 'limit': 100})
    payload = r.json() if r.status_code == 200 else {'error': r.text}
    row = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'status_code': r.status_code,
        'payload': payload,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(json.dumps({'ok': r.status_code == 200, 'count': payload.get('count') if isinstance(payload, dict) else None}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

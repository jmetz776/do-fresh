#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from urllib import request
import json

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / '.env')


def present(name: str) -> bool:
    return bool(os.getenv(name, '').strip())


def main() -> int:
    checks = {
        'PUBLISH_PROVIDER_MODE': present('PUBLISH_PROVIDER_MODE'),
        'PUBLISH_PROVIDER_URL': present('PUBLISH_PROVIDER_URL'),
        'PUBLISH_PROVIDER_TOKEN': present('PUBLISH_PROVIDER_TOKEN'),
        'RELAY_SHARED_TOKEN': present('RELAY_SHARED_TOKEN'),
        'X_BEARER_TOKEN': present('X_BEARER_TOKEN'),
        'LINKEDIN_ACCESS_TOKEN': present('LINKEDIN_ACCESS_TOKEN'),
        'LINKEDIN_AUTHOR_URN': present('LINKEDIN_AUTHOR_URN'),
    }

    print('Relay credential plumbing check')
    for k, v in checks.items():
        print(f"- {k}: {'OK' if v else 'MISSING'}")

    # Soft validation: expected token pairing
    ptoken = os.getenv('PUBLISH_PROVIDER_TOKEN', '').strip()
    rtoken = os.getenv('RELAY_SHARED_TOKEN', '').strip()
    if ptoken and rtoken and ptoken != rtoken:
        print('! WARNING: PUBLISH_PROVIDER_TOKEN and RELAY_SHARED_TOKEN differ (recommended: match).')

    # Optional local relay health probe
    try:
        with request.urlopen('http://127.0.0.1:8000/relay/health', timeout=4) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
            print(f"- relay health: {payload}")
    except Exception:
        print('- relay health: not reachable (start API to verify runtime wiring)')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

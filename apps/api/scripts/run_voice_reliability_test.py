#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.db import init_db
from app.main import app

ROOT = Path('/Users/jaredmetz/.openclaw/workspace/business/demandorchestrator')
OUT = ROOT / 'quality' / 'voice-reliability-report.json'

SCRIPTS = [
    'Most creators do not have an idea problem. They have an execution problem.',
    'One idea in, channel-ready content out. That is how consistency scales.',
    'If posting feels chaotic, you need a system, not more motivation.',
    'DemandOrchestrator helps teams publish safely and track what drives leads.',
    'Execution discipline beats random content bursts every single time.',
]


def ensure_voice_profile(client: TestClient) -> str:
    # create consent + verification + voice profile quickly for test
    c = client.post('/v1/consent/records', json={
        'workspaceId': 'default',
        'subjectFullName': 'Reliability Test User',
        'subjectEmail': f"reltest-{int(datetime.now().timestamp())}@example.com",
        'consentType': 'voice',
        'scope': {'commercial': True},
        'evidenceUri': 'local://reliability-release.pdf',
    }).json()['id']

    client.post(f'/v1/consent/records/{c}/verify-identity', json={'provider': 'manual', 'status': 'verified', 'score': 1.0})

    vp = client.post('/v1/consent/voice/profiles', json={
        'workspaceId': 'default',
        'consentRecordId': c,
        'provider': 'elevenlabs',
        'providerVoiceId': 'CwhRBWXzGAHq8TQ4Fs17',
        'displayName': 'Reliability Voice',
    })
    vp.raise_for_status()
    return vp.json()['id']


def main() -> int:
    init_db()
    client = TestClient(app)
    voice_profile_id = ensure_voice_profile(client)

    total = 20
    ok = 0
    failed = 0
    render_ids = []

    for i in range(total):
        text = SCRIPTS[i % len(SCRIPTS)] + f' Batch item {i+1}.'
        r = client.post('/v1/consent/voice/renders', json={
            'workspaceId': 'default',
            'voiceProfileId': voice_profile_id,
            'scriptText': text,
        })
        if r.status_code == 200 and r.json().get('status') == 'succeeded':
            ok += 1
            render_ids.append(r.json().get('id'))
        else:
            failed += 1

    failure_rate = (failed / total) * 100.0

    # pull recent renders for latency proxy not available per render currently; rely on success/fail count
    report = {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'total': total,
        'succeeded': ok,
        'failed': failed,
        'failure_rate_pct': round(failure_rate, 2),
        'pass_failure_gate_leq_2pct': failure_rate <= 2.0,
        'render_ids': render_ids,
    }

    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

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

from app.db import init_db
from app.main import app

ROOT = Path('/Users/jaredmetz/.openclaw/workspace/business/demandorchestrator')
OUT = ROOT / 'quality' / 'video-reliability-report.json'

SCRIPTS = [
    'Most creators do not fail from bad ideas. They fail from inconsistent execution.',
    'One system for draft, review, publish, and lead tracking removes chaos.',
    'If your content is inconsistent, your pipeline will be inconsistent too.',
    'DemandOrchestrator turns one idea into channel-ready output in minutes.',
    'Ship better content with approvals and retry-safe publishing built in.',
]


def setup_voice_render(client: TestClient) -> str:
    cr = client.post('/v1/consent/records', json={
        'workspaceId': 'default',
        'subjectFullName': 'Video Reliability User',
        'subjectEmail': f"video-rel-{int(datetime.now().timestamp())}@example.com",
        'consentType': 'both',
        'scope': {'commercial': True},
        'evidenceUri': 'local://video-reliability-release.pdf',
    }).json()['id']

    client.post(f'/v1/consent/records/{cr}/verify-identity', json={'provider': 'manual', 'status': 'verified', 'score': 1.0})

    vp = client.post('/v1/consent/voice/profiles', json={
        'workspaceId': 'default',
        'consentRecordId': cr,
        'provider': 'elevenlabs',
        'providerVoiceId': 'CwhRBWXzGAHq8TQ4Fs17',
        'displayName': 'Reliability Voice',
    }).json()['id']

    vr = client.post('/v1/consent/voice/renders', json={
        'workspaceId': 'default',
        'voiceProfileId': vp,
        'scriptText': 'Approved voice input for video reliability testing.',
    }).json()['id']

    client.post(f'/v1/consent/voice/renders/{vr}/approve')
    return vr


def main() -> int:
    init_db()
    client = TestClient(app)

    total = 10
    created = 0
    immediate_failed = 0
    queued_ids = []

    for i in range(total):
        vr = setup_voice_render(client)
        script = SCRIPTS[i % len(SCRIPTS)] + f' Run {i+1}.'
        r = client.post('/v1/consent/video/renders', json={'workspaceId': 'default', 'voiceRenderId': vr, 'scriptText': script})
        if r.status_code != 200:
            immediate_failed += 1
            continue
        js = r.json()
        created += 1
        if js.get('status') == 'failed':
            immediate_failed += 1
        else:
            queued_ids.append(js.get('id'))

    # Poll queued jobs a few rounds
    final = {'approved': 0, 'succeeded': 0, 'failed': immediate_failed, 'queued': 0}
    per_job = {}
    for rid in queued_ids:
        per_job[rid] = {'status': 'queued'}

    for _ in range(8):
        all_done = True
        for rid in queued_ids:
            if per_job[rid]['status'] in ('failed', 'succeeded', 'approved'):
                continue
            all_done = False
            rf = client.post(f'/v1/consent/video/renders/{rid}/refresh')
            if rf.status_code != 200:
                per_job[rid]['status'] = 'failed'
                per_job[rid]['error'] = f'refresh_http_{rf.status_code}'
                continue
            js = rf.json()
            per_job[rid]['status'] = js.get('status', 'queued')
            per_job[rid]['videoUri'] = js.get('videoUri', '')
        if all_done:
            break
        time.sleep(2)

    for rid, meta in per_job.items():
        st = meta.get('status', 'queued')
        if st == 'approved':
            final['approved'] += 1
        elif st == 'succeeded':
            final['succeeded'] += 1
        elif st == 'failed':
            final['failed'] += 1
        else:
            final['queued'] += 1

    done = final['approved'] + final['succeeded'] + final['failed']
    failure_rate = 0.0 if done == 0 else (final['failed'] / done) * 100.0

    report = {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'total_target': total,
        'created': created,
        'final': final,
        'failure_rate_pct': round(failure_rate, 2),
        'pass_failure_gate_leq_2pct': failure_rate <= 2.0,
        'jobs': per_job,
    }

    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

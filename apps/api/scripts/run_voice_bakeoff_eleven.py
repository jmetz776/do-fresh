#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path
from urllib import request, error

from dotenv import load_dotenv

ROOT = Path('/Users/jaredmetz/.openclaw/workspace/business/demandorchestrator')
INPUTS = ROOT / 'quality' / 'voice-bakeoff-inputs.json'
RESULTS = ROOT / 'quality' / 'voice-bakeoff-results.csv'
AUDIO_DIR = ROOT / 'quality' / 'audio' / 'elevenlabs'


def api_headers(key: str, accept_audio: bool = False) -> dict[str, str]:
    h = {
        'xi-api-key': key,
        'Content-Type': 'application/json',
    }
    if accept_audio:
        h['Accept'] = 'audio/mpeg'
    return h


def http_json(url: str, headers: dict[str, str]) -> dict:
    req = request.Request(url, headers=headers, method='GET')
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def tts(key: str, voice_id: str, text: str) -> tuple[bytes, float]:
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    payload = {
        'text': text,
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {'stability': 0.45, 'similarity_boost': 0.75},
    }
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=data, headers=api_headers(key, accept_audio=True), method='POST')
    t0 = time.perf_counter()
    with request.urlopen(req, timeout=60) as resp:
        blob = resp.read()
    latency = time.perf_counter() - t0
    return blob, latency


def estimate_cost_usd(text: str) -> float:
    # Placeholder estimator until invoice reconciliation by provider character usage.
    # Roughly maps to prior worksheet assumptions.
    chars = max(1, len(text or ''))
    return round((chars / 1000.0) * 0.18, 4)


def main() -> int:
    load_dotenv(ROOT / 'apps' / 'api' / '.env')
    key = (os.getenv('ELEVENLABS_API_KEY') or '').strip()
    if not key:
        raise SystemExit('Missing ELEVENLABS_API_KEY in apps/api/.env')

    voices = http_json('https://api.elevenlabs.io/v1/voices', api_headers(key))
    items = voices.get('voices', [])
    if not items:
        raise SystemExit('No ElevenLabs voices available for this account')
    voice_id = items[0].get('voice_id')
    voice_name = items[0].get('name', 'unknown')

    prompts = json.loads(INPUTS.read_text(encoding='utf-8'))
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for p in prompts:
        sid = p['id']
        tone = p.get('tone', 'neutral')
        text = p['script']
        failed = False
        latency = ''
        cost = ''
        notes = f'voice={voice_name}'
        try:
            audio, lat = tts(key, voice_id, text)
            (AUDIO_DIR / f'{sid}.mp3').write_bytes(audio)
            latency = round(lat, 2)
            cost = estimate_cost_usd(text)
        except error.HTTPError as e:
            failed = True
            notes = f'HTTP {e.code}'
        except Exception as e:
            failed = True
            notes = f'ERR {e}'

        rows.append({
            'provider': 'ElevenLabs',
            'sample_id': sid,
            'tone': tone,
            'naturalness': '',
            'intelligibility': '',
            'emotional_fit': '',
            'pronunciation_accuracy': '',
            'consistency': '',
            'latency_sec': latency,
            'failed': str(failed).lower(),
            'cost_usd': cost,
            'notes': notes,
        })

    # merge/replace eleven rows in results csv
    existing = []
    if RESULTS.exists():
        with RESULTS.open() as f:
            r = csv.DictReader(f)
            existing = [x for x in r if x.get('provider') != 'ElevenLabs']

    fieldnames = ['provider','sample_id','tone','naturalness','intelligibility','emotional_fit','pronunciation_accuracy','consistency','latency_sec','failed','cost_usd','notes']
    with RESULTS.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for x in rows + existing:
            w.writerow(x)

    ok = sum(1 for r in rows if r['failed'] == 'false')
    print(json.dumps({'voice_id': voice_id, 'voice_name': voice_name, 'samples': len(rows), 'ok': ok, 'results_csv': str(RESULTS), 'audio_dir': str(AUDIO_DIR)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

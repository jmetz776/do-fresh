from __future__ import annotations

import json
import os
from urllib import request, error


class ElevenLabsClient:
    def __init__(self):
        self.api_key = (os.getenv('ELEVENLABS_API_KEY') or '').strip()
        self.base = 'https://api.elevenlabs.io/v1'

    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self, accept_audio: bool = False) -> dict[str, str]:
        h = {
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json',
        }
        if accept_audio:
            h['Accept'] = 'audio/mpeg'
        return h

    def text_to_speech(self, voice_id: str, text: str) -> bytes:
        payload = {
            'text': text,
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {'stability': 0.45, 'similarity_boost': 0.75},
        }
        req = request.Request(
            f'{self.base}/text-to-speech/{voice_id}',
            data=json.dumps(payload).encode('utf-8'),
            headers=self._headers(accept_audio=True),
            method='POST',
        )
        try:
            with request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except error.HTTPError as e:
            msg = e.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f'ElevenLabs HTTP {e.code}: {msg[:300]}')

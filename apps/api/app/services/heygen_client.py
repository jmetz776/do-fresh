from __future__ import annotations

import json
import os
from urllib import request, error


class HeyGenClient:
    def __init__(self):
        self.api_key = (os.getenv('HEYGEN_API_KEY') or '').strip()
        self.base = (os.getenv('HEYGEN_API_BASE') or 'https://api.heygen.com').rstrip('/')

    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json',
        }

    def create_video(self, script_text: str, audio_url: str = '', avatar_id: str = '', background_url: str = '') -> dict:
        # Minimal payload scaffold. Adjust exact shape per final HeyGen endpoint contract.
        resolved_avatar_id = avatar_id or (os.getenv('HEYGEN_AVATAR_ID') or '').strip()
        if not resolved_avatar_id:
            raise RuntimeError('HEYGEN_AVATAR_ID missing')

        resolved_voice_id = (os.getenv('HEYGEN_VOICE_ID') or '').strip()
        if audio_url:
            voice_payload = {'type': 'audio', 'audio_url': audio_url}
        else:
            if not resolved_voice_id:
                raise RuntimeError('HEYGEN_VOICE_ID missing for text-to-voice render')
            voice_payload = {
                'type': 'text',
                'voice_id': resolved_voice_id,
                'input_text': script_text,
            }

        video_input = {
            'character': {
                'type': 'avatar',
                'avatar_id': resolved_avatar_id,
            },
            'voice': voice_payload,
        }

        # Apply scene template background when provided.
        if background_url and (background_url.startswith('http://') or background_url.startswith('https://')):
            bg_type = 'video' if background_url.lower().endswith('.mp4') else 'image'
            video_input['background'] = {
                'type': bg_type,
                'url': background_url,
            }

        # Keep payload minimal and explicit to avoid silent renders from conflicting fields.
        payload = {
            'video_inputs': [video_input],
            'dimension': {'width': 1080, 'height': 1920},
        }
        req = request.Request(
            f'{self.base}/v2/video/generate',
            data=json.dumps(payload).encode('utf-8'),
            headers=self._headers(),
            method='POST',
        )
        try:
            with request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except error.HTTPError as e:
            msg = e.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f'HeyGen HTTP {e.code}: {msg[:400]}')

    def create_digital_twin(self, avatar_name: str, training_footage_url: str, consent_video_url: str) -> dict:
        payload = {
            'avatar_name': avatar_name,
            'training_footage_url': training_footage_url,
            'video_consent_url': consent_video_url,
        }
        req = request.Request(
            f'{self.base}/v2/video_avatar',
            data=json.dumps(payload).encode('utf-8'),
            headers=self._headers(),
            method='POST',
        )
        try:
            with request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except error.HTTPError as e:
            msg = e.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f'HeyGen HTTP {e.code}: {msg[:600]}')

    def get_digital_twin(self, avatar_id: str) -> dict:
        req = request.Request(f'{self.base}/v2/video_avatar/{avatar_id}', headers=self._headers(), method='GET')
        try:
            with request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except error.HTTPError as e:
            msg = e.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f'HeyGen HTTP {e.code}: {msg[:600]}')

    def get_video(self, video_id: str) -> dict:
        req = request.Request(f'{self.base}/v1/video_status.get?video_id={video_id}', headers=self._headers(), method='GET')
        try:
            with request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except error.HTTPError as e:
            msg = e.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f'HeyGen HTTP {e.code}: {msg[:400]}')

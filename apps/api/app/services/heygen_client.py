from __future__ import annotations

import json
import os
from urllib import request, error


class HeyGenClient:
    def __init__(self):
        self.base = (os.getenv('HEYGEN_API_BASE') or 'https://api.heygen.com').rstrip('/')
        keys = [
            (os.getenv('HEYGEN_API_KEY') or '').strip(),
            (os.getenv('HEYGEN_API_KEY_SECONDARY') or '').strip(),
        ]
        self.api_keys = [k for k in keys if k]

    def configured(self) -> bool:
        return bool(self.api_keys)

    def _headers(self, api_key: str) -> dict[str, str]:
        return {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json',
        }

    def _request_with_failover(self, method: str, path: str, payload: dict | None = None, timeout: int = 60) -> dict:
        if not self.api_keys:
            raise RuntimeError('HEYGEN_API_KEY missing')
        last_err = None
        for key in self.api_keys:
            req = request.Request(
                f'{self.base}{path}',
                data=(json.dumps(payload).encode('utf-8') if payload is not None else None),
                headers=self._headers(key),
                method=method,
            )
            try:
                with request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except error.HTTPError as e:
                msg = e.read().decode('utf-8', errors='ignore')
                last_err = RuntimeError(f'HeyGen HTTP {e.code}: {msg[:400]}')
                # Try secondary on auth/rate-limit/server errors
                if e.code in (401, 403, 429, 500, 502, 503, 504):
                    continue
                raise last_err
            except Exception as e:
                last_err = RuntimeError(f'HeyGen network error: {e}')
                continue
        raise last_err or RuntimeError('HeyGen request failed')

    def health_probe(self) -> tuple[bool, str]:
        if not self.configured():
            return False, 'No API key configured'
        try:
            # lightweight probe
            self._request_with_failover('GET', '/v2/video_avatar?limit=1', payload=None, timeout=20)
            return True, 'Probe ok'
        except Exception as e:
            return False, str(e)[:220]

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
        return self._request_with_failover('POST', '/v2/video/generate', payload=payload, timeout=60)

    def create_digital_twin(self, avatar_name: str, training_footage_url: str, consent_video_url: str) -> dict:
        payload = {
            'avatar_name': avatar_name,
            'training_footage_url': training_footage_url,
            'video_consent_url': consent_video_url,
        }
        return self._request_with_failover('POST', '/v2/video_avatar', payload=payload, timeout=60)

    def get_digital_twin(self, avatar_id: str) -> dict:
        return self._request_with_failover('GET', f'/v2/video_avatar/{avatar_id}', payload=None, timeout=30)

    def get_video(self, video_id: str) -> dict:
        return self._request_with_failover('GET', f'/v1/video_status.get?video_id={video_id}', payload=None, timeout=30)

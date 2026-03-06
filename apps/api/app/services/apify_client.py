from __future__ import annotations

import json
import os
from typing import Any, Optional
from urllib import error, parse, request


class ApifyClient:
    def __init__(self):
        self.base_url = os.getenv('APIFY_BASE_URL', 'https://api.apify.com/v2').rstrip('/')
        toks = [
            os.getenv('APIFY_TOKEN', '').strip(),
            os.getenv('APIFY_TOKEN_SECONDARY', '').strip(),
        ]
        self.tokens = [t for t in toks if t]
        self.timeout = int(os.getenv('APIFY_TIMEOUT_SECONDS', '30'))

    def configured(self) -> bool:
        return bool(self.tokens)

    def _url(self, path: str, token: str, query: Optional[dict[str, Any]] = None) -> str:
        q = {'token': token}
        if query:
            q.update({k: v for k, v in query.items() if v is not None and v != ''})
        return f"{self.base_url}{path}?{parse.urlencode(q)}"

    def _request(self, method: str, path: str, payload: Optional[dict[str, Any]] = None, query: Optional[dict[str, Any]] = None):
        data = None
        headers = {'Content-Type': 'application/json'}
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')

        if not self.tokens:
            raise RuntimeError('APIFY_TOKEN missing')

        last_err = None
        for token in self.tokens:
            req = request.Request(self._url(path, token=token, query=query), data=data, headers=headers, method=method)
            try:
                with request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode('utf-8')
                    return json.loads(raw) if raw else {}
            except error.HTTPError as e:
                body = e.read().decode('utf-8', errors='ignore')
                last_err = RuntimeError(f'Apify HTTP {e.code}: {body[:500]}')
                if e.code in (401, 403, 429, 500, 502, 503, 504):
                    continue
                raise last_err
            except error.URLError as e:
                last_err = RuntimeError(f'Apify network error: {e}')
                continue
        raise last_err or RuntimeError('Apify request failed')

    def health_probe(self) -> tuple[bool, str]:
        if not self.configured():
            return False, 'No API token configured'
        try:
            self._request('GET', '/acts', query={'limit': 1})
            return True, 'Probe ok'
        except Exception as e:
            return False, str(e)[:220]

    def run_actor(
        self,
        actor_id: str,
        actor_input: Optional[dict[str, Any]] = None,
        build: Optional[str] = None,
        memory_mbytes: Optional[int] = None,
        timeout_secs: Optional[int] = None,
    ) -> dict[str, Any]:
        payload = actor_input or {}
        query = {
            'build': build,
            'memory': memory_mbytes,
            'timeout': timeout_secs,
        }
        return self._request('POST', f'/acts/{parse.quote(actor_id, safe="")}/runs', payload=payload, query=query).get('data', {})

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self._request('GET', f'/actor-runs/{parse.quote(run_id, safe="")}').get('data', {})

    def get_dataset_items(self, dataset_id: str, limit: int = 100) -> list[dict[str, Any]]:
        data = self._request('GET', f'/datasets/{parse.quote(dataset_id, safe="")}/items', query={'limit': limit, 'clean': 1})
        if isinstance(data, list):
            return data
        return []

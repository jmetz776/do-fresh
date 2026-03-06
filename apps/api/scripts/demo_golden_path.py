#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app


def main() -> int:
    client = TestClient(app)
    workspace = "default"

    source = client.post(
        "/sources",
        json={
            "workspaceId": workspace,
            "type": "url",
            "rawPayload": "https://example.com/demo/do-golden-path",
        },
    )
    source.raise_for_status()
    source_id = source.json()["id"]

    normalize = client.post(f"/sources/{source_id}/normalize")
    normalize.raise_for_status()

    source_items = client.get(f"/sources/{source_id}/items")
    source_items.raise_for_status()
    source_item_id = source_items.json()[0]["id"]

    generated = client.post(
        "/content/generate",
        json={
            "workspaceId": workspace,
            "sourceItemId": source_item_id,
            "channels": ["x", "linkedin"],
            "variantCount": 1,
        },
    )
    generated.raise_for_status()
    content_item_id = generated.json()["contentItems"][0]["id"]

    edited = client.patch(
        f"/content/{content_item_id}",
        json={"caption": "DO golden-path demo: ingest → generate → approve → schedule → publish."},
    )
    edited.raise_for_status()

    approved = client.post(f"/content/{content_item_id}/approve")
    approved.raise_for_status()

    publish_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    scheduled = client.post(
        "/schedules",
        json={
            "contentItemId": content_item_id,
            "publishAt": publish_at,
            "timezone": "America/New_York",
        },
    )
    scheduled.raise_for_status()
    schedule_id = scheduled.json()["id"]

    run = client.post("/publish/run", params={"workspaceId": workspace})
    run.raise_for_status()

    dashboard = client.get("/dashboard", params={"workspaceId": workspace})
    dashboard.raise_for_status()

    jobs = client.get("/publish/jobs", params={"workspaceId": workspace})
    jobs.raise_for_status()

    print(
        {
            "source_id": source_id,
            "source_item_id": source_item_id,
            "content_item_id": content_item_id,
            "schedule_id": schedule_id,
            "publish_run": run.json(),
            "dashboard": dashboard.json(),
            "publish_jobs": len(jobs.json()),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

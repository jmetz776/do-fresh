#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import engine, ensure_db_indexes, init_db

EXPECTED = {
    "ix_mvp_sources_workspace_status",
    "ix_mvp_source_items_source_created",
    "ix_mvp_content_items_workspace_status_created",
    "ix_mvp_schedules_status_publish_at",
    "ix_mvp_publish_jobs_schedule_created",
}


def main() -> int:
    init_db()
    ensure_db_indexes()
    found = set()
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
        for r in rows:
            found.add(r[0])

    missing = sorted(EXPECTED - found)
    if missing:
        print({"ok": False, "missing": missing})
        return 1

    print({"ok": True, "indexes": sorted(EXPECTED)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

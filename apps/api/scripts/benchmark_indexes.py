#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "demandorchestrator.db"

INDEXES = [
    "ix_mvp_sources_workspace_status",
    "ix_mvp_source_items_source_created",
    "ix_mvp_content_items_workspace_status_created",
    "ix_mvp_schedules_status_publish_at",
    "ix_mvp_publish_jobs_schedule_created",
]

QUERIES = {
    "content_by_workspace_status": (
        "SELECT id FROM mvp_content_items WHERE workspace_id=? AND status=? ORDER BY created_at DESC LIMIT 100",
        ("default", "draft"),
    ),
    "due_schedules": (
        "SELECT id FROM mvp_schedules WHERE status=? AND publish_at<=? ORDER BY publish_at ASC LIMIT 100",
        ("scheduled", "9999-12-31T23:59:59+00:00"),
    ),
    "jobs_by_schedule": (
        "SELECT id FROM mvp_publish_jobs WHERE schedule_id=? ORDER BY created_at DESC LIMIT 50",
        ("no-such-schedule",),
    ),
    "sources_by_workspace_status": (
        "SELECT id FROM mvp_sources WHERE workspace_id=? AND status=? ORDER BY created_at DESC LIMIT 100",
        ("default", "normalized"),
    ),
    "source_items_by_source": (
        "SELECT id FROM mvp_source_items WHERE source_id=? ORDER BY created_at DESC LIMIT 100",
        ("no-such-source",),
    ),
}


def timed_run(conn: sqlite3.Connection, sql: str, params: tuple, loops: int = 2000) -> float:
    cur = conn.cursor()
    t0 = time.perf_counter()
    for _ in range(loops):
        cur.execute(sql, params)
        cur.fetchall()
    return (time.perf_counter() - t0) * 1000


def plans(conn: sqlite3.Connection, sql: str, params: tuple):
    cur = conn.cursor()
    cur.execute("EXPLAIN QUERY PLAN " + sql, params)
    return [row[3] for row in cur.fetchall()]


def main() -> int:
    if not DB_PATH.exists():
        print({"ok": False, "error": f"DB missing: {DB_PATH}"})
        return 1

    tmpdir = Path(tempfile.mkdtemp(prefix="do-bench-"))
    db_idx = tmpdir / "with_idx.db"
    db_noidx = tmpdir / "without_idx.db"
    shutil.copy2(DB_PATH, db_idx)
    shutil.copy2(DB_PATH, db_noidx)

    conn_idx = sqlite3.connect(db_idx)
    conn_noidx = sqlite3.connect(db_noidx)

    # remove new composite indexes from control copy
    cur_noidx = conn_noidx.cursor()
    for name in INDEXES:
        cur_noidx.execute(f"DROP INDEX IF EXISTS {name}")
    conn_noidx.commit()

    results = {}
    for name, (sql, params) in QUERIES.items():
        with_ms = timed_run(conn_idx, sql, params)
        without_ms = timed_run(conn_noidx, sql, params)
        speedup = (without_ms / with_ms) if with_ms > 0 else None
        results[name] = {
            "with_indexes_ms": round(with_ms, 2),
            "without_indexes_ms": round(without_ms, 2),
            "speedup_x": round(speedup, 2) if speedup else None,
            "plan_with_indexes": plans(conn_idx, sql, params),
            "plan_without_indexes": plans(conn_noidx, sql, params),
        }

    conn_idx.close()
    conn_noidx.close()

    print({"ok": True, "loops": 2000, "db": str(DB_PATH), "results": results})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

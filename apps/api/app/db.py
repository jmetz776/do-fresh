from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./demandorchestrator.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def ensure_db_indexes() -> None:
    # Guardrail for existing SQLite DBs where metadata/index drift can happen over time.
    statements = [
        "CREATE INDEX IF NOT EXISTS ix_mvp_sources_workspace_status ON mvp_sources (workspace_id, status)",
        "CREATE INDEX IF NOT EXISTS ix_mvp_source_items_source_created ON mvp_source_items (source_id, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_mvp_content_items_workspace_status_created ON mvp_content_items (workspace_id, status, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_mvp_schedules_status_publish_at ON mvp_schedules (status, publish_at)",
        "CREATE INDEX IF NOT EXISTS ix_mvp_publish_jobs_schedule_created ON mvp_publish_jobs (schedule_id, created_at)",
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def init_db() -> None:
    # Optional guardrail: prevent accidental ephemeral SQLite usage in production deploys.
    require_persistent = (os.getenv('DO_REQUIRE_PERSISTENT_DB') or 'false').strip().lower() == 'true'
    if require_persistent and DATABASE_URL.startswith('sqlite'):
        raise RuntimeError('Persistent DB required but DATABASE_URL points to sqlite')

    # Ensure model metadata is registered before create_all.
    # Keep startup resilient when optional modules are absent in a given deploy.
    from app.models import core  # noqa: F401
    from app.models import mvp  # noqa: F401

    for optional_mod in ("consent", "auth", "intelligence", "avatar_marketplace", "analytics", "provider_health", "repurpose", "email"):
        try:
            __import__(f"app.models.{optional_mod}")
        except Exception:
            pass

    SQLModel.metadata.create_all(engine)
    ensure_db_indexes()


def get_session():
    with Session(engine) as session:
        yield session

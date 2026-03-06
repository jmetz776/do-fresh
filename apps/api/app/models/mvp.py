from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class MVPWorkspace(SQLModel, table=True):
    __tablename__ = "mvp_workspaces"

    id: str = Field(primary_key=True)
    name: str = Field(default="MVP Workspace")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MVPSource(SQLModel, table=True):
    __tablename__ = "mvp_sources"

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    type: str
    raw_payload: str
    status: str = Field(default="pending", index=True)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MVPSourceItem(SQLModel, table=True):
    __tablename__ = "mvp_source_items"

    id: str = Field(primary_key=True)
    source_id: str = Field(index=True)
    external_ref: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MVPContentItem(SQLModel, table=True):
    __tablename__ = "mvp_content_items"

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    source_item_id: Optional[str] = Field(default=None, index=True)
    channel: str = Field(index=True)
    title: Optional[str] = None
    hook: Optional[str] = None
    caption: str
    variant_no: int = Field(default=1)
    status: str = Field(default="draft", index=True)
    provider_post_id: Optional[str] = Field(default=None, index=True)
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MVPSchedule(SQLModel, table=True):
    __tablename__ = "mvp_schedules"

    id: str = Field(primary_key=True)
    content_item_id: str = Field(index=True)
    publish_at: datetime = Field(index=True)
    timezone: str = Field(default="America/New_York")
    status: str = Field(default="scheduled", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MVPPublishJob(SQLModel, table=True):
    __tablename__ = "mvp_publish_jobs"
    __table_args__ = (UniqueConstraint("idempotency_key", "attempt", name="uq_mvp_job_idem_attempt"),)

    id: str = Field(primary_key=True)
    schedule_id: str = Field(index=True)
    attempt: int = Field(default=1)
    idempotency_key: str = Field(index=True)
    status: str = Field(default="queued", index=True)
    provider_response_json: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MVPGenerationCostEvent(SQLModel, table=True):
    __tablename__ = "mvp_generation_cost_events"

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    capability: str = Field(index=True)  # text|image|video
    model_id: str = Field(index=True)
    provider: str = Field(index=True)
    estimated_cost_usd: float = Field(default=0.0)
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)

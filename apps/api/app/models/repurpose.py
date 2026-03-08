from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class RepurposeJob(SQLModel, table=True):
    __tablename__ = 'repurpose_jobs'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    source_type: str = Field(default='idea', index=True)
    source_title: str = Field(default='')
    source_body: str = Field(default='')
    intent_goal: str = Field(default='awareness', index=True)
    intent_audience: str = Field(default='')
    status: str = Field(default='queued', index=True)  # queued|running|succeeded|partial|failed
    quality_gate_passed: bool = Field(default=False)
    quality_gate_threshold: float = Field(default=0.78)
    errors_json: str = Field(default='[]')
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class RepurposeVariant(SQLModel, table=True):
    __tablename__ = 'repurpose_variants'

    id: str = Field(primary_key=True)
    job_id: str = Field(index=True)
    workspace_id: str = Field(index=True)
    channel: str = Field(index=True)
    format: str = Field(index=True)
    title: str = Field(default='')
    body: str = Field(default='')
    cta: str = Field(default='')
    hashtags_json: str = Field(default='[]')
    payload_json: str = Field(default='{}')
    quality_overall: float = Field(default=0.0)
    quality_brand_fit: float = Field(default=0.0)
    quality_clarity: float = Field(default=0.0)
    quality_originality: float = Field(default=0.0)
    quality_compliance: float = Field(default=0.0)
    status: str = Field(default='draft', index=True)  # draft|needs_review|approved|rejected
    flags_json: str = Field(default='[]')
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class RepurposeQualityEvent(SQLModel, table=True):
    __tablename__ = 'repurpose_quality_events'

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(index=True)
    job_id: str = Field(index=True)
    variant_id: str = Field(index=True)
    event_type: str = Field(default='scored', index=True)  # scored|regenerated|approved|rejected|published
    metadata_json: str = Field(default='{}')
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

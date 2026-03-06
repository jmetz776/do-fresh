from __future__ import annotations

from datetime import datetime, date
from sqlmodel import Field, SQLModel


class ContentPerformanceEvent(SQLModel, table=True):
    __tablename__ = 'content_performance_events'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    content_item_id: str = Field(index=True)
    schedule_id: str = Field(default='', index=True)
    channel: str = Field(default='x', index=True)
    event_type: str = Field(default='impression', index=True)  # impression|engagement|click|lead|publish_succeeded|publish_failed
    value: float = 1.0
    metadata_json: str = '{}'
    occurred_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentDailyMetric(SQLModel, table=True):
    __tablename__ = 'content_daily_metrics'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    content_item_id: str = Field(index=True)
    metric_date: date = Field(index=True)
    channel: str = Field(default='x', index=True)
    impressions: int = 0
    engagements: int = 0
    clicks: int = 0
    leads: int = 0
    publish_succeeded: int = 0
    publish_failed: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)

from __future__ import annotations

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Workspace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BrandProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(index=True)
    voice_tone: str = ""
    offer_positioning: str = ""
    cta_preferences: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(index=True)
    objective: str = Field(index=True)  # awareness|lead-gen|conversion
    source_type: str = "notes"  # topic|transcript|url|notes
    source_input: str = ""
    status: str = Field(default="draft", index=True)  # draft|generated|reviewed|ready
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(index=True)
    asset_type: str = Field(index=True)  # hook|script|post|email|lead_magnet|landing_block
    channel: str = "generic"
    content: str = ""
    score: float = 0.0
    status: str = Field(default="draft", index=True)  # draft|approved|rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(index=True)
    action: str  # approve|reject
    note: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    source: str = "waitlist"
    status: str = "new"
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PerformanceEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(index=True)
    event_type: str = Field(index=True)  # generated|approved|rejected|published|signup
    value: float = 0.0
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LeadActivityEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(index=True)
    event_type: str = Field(index=True)  # created|status_changed|duplicate_blocked|exported
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)

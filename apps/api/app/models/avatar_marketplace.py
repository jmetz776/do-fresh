from __future__ import annotations

from datetime import datetime
from sqlmodel import SQLModel, Field


class AvatarProvider(SQLModel, table=True):
    __tablename__ = 'avatar_providers'

    id: str = Field(primary_key=True)
    display_name: str = Field(index=True)
    status: str = Field(default='active', index=True)  # active|paused|revoked
    consent_packet_id: str = ''
    consent_version: str = 'v1'
    legal_region: str = 'US'
    allowed_use_json: str = '[]'
    prohibited_use_json: str = '[]'
    payout_cents_per_use: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AvatarListing(SQLModel, table=True):
    __tablename__ = 'avatar_listings'

    id: str = Field(primary_key=True)
    provider_id: str = Field(index=True)
    name: str = Field(index=True)
    status: str = Field(default='active', index=True)  # active|paused|retired
    tier: str = Field(default='premium', index=True)
    price_cents_per_video: int = 0
    currency: str = 'USD'
    included_uses_per_month: int = 0
    metadata_json: str = '{}'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AvatarPurchase(SQLModel, table=True):
    __tablename__ = 'avatar_purchases'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    listing_id: str = Field(index=True)
    buyer_user_id: str = Field(index=True)
    status: str = Field(default='active', index=True)  # active|expired|refunded|revoked
    quantity: int = 1
    amount_cents: int = 0
    currency: str = 'USD'
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_to: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AvatarUsageEvent(SQLModel, table=True):
    __tablename__ = 'avatar_usage_events'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    listing_id: str = Field(index=True)
    provider_id: str = Field(index=True)
    purchase_id: str = Field(index=True)
    video_render_id: str = Field(index=True)
    payout_cents: int = 0
    status: str = Field(default='accrued', index=True)  # accrued|settled|reversed
    created_at: datetime = Field(default_factory=datetime.utcnow)

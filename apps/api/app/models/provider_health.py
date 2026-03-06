from __future__ import annotations

from datetime import datetime
from sqlmodel import SQLModel, Field


class ProviderHealthStatus(SQLModel, table=True):
    __tablename__ = 'provider_health_statuses'

    id: str = Field(primary_key=True)
    provider: str = Field(index=True)
    status: str = Field(default='unknown', index=True)  # healthy|degraded|down|unknown
    message: str = ''
    consecutive_failures: int = 0
    checked_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

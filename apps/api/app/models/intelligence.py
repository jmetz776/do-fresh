from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TrendSuggestion(SQLModel, table=True):
    __tablename__ = "trend_suggestions"

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    topic: str = Field(index=True)
    source: str = Field(index=True)
    why_now: str = Field(default="")
    trend_score: float = Field(default=0.0)
    brand_fit_score: float = Field(default=0.0)
    policy_risk_score: float = Field(default=0.0)
    final_score: float = Field(default=0.0, index=True)
    status: str = Field(default="new", index=True)  # new|accepted|rejected|published
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceLearningProfile(SQLModel, table=True):
    __tablename__ = "workspace_learning_profiles"

    workspace_id: str = Field(primary_key=True)
    source_weight: float = Field(default=0.30)
    trend_weight: float = Field(default=0.35)
    brand_fit_weight: float = Field(default=0.35)
    reject_penalty: float = Field(default=0.15)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SuggestionFeedbackEvent(SQLModel, table=True):
    __tablename__ = "suggestion_feedback_events"

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    suggestion_id: str = Field(index=True)
    user_id: str = Field(index=True)
    event_type: str = Field(index=True)  # viewed|accepted|rejected|edited|published
    edit_distance: Optional[float] = None
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)

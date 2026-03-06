from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ConsentRecord(SQLModel, table=True):
    __tablename__ = 'consent_records'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    subject_full_name: str
    subject_email: str = Field(index=True)
    consent_type: str = Field(index=True)  # voice|likeness|both
    scope_json: str = '{}'  # allowed channels/use-case scope
    release_version: str = 'v1'
    signed_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None
    status: str = Field(default='signed', index=True)  # signed|revoked|blocked
    evidence_uri: str = ''  # signed release artifact URI/path
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IdentityVerification(SQLModel, table=True):
    __tablename__ = 'identity_verifications'

    id: str = Field(primary_key=True)
    consent_record_id: str = Field(index=True)
    provider: str = 'manual'
    status: str = Field(default='pending', index=True)  # pending|verified|failed
    score: float = 0.0
    metadata_json: str = '{}'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceProfile(SQLModel, table=True):
    __tablename__ = 'voice_profiles'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    consent_record_id: str = Field(index=True)
    provider: str = 'elevenlabs'
    provider_voice_id: str = ''
    display_name: str = 'Custom Voice'
    status: str = Field(default='pending', index=True)  # pending|active|disabled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AvatarProfile(SQLModel, table=True):
    __tablename__ = 'avatar_profiles'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    consent_record_id: str = Field(index=True)
    provider: str = 'heygen'
    provider_avatar_id: str = ''
    display_name: str = 'Custom Avatar'
    status: str = Field(default='pending', index=True)  # pending|active|disabled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceRenderJob(SQLModel, table=True):
    __tablename__ = 'voice_render_jobs'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    voice_profile_id: str = Field(index=True)
    script_text: str
    provider: str = 'elevenlabs'
    provider_job_id: str = ''
    audio_uri: str = ''
    status: str = Field(default='queued', index=True)  # queued|succeeded|failed|approved
    error: str = ''
    estimated_cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VideoRenderJob(SQLModel, table=True):
    __tablename__ = 'video_render_jobs'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    voice_render_id: str = Field(index=True)
    provider: str = 'stub-video'
    provider_job_id: str = ''
    script_text: str = ''
    video_uri: str = ''
    status: str = Field(default='queued', index=True)  # queued|succeeded|failed|approved
    error: str = ''
    estimated_cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VideoRenderBackground(SQLModel, table=True):
    __tablename__ = 'video_render_backgrounds'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    render_id: str = Field(index=True)
    background_template_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

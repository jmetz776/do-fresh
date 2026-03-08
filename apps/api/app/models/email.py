from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class EmailSenderConnection(SQLModel, table=True):
    __tablename__ = 'email_sender_connections'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    provider: str = Field(index=True)  # gmail|outlook
    sender_email: str = Field(index=True)
    sender_name: str = Field(default='')
    status: str = Field(default='active', index=True)  # active|expired|error|disconnected
    scopes_json: str = Field(default='[]')
    token_ref: str = Field(default='')
    is_default: bool = Field(default=False)
    last_tested_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class AudienceList(SQLModel, table=True):
    __tablename__ = 'audience_lists'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    name: str = Field(index=True)
    source_type: str = Field(default='csv', index=True)  # csv|hubspot|crm
    status: str = Field(default='active', index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class AudienceContact(SQLModel, table=True):
    __tablename__ = 'audience_contacts'

    id: str = Field(primary_key=True)
    list_id: str = Field(index=True)
    workspace_id: str = Field(index=True)
    email: str = Field(index=True)
    first_name: str = Field(default='')
    last_name: str = Field(default='')
    tags_json: str = Field(default='[]')
    consent_status: str = Field(default='opted_in', index=True)  # opted_in|unknown|unsubscribed
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class SuppressionEntry(SQLModel, table=True):
    __tablename__ = 'email_suppression_list'

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(index=True)
    email: str = Field(index=True)
    reason: str = Field(default='manual')
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class EmailImportAudit(SQLModel, table=True):
    __tablename__ = 'email_import_audits'

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    list_id: str = Field(index=True)
    uploaded_by_email: str = Field(default='', index=True)
    list_origin: str = Field(default='external_csv')
    consent_attested: bool = Field(default=False)
    imported_count: int = Field(default=0)
    eligible_opted_in_count: int = Field(default=0)
    suppressed_or_unknown_count: int = Field(default=0)
    skipped_invalid_count: int = Field(default=0)
    notes_json: str = Field(default='{}')
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

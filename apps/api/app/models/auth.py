from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    email: str = Field(index=True, unique=True)
    email_verified: bool = Field(default=False, index=True)
    password_hash: Optional[str] = None
    oidc_subject: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Workspace(SQLModel, table=True):
    __tablename__ = "workspaces"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    plan_tier: str = Field(default="starter", index=True)
    owner_user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceMembership(SQLModel, table=True):
    __tablename__ = "workspace_memberships"

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    user_id: str = Field(index=True)
    role: str = Field(default="viewer", index=True)  # owner|admin|editor|publisher|viewer
    status: str = Field(default="active", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceSetting(SQLModel, table=True):
    __tablename__ = "workspace_settings"

    id: str = Field(primary_key=True)
    workspace_id: str = Field(index=True)
    key: str = Field(index=True)
    value_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BetaInvite(SQLModel, table=True):
    __tablename__ = "beta_invites"

    id: str = Field(primary_key=True)
    email: str = Field(index=True)
    workspace_name: str = Field(default="Beta Workspace")
    role: str = Field(default="owner", index=True)
    status: str = Field(default="active", index=True)  # active|used|revoked|expired
    expires_at: Optional[datetime] = None
    max_uses: int = Field(default=1)
    used_count: int = Field(default=0)
    created_by: str = Field(default="system")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MagicLinkToken(SQLModel, table=True):
    __tablename__ = "magic_link_tokens"

    id: str = Field(primary_key=True)
    email: str = Field(index=True)
    invite_id: str = Field(index=True)
    token_hash: str = Field(index=True)
    status: str = Field(default="issued", index=True)  # issued|consumed|expired|revoked
    expires_at: datetime = Field(index=True)
    consumed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

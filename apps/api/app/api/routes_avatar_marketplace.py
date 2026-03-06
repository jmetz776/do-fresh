from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models.avatar_marketplace import AvatarProvider, AvatarListing, AvatarPurchase
from app.services.authz import actor_user_id, require_workspace_role

router = APIRouter(prefix='/v1/avatar-marketplace', tags=['avatar-marketplace'])


def _now() -> datetime:
    return datetime.utcnow()


def _require_admin(x_admin_key: Optional[str]) -> None:
    expected = (os.getenv('AVATAR_MARKETPLACE_ADMIN_KEY') or '').strip()
    if not expected:
        raise HTTPException(status_code=503, detail='avatar marketplace admin key not configured')
    if (x_admin_key or '').strip() != expected:
        raise HTTPException(status_code=403, detail='forbidden')


class CreateProviderRequest(BaseModel):
    displayName: str = Field(min_length=2, max_length=120)
    consentPacketId: str = Field(min_length=2, max_length=120)
    consentVersion: str = Field(default='v1', min_length=1, max_length=32)
    legalRegion: str = Field(default='US', min_length=2, max_length=16)
    allowedUse: list[str] = Field(default_factory=lambda: ['organic', 'ads'])
    prohibitedUse: list[str] = Field(default_factory=lambda: ['political'])
    payoutCentsPerUse: int = Field(default=300, ge=0, le=100000)


class CreateListingRequest(BaseModel):
    providerId: str
    name: str = Field(min_length=2, max_length=120)
    tier: str = Field(default='premium')
    priceCentsPerVideo: int = Field(default=1500, ge=0, le=1000000)
    includedUsesPerMonth: int = Field(default=0, ge=0, le=100000)


class PurchaseListingRequest(BaseModel):
    workspaceId: str
    listingId: str
    quantity: int = Field(default=1, ge=1, le=100)


@router.post('/providers')
def create_provider(
    payload: CreateProviderRequest,
    session: Session = Depends(get_session),
    x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key'),
):
    _require_admin(x_admin_key)

    row = AvatarProvider(
        id=f'ap_{uuid4().hex[:14]}',
        display_name=payload.displayName.strip(),
        status='active',
        consent_packet_id=payload.consentPacketId.strip(),
        consent_version=payload.consentVersion.strip(),
        legal_region=payload.legalRegion.strip().upper(),
        allowed_use_json=json.dumps(payload.allowedUse),
        prohibited_use_json=json.dumps(payload.prohibitedUse),
        payout_cents_per_use=payload.payoutCentsPerUse,
        created_at=_now(),
        updated_at=_now(),
    )
    session.add(row)
    session.commit()
    return {'ok': True, 'id': row.id}


@router.post('/listings')
def create_listing(
    payload: CreateListingRequest,
    session: Session = Depends(get_session),
    x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key'),
):
    _require_admin(x_admin_key)

    provider = session.get(AvatarProvider, payload.providerId)
    if not provider or provider.status != 'active':
        raise HTTPException(status_code=404, detail='provider not found or inactive')

    row = AvatarListing(
        id=f'al_{uuid4().hex[:14]}',
        provider_id=provider.id,
        name=payload.name.strip(),
        status='active',
        tier=(payload.tier or 'premium').strip().lower(),
        price_cents_per_video=payload.priceCentsPerVideo,
        currency='USD',
        included_uses_per_month=payload.includedUsesPerMonth,
        metadata_json=json.dumps({'providerDisplayName': provider.display_name}),
        created_at=_now(),
        updated_at=_now(),
    )
    session.add(row)
    session.commit()
    return {'ok': True, 'id': row.id}


@router.get('/listings')
def list_listings(
    status: str = Query(default='active'),
    tier: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(AvatarListing)
        .where(AvatarListing.status == status)
        .order_by(AvatarListing.created_at.desc())
        .limit(limit)
    ).all()

    out = []
    for r in rows:
        if tier and (r.tier or '').lower() != tier.lower():
            continue
        provider = session.get(AvatarProvider, r.provider_id)
        out.append({
            'id': r.id,
            'name': r.name,
            'tier': r.tier,
            'priceCentsPerVideo': r.price_cents_per_video,
            'currency': r.currency,
            'includedUsesPerMonth': r.included_uses_per_month,
            'provider': {
                'id': provider.id if provider else r.provider_id,
                'displayName': provider.display_name if provider else 'Unknown',
                'legalRegion': provider.legal_region if provider else 'US',
            },
        })
    return {'count': len(out), 'items': out}


@router.post('/purchases')
def purchase_listing(
    payload: PurchaseListingRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(actor_user_id),
):
    require_workspace_role(session, workspace_id=payload.workspaceId, min_role='editor', user_id=user_id)

    listing = session.get(AvatarListing, payload.listingId)
    if not listing or listing.status != 'active':
        raise HTTPException(status_code=404, detail='listing not found or inactive')

    amount = int(listing.price_cents_per_video * payload.quantity)
    row = AvatarPurchase(
        id=f'apu_{uuid4().hex[:14]}',
        workspace_id=payload.workspaceId,
        listing_id=listing.id,
        buyer_user_id=user_id,
        status='active',
        quantity=payload.quantity,
        amount_cents=amount,
        currency=listing.currency,
        valid_from=_now(),
        valid_to=_now() + timedelta(days=30),
        created_at=_now(),
        updated_at=_now(),
    )
    session.add(row)
    session.commit()

    return {
        'ok': True,
        'purchase': {
            'id': row.id,
            'workspaceId': row.workspace_id,
            'listingId': row.listing_id,
            'quantity': row.quantity,
            'amountCents': row.amount_cents,
            'currency': row.currency,
            'validTo': row.valid_to.isoformat() if row.valid_to else None,
        },
    }

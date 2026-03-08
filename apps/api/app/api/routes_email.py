from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlmodel import Session, select

from app.db import get_session
from app.models.email import EmailSenderConnection, AudienceList, AudienceContact

router = APIRouter(prefix='/v1/email', tags=['email'])


@router.post('/senders/connect/{provider}')
def connect_sender(
    provider: str,
    workspaceId: str = Form(default='default'),
    senderEmail: str = Form(default=''),
    senderName: str = Form(default=''),
    setDefault: bool = Form(default=True),
    session: Session = Depends(get_session),
):
    p = provider.strip().lower()
    if p not in {'gmail', 'outlook'}:
        raise HTTPException(status_code=400, detail='provider must be gmail or outlook')
    email = senderEmail.strip().lower()
    if '@' not in email:
        raise HTTPException(status_code=400, detail='valid senderEmail required')

    if setDefault:
        rows = session.exec(select(EmailSenderConnection).where(EmailSenderConnection.workspace_id == workspaceId)).all()
        for r in rows:
            if r.is_default:
                r.is_default = False
                r.updated_at = datetime.utcnow()
                session.add(r)

    row = EmailSenderConnection(
        id=str(uuid4()),
        workspace_id=workspaceId,
        provider=p,
        sender_email=email,
        sender_name=senderName.strip(),
        status='active',
        scopes_json=json.dumps(['send']),
        token_ref='oauth_stub',
        is_default=bool(setDefault),
        updated_at=datetime.utcnow(),
    )
    session.add(row)
    session.commit()
    return {'id': row.id, 'status': row.status, 'provider': row.provider, 'senderEmail': row.sender_email}


@router.get('/senders')
def list_senders(
    workspaceId: str = Query(default='default'),
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(EmailSenderConnection)
        .where(EmailSenderConnection.workspace_id == workspaceId)
        .order_by(EmailSenderConnection.created_at.desc())
        .limit(limit)
    ).all()
    return {
        'items': [
            {
                'id': r.id,
                'provider': r.provider,
                'senderEmail': r.sender_email,
                'senderName': r.sender_name,
                'status': r.status,
                'isDefault': r.is_default,
                'lastTestedAt': r.last_tested_at.isoformat() if r.last_tested_at else None,
            }
            for r in rows
        ]
    }


@router.post('/senders/{sender_id}/test')
def test_sender(sender_id: str, session: Session = Depends(get_session)):
    row = session.get(EmailSenderConnection, sender_id)
    if not row:
        raise HTTPException(status_code=404, detail='sender not found')
    row.last_tested_at = datetime.utcnow()
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    return {'ok': True, 'id': row.id, 'status': row.status, 'lastTestedAt': row.last_tested_at.isoformat()}


@router.post('/senders/{sender_id}/disconnect')
def disconnect_sender(sender_id: str, session: Session = Depends(get_session)):
    row = session.get(EmailSenderConnection, sender_id)
    if not row:
        raise HTTPException(status_code=404, detail='sender not found')
    row.status = 'disconnected'
    row.is_default = False
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    return {'ok': True, 'id': row.id, 'status': row.status}


@router.post('/audiences/import-csv')
def import_audience_csv(
    workspaceId: str = Form(default='default'),
    listName: str = Form(default='Imported List'),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    content = file.file.read()
    text = content.decode('utf-8', errors='ignore')
    reader = csv.DictReader(io.StringIO(text))

    audience = AudienceList(
        id=str(uuid4()),
        workspace_id=workspaceId,
        name=listName.strip() or 'Imported List',
        source_type='csv',
        status='active',
        updated_at=datetime.utcnow(),
    )
    session.add(audience)
    session.commit()

    imported = 0
    for row in reader:
        email = str(row.get('email') or '').strip().lower()
        if '@' not in email:
            continue
        contact = AudienceContact(
            id=str(uuid4()),
            list_id=audience.id,
            workspace_id=workspaceId,
            email=email,
            first_name=str(row.get('first_name') or row.get('firstName') or '').strip(),
            last_name=str(row.get('last_name') or row.get('lastName') or '').strip(),
            tags_json=json.dumps([]),
            consent_status='opted_in',
        )
        session.add(contact)
        imported += 1

    audience.updated_at = datetime.utcnow()
    session.add(audience)
    session.commit()

    return {'ok': True, 'listId': audience.id, 'imported': imported}


@router.get('/audiences')
def list_audiences(
    workspaceId: str = Query(default='default'),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(AudienceList)
        .where(AudienceList.workspace_id == workspaceId)
        .order_by(AudienceList.created_at.desc())
        .limit(limit)
    ).all()

    items = []
    for r in rows:
        count = session.exec(
            select(AudienceContact)
            .where(AudienceContact.list_id == r.id)
        ).all()
        items.append(
            {
                'id': r.id,
                'name': r.name,
                'sourceType': r.source_type,
                'status': r.status,
                'contactCount': len(count),
                'updatedAt': r.updated_at.isoformat(),
            }
        )

    return {'items': items}

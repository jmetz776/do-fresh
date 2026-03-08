from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models.email import EmailSenderConnection, AudienceList, AudienceContact, SuppressionEntry, EmailImportAudit

router = APIRouter(prefix='/v1/email', tags=['email'])


class SendRepurposeEmailRequest(
    BaseModel
):
    workspaceId: str = 'default'
    senderConnectionId: str
    audienceListId: str
    subject: str
    body: str
    includeUnsubscribe: bool = True


class UnsubscribeRequest(BaseModel):
    workspaceId: str = 'default'
    email: str
    reason: str = 'user_unsubscribe'


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
    listOrigin: str = Form(default='external_csv'),
    consentAttestation: bool = Form(default=False),
    uploadedByEmail: str = Form(default=''),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    if not consentAttestation:
        raise HTTPException(status_code=400, detail='consent_attestation_required')

    content = file.file.read()
    text = content.decode('utf-8', errors='ignore')
    reader = csv.DictReader(io.StringIO(text))

    required_cols = {'email', 'consent_status'}
    cols = {c.strip() for c in (reader.fieldnames or []) if c}
    if not required_cols.issubset(cols):
        raise HTTPException(status_code=400, detail='csv_requires_columns: email, consent_status')

    audience = AudienceList(
        id=str(uuid4()),
        workspace_id=workspaceId,
        name=(listName.strip() or 'Imported List')[:180],
        source_type='csv',
        status='active',
        updated_at=datetime.utcnow(),
    )
    session.add(audience)
    session.commit()

    imported = 0
    opted_in = 0
    suppressed = 0
    skipped = 0
    allowed_status = {'opted_in', 'unknown', 'unsubscribed'}

    for row in reader:
        email = str(row.get('email') or '').strip().lower()
        if '@' not in email:
            skipped += 1
            continue

        consent_status = str(row.get('consent_status') or 'unknown').strip().lower()
        if consent_status not in allowed_status:
            consent_status = 'unknown'

        tags = str(row.get('tags') or '').strip()
        tags_json = json.dumps([t.strip() for t in tags.split(',') if t.strip()]) if tags else '[]'

        contact = AudienceContact(
            id=str(uuid4()),
            list_id=audience.id,
            workspace_id=workspaceId,
            email=email,
            first_name=str(row.get('first_name') or row.get('firstName') or '').strip(),
            last_name=str(row.get('last_name') or row.get('lastName') or '').strip(),
            tags_json=tags_json,
            consent_status=consent_status,
        )
        session.add(contact)
        imported += 1

        if consent_status == 'opted_in':
            opted_in += 1
        else:
            suppressed += 1

    audience.updated_at = datetime.utcnow()
    session.add(audience)

    audit = EmailImportAudit(
        id=str(uuid4()),
        workspace_id=workspaceId,
        list_id=audience.id,
        uploaded_by_email=uploadedByEmail.strip().lower(),
        list_origin=(listOrigin or 'external_csv')[:120],
        consent_attested=bool(consentAttestation),
        imported_count=imported,
        eligible_opted_in_count=opted_in,
        suppressed_or_unknown_count=suppressed,
        skipped_invalid_count=skipped,
        notes_json=json.dumps({'required_columns_enforced': True}),
    )
    session.add(audit)
    session.commit()

    return {
        'ok': True,
        'listId': audience.id,
        'listOrigin': listOrigin,
        'imported': imported,
        'eligibleOptedIn': opted_in,
        'suppressedOrUnknown': suppressed,
        'skippedInvalid': skipped,
        'complianceWarning': suppressed > 0,
        'auditId': audit.id,
    }


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
        contacts = session.exec(
            select(AudienceContact)
            .where(AudienceContact.list_id == r.id)
        ).all()
        opted_in = sum(1 for c in contacts if c.consent_status == 'opted_in')
        blocked = len(contacts) - opted_in
        warnings = []
        if blocked > 0:
            warnings.append('list_contains_non_opted_in_contacts')
        items.append(
            {
                'id': r.id,
                'name': r.name,
                'sourceType': r.source_type,
                'status': r.status,
                'contactCount': len(contacts),
                'eligibleOptedIn': opted_in,
                'blockedContacts': blocked,
                'complianceWarnings': warnings,
                'updatedAt': r.updated_at.isoformat(),
            }
        )

    return {'items': items}


@router.post('/unsubscribe')
def unsubscribe_contact(payload: UnsubscribeRequest, session: Session = Depends(get_session)):
    email = payload.email.strip().lower()
    if '@' not in email:
        raise HTTPException(status_code=400, detail='valid_email_required')

    entry = SuppressionEntry(
        workspace_id=payload.workspaceId,
        email=email,
        reason=(payload.reason or 'user_unsubscribe')[:120],
    )
    session.add(entry)

    contacts = session.exec(
        select(AudienceContact).where(
            AudienceContact.workspace_id == payload.workspaceId,
            AudienceContact.email == email,
        )
    ).all()
    for c in contacts:
        c.consent_status = 'unsubscribed'
        session.add(c)

    session.commit()
    return {'ok': True, 'email': email, 'updatedContacts': len(contacts)}


@router.post('/repurpose/send')
def send_repurpose_email(payload: SendRepurposeEmailRequest, session: Session = Depends(get_session)):
    sender = session.get(EmailSenderConnection, payload.senderConnectionId)
    if not sender or sender.workspace_id != payload.workspaceId or sender.status != 'active':
        raise HTTPException(status_code=400, detail='active_sender_required')

    audience = session.get(AudienceList, payload.audienceListId)
    if not audience or audience.workspace_id != payload.workspaceId:
        raise HTTPException(status_code=400, detail='audience_list_not_found')

    if not payload.includeUnsubscribe:
        raise HTTPException(status_code=400, detail='unsubscribe_footer_required')

    contacts = session.exec(
        select(AudienceContact).where(
            AudienceContact.list_id == payload.audienceListId,
            AudienceContact.workspace_id == payload.workspaceId,
        )
    ).all()

    suppression = session.exec(
        select(SuppressionEntry).where(SuppressionEntry.workspace_id == payload.workspaceId)
    ).all()
    suppressed_set = {s.email.strip().lower() for s in suppression}

    eligible = [c for c in contacts if c.consent_status == 'opted_in' and c.email.strip().lower() not in suppressed_set]
    blocked = len(contacts) - len(eligible)
    if not eligible:
        raise HTTPException(status_code=400, detail='no_eligible_opted_in_contacts')

    rendered = (payload.body.strip() + '\n\n---\nUnsubscribe: {{unsubscribe_link}}').strip()

    # Sending is stubbed in v1 scaffold; compliance gating is enforced before this step.
    return {
        'ok': True,
        'mode': 'dry_run_stub',
        'senderEmail': sender.sender_email,
        'audienceListId': audience.id,
        'subject': payload.subject[:180],
        'eligibleRecipients': len(eligible),
        'blockedRecipients': blocked,
        'enforced': {
            'opted_in_only': True,
            'suppression_enforced': True,
            'unsubscribe_footer_required': True,
        },
        'renderedBodyPreview': rendered[:500],
    }

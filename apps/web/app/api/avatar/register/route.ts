import { NextResponse } from 'next/server';

const API_BASE = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const email = String(body?.email || '').trim().toLowerCase();
    const fullName = String(body?.fullName || '').trim();
    const providerAvatarId = String(body?.providerAvatarId || '').trim();
    const displayName = String(body?.displayName || 'Custom Avatar').trim();
    const workspaceId = String(body?.workspaceId || 'default').trim() || 'default';

    if (!email || !fullName || !providerAvatarId) {
      return NextResponse.json({ detail: 'fullName, email, and providerAvatarId are required' }, { status: 400 });
    }

    const recRes = await fetch(`${API_BASE}/v1/consent/records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workspaceId,
        subjectFullName: fullName,
        subjectEmail: email,
        consentType: 'likeness',
        scope: { channels: ['x', 'linkedin', 'instagram', 'youtube', 'tiktok'], usage: 'avatar_generation' },
      }),
    });
    const rec = await recRes.json().catch(() => ({}));
    if (!recRes.ok || !rec?.id) {
      return NextResponse.json(rec || { detail: 'failed to create consent record' }, { status: recRes.status || 502 });
    }

    const verifyRes = await fetch(`${API_BASE}/v1/consent/records/${rec.id}/verify-identity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: 'manual', status: 'verified', score: 1.0, metadata: { source: 'avatar-studio-register' } }),
    });
    if (!verifyRes.ok) {
      const verifyErr = await verifyRes.json().catch(() => ({}));
      return NextResponse.json(verifyErr || { detail: 'failed to verify identity' }, { status: verifyRes.status || 502 });
    }

    const profileRes = await fetch(`${API_BASE}/v1/consent/avatar/profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workspaceId,
        consentRecordId: rec.id,
        provider: 'heygen',
        providerAvatarId,
        displayName,
      }),
    });
    const profile = await profileRes.json().catch(() => ({}));
    if (!profileRes.ok) {
      return NextResponse.json(profile || { detail: 'failed to create avatar profile' }, { status: profileRes.status || 502 });
    }

    return NextResponse.json({ ok: true, consentRecordId: rec.id, avatarProfileId: profile.id, status: profile.status });
  } catch (e: any) {
    return NextResponse.json({ detail: e?.message || 'unexpected error' }, { status: 500 });
  }
}

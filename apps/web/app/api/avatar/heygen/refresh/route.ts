import { NextResponse } from 'next/server';

const API_BASE = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const avatarProfileId = String(body?.avatarProfileId || '').trim();
  if (!avatarProfileId) {
    return NextResponse.json({ detail: 'avatarProfileId is required' }, { status: 400 });
  }

  const upstream = await fetch(`${API_BASE}/v1/consent/avatar/heygen/${encodeURIComponent(avatarProfileId)}/refresh`, {
    method: 'POST',
  });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { 'Content-Type': upstream.headers.get('content-type') || 'application/json' },
  });
}

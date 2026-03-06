import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_BASE = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const platform = String(body?.platform || '').trim().toLowerCase();
  if (!platform) return NextResponse.json({ ok: false, error: 'platform required' }, { status: 400 });

  const c = cookies();
  const token = c.get('do_api_token')?.value || '';
  const workspaceId = c.get('do_workspace_id')?.value || 'default';
  if (!token) return NextResponse.json({ ok: false, error: 'not authenticated' }, { status: 401 });

  const upstream = await fetch(`${API_BASE}/integrations/accounts/connect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ workspaceId, platform }),
    cache: 'no-store',
  });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { 'Content-Type': upstream.headers.get('content-type') || 'application/json' },
  });
}

import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export async function GET() {
  const token = cookies().get('do_api_token')?.value || '';
  const workspaceId = cookies().get('do_workspace_id')?.value || 'default';

  const upstream = await fetch(`${API_BASE}/v1/consent/video/limits?workspaceId=${encodeURIComponent(workspaceId)}`, {
    method: 'GET',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: 'no-store',
  });

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { 'Content-Type': upstream.headers.get('content-type') || 'application/json' },
  });
}

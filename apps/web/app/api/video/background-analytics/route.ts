import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export async function GET(req: Request) {
  const token = cookies().get('do_api_token')?.value || '';
  const workspaceId = cookies().get('do_workspace_id')?.value || 'default';
  const u = new URL(req.url);
  const limit = u.searchParams.get('limit') || '200';

  const upstream = await fetch(`${API_BASE}/v1/consent/video/background-analytics?workspaceId=${encodeURIComponent(workspaceId)}&limit=${encodeURIComponent(limit)}`, {
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

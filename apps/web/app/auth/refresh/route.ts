import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

function assertSameOrigin(req: Request) {
  const origin = req.headers.get('origin') || '';
  const host = req.headers.get('host') || '';
  if (!origin || !host) return false;
  try {
    const u = new URL(origin);
    return u.host === host;
  } catch {
    return false;
  }
}

export async function POST(req: Request) {
  if (!assertSameOrigin(req)) {
    return NextResponse.json({ ok: false, error: 'csrf blocked' }, { status: 403 });
  }
  const c = cookies();
  const token = c.get('do_api_token')?.value || '';
  if (!token) return NextResponse.json({ ok: false, error: 'missing token' }, { status: 401 });

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data?.token) return NextResponse.json({ ok: false, error: 'refresh failed' }, { status: 401 });

  const out = NextResponse.json({ ok: true });
  const isProd = process.env.NODE_ENV === 'production';
  out.cookies.set('do_api_token', String(data.token), { httpOnly: true, sameSite: 'lax', path: '/', secure: isProd });
  return out;
}

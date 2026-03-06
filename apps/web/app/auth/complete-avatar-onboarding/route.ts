import { NextResponse } from 'next/server';

function assertSameOrigin(req: Request) {
  const origin = req.headers.get('origin') || '';
  const host = req.headers.get('host') || '';
  if (!origin || !host) return false;
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

export async function POST(req: Request) {
  if (!assertSameOrigin(req)) {
    return NextResponse.json({ ok: false, error: 'csrf blocked' }, { status: 403 });
  }

  const res = NextResponse.json({ ok: true });
  const isProd = process.env.NODE_ENV === 'production';
  const common = { httpOnly: true as const, sameSite: 'lax' as const, path: '/', secure: isProd };
  res.cookies.set('do_avatar_onboarding_complete', '1', common);
  return res;
}

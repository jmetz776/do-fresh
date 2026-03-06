import { NextResponse } from 'next/server';

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
  const body = await req.json().catch(() => ({}));
  const userId = String(body?.userId || '').trim();
  const userEmail = String(body?.userEmail || '').trim();
  const workspaceId = String(body?.workspaceId || '').trim();
  const token = String(body?.token || '').trim();

  if (!userId || !userEmail || !workspaceId || !token) {
    return NextResponse.json({ ok: false, error: 'missing fields' }, { status: 400 });
  }

  const res = NextResponse.json({ ok: true });
  const isProd = process.env.NODE_ENV === 'production';
  const common = { httpOnly: true as const, sameSite: 'lax' as const, path: '/', secure: isProd };
  res.cookies.set('do_user_id', userId, common);
  res.cookies.set('do_user_email', userEmail, common);
  res.cookies.set('do_workspace_id', workspaceId, common);
  res.cookies.set('do_api_token', token, common);

  const superusers = new Set(
    String(process.env.AUTH_SUPERUSER_EMAILS || process.env.WEB_SUPERUSER_EMAILS || '')
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
  const isSuperuser = superusers.has(userEmail.toLowerCase());

  // Force onboarding once after login; superusers can bypass for internal operations.
  res.cookies.set('do_onboarding_complete', isSuperuser ? '1' : '0', common);
  res.cookies.set('do_avatar_onboarding_complete', isSuperuser ? '1' : '0', common);
  return res;
}

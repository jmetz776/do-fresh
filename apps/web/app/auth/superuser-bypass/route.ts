import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

function isSuperuser(email: string) {
  const set = new Set(
    String(process.env.AUTH_SUPERUSER_EMAILS || process.env.WEB_SUPERUSER_EMAILS || '')
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
  return set.has((email || '').trim().toLowerCase());
}

function cookieOpts() {
  const isProd = process.env.NODE_ENV === 'production';
  return { httpOnly: true as const, sameSite: 'lax' as const, path: '/', secure: isProd };
}

export async function GET(req: Request) {
  const c = cookies();
  const email = c.get('do_user_email')?.value || '';
  const origin = new URL(req.url).origin;
  if (!email) {
    return NextResponse.redirect(new URL('/login', origin));
  }

  if (!isSuperuser(email)) {
    return NextResponse.json({ ok: false, error: 'forbidden' }, { status: 403 });
  }

  const res = NextResponse.redirect(new URL('/studio', origin));
  const common = cookieOpts();
  res.cookies.set('do_onboarding_complete', '1', common);
  res.cookies.set('do_avatar_onboarding_complete', '1', common);
  return res;
}

import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const form = await req.formData();
  const key = String(form.get('access_key') || '');
  const nextPath = String(form.get('next') || '/studio');

  const expected = process.env.EARLY_ACCESS_KEY || 'do-invite-only';
  if (key !== expected) {
    return NextResponse.redirect(new URL('/early-access?error=1', req.url));
  }

  const res = NextResponse.redirect(new URL(nextPath.startsWith('/') ? nextPath : '/studio', req.url));
  res.cookies.set('do_early_access', '1', {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60 * 12,
  });
  return res;
}

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const withSecurityHeaders = (res: NextResponse) => {
    res.headers.set('X-Frame-Options', 'DENY');
    res.headers.set('X-Content-Type-Options', 'nosniff');
    res.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    res.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    return res;
  };

  // Gate Studio routes only.
  if (!pathname.startsWith('/studio')) return withSecurityHeaders(NextResponse.next());

  // Allow avatar recording during onboarding.
  if (pathname.startsWith('/studio/model-signup')) return withSecurityHeaders(NextResponse.next());

  const hasSession = Boolean(req.cookies.get('do_user_id')?.value) && Boolean(req.cookies.get('do_user_email')?.value) && Boolean(req.cookies.get('do_workspace_id')?.value) && Boolean(req.cookies.get('do_api_token')?.value);
  if (hasSession) {
    const onboardingComplete = req.cookies.get('do_onboarding_complete')?.value === '1';
    if (!onboardingComplete) {
      const url = req.nextUrl.clone();
      url.pathname = '/onboarding';
      url.searchParams.set('phase', 'setup');
      url.searchParams.set('next', pathname);
      return withSecurityHeaders(NextResponse.redirect(url));
    }
    return withSecurityHeaders(NextResponse.next());
  }

  const unlocked = req.cookies.get('do_early_access')?.value === '1';
  if (!unlocked) {
    const url = req.nextUrl.clone();
    url.pathname = '/early-access';
    url.searchParams.set('next', pathname);
    return withSecurityHeaders(NextResponse.redirect(url));
  }

  const url = req.nextUrl.clone();
  url.pathname = '/login';
  url.searchParams.set('next', pathname);
  return withSecurityHeaders(NextResponse.redirect(url));

  return withSecurityHeaders(NextResponse.next());
}

export const config = {
  matcher: ['/studio/:path*'],
};

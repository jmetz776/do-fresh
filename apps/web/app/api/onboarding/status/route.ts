import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_BASE = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

async function getJson(path: string, token: string) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    cache: 'no-store',
  });
  if (!res.ok) return null;
  return res.json();
}

export async function GET() {
  const c = cookies();
  const token = c.get('do_api_token')?.value || '';
  const workspaceId = c.get('do_workspace_id')?.value || 'default';
  const onboardingComplete = c.get('do_onboarding_complete')?.value === '1';
  const avatarComplete = c.get('do_avatar_onboarding_complete')?.value === '1';

  const accounts = await getJson(`/integrations/accounts?workspaceId=${encodeURIComponent(workspaceId)}`, token);
  const byPlatform = Object.fromEntries(((accounts?.items || []) as any[]).map((a) => [String(a.platform), Boolean(a.connected)]));

  return NextResponse.json({
    workspaceId,
    onboardingComplete,
    avatarComplete,
    connections: {
      x: Boolean(byPlatform.x),
      linkedin: Boolean(byPlatform.linkedin),
      instagram: Boolean(byPlatform.instagram),
      youtube: Boolean(byPlatform.youtube),
    },
  });
}

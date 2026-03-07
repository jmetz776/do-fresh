import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_BASE = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const DEFAULT_PROFILE_NAME = process.env.ONBOARDING_VOICE_PROFILE_NAME || 'Harper Premium Voice';

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

  const profiles = await getJson(`/v1/consent/voice/profiles?workspaceId=${encodeURIComponent(workspaceId)}&status=active&limit=50`, token);
  const profileItems = (profiles?.items || []) as Array<any>;
  const preferred = profileItems.find((p) => String(p.displayName || '').toLowerCase() === DEFAULT_PROFILE_NAME.toLowerCase()) || profileItems[0] || null;

  if (!preferred) {
    return NextResponse.json({
      workspaceId,
      enabled: false,
      reason: 'no_active_voice_profile',
      profile: null,
      audioBySlide: [],
    });
  }

  const renders = await getJson(`/v1/consent/voice/renders?workspaceId=${encodeURIComponent(workspaceId)}&status=approved&limit=80`, token);
  const renderItems = ((renders?.items || []) as Array<any>)
    .filter((r) => String(r.voiceProfileId || '') === String(preferred.id || ''))
    .sort((a, b) => String(a.createdAt || '').localeCompare(String(b.createdAt || '')));

  const latestFive = renderItems.slice(-5);
  const audioBySlide = latestFive.map((r) => ({
    renderId: r.id,
    audioUrl: `${API_BASE}/v1/consent/voice/renders/${encodeURIComponent(String(r.id))}/audio`,
    createdAt: r.createdAt,
  }));

  return NextResponse.json({
    workspaceId,
    enabled: audioBySlide.length > 0,
    profile: {
      id: preferred.id,
      displayName: preferred.displayName,
      providerVoiceId: preferred.providerVoiceId,
    },
    audioBySlide,
  });
}

import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_BASE = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const DEFAULT_PROFILE_NAME = process.env.ASSIST_VOICE_PROFILE_NAME || process.env.ONBOARDING_VOICE_PROFILE_NAME || 'Harper Premium Voice';

async function getJson(path: string, token: string) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    cache: 'no-store',
  });
  if (!res.ok) return null;
  return res.json();
}

async function postJson(path: string, token: string, body: object) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    cache: 'no-store',
  });
  if (!res.ok) return null;
  return res.json();
}

export async function POST(req: Request) {
  const c = cookies();
  const token = c.get('do_api_token')?.value || '';
  const workspaceId = c.get('do_workspace_id')?.value || 'default';
  const payload = await req.json().catch(() => ({}));
  const text = String(payload?.text || '').trim();

  if (!text) return NextResponse.json({ ok: false, error: 'missing_text' }, { status: 400 });

  const profiles = await getJson(`/v1/consent/voice/profiles?workspaceId=${encodeURIComponent(workspaceId)}&status=active&limit=50`, token);
  const items = (profiles?.items || []) as Array<any>;
  const profile = items.find((p) => String(p.displayName || '').toLowerCase() === DEFAULT_PROFILE_NAME.toLowerCase()) || items[0] || null;
  if (!profile) return NextResponse.json({ ok: false, error: 'no_active_voice_profile' }, { status: 404 });

  const render = await postJson('/v1/consent/voice/renders', token, {
    workspaceId,
    voiceProfileId: profile.id,
    scriptText: text.slice(0, 700),
  });
  if (!render?.id) return NextResponse.json({ ok: false, error: 'render_failed' }, { status: 502 });

  await postJson(`/v1/consent/voice/renders/${encodeURIComponent(String(render.id))}/approve`, token, {});

  return NextResponse.json({
    ok: true,
    renderId: render.id,
    audioUrl: `${API_BASE}/v1/consent/voice/renders/${encodeURIComponent(String(render.id))}/audio`,
    profile: { id: profile.id, displayName: profile.displayName },
  });
}

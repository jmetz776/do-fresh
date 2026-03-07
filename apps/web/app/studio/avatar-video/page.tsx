import Link from 'next/link';
import type React from 'react';
import { cookies } from 'next/headers';
import { bootstrapSampleVoiceRenderAction, createAvatarVideoQuickAction } from '../../actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const FALLBACK_WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';

async function getJson(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

export default async function AvatarVideoPage({ searchParams }: { searchParams?: { notice?: string; error?: string } }) {
  const c = cookies();
  const workspaceId = c.get('do_workspace_id')?.value || FALLBACK_WORKSPACE_ID;
  const userEmail = (c.get('do_user_email')?.value || '').toLowerCase();
  const operatorAllowlist = new Set(
    String(process.env.AUTH_SUPERUSER_EMAILS || process.env.WEB_SUPERUSER_EMAILS || process.env.AUTH_OWNER_EMAILS || '')
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
  const isOperator = operatorAllowlist.has(userEmail);

  const [templates, approvedVoiceRenders] = await Promise.all([
    getJson('/video/background-templates'),
    getJson(`/v1/consent/voice/renders?workspaceId=${encodeURIComponent(workspaceId)}&limit=25&status=approved`),
  ]);
  const rows = Array.isArray(templates?.items) ? templates.items : [];
  const approvedCount = Array.isArray(approvedVoiceRenders?.items) ? approvedVoiceRenders.items.length : 0;

  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 22, fontFamily: 'Inter, system-ui' }}>
      <div style={{ maxWidth: 860, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <h1 style={{ margin: 0 }}>Avatar Video</h1>
            <p style={{ margin: '6px 0 0', color: '#9fb2d6' }}>Simple flow: paste script, pick scene, generate.</p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Link href="/studio" style={{ color: '#cce5ff' }}>Back to Studio</Link>
            {isOperator ? <Link href="/ops" style={{ color: '#cce5ff' }}>Operator Console ↗</Link> : null}
          </div>
        </div>

        {searchParams?.notice ? <section style={okCard}>✅ {decodeURIComponent(searchParams.notice)}</section> : null}
        {searchParams?.error ? <section style={errCard}>⚠️ {decodeURIComponent(searchParams.error)}</section> : null}

        <section style={flowCard}>
          <h2 style={{ marginTop: 0, marginBottom: 6, letterSpacing: '-.015em', lineHeight: 1.15 }}>Fast Path: Marketplace → Scene → Video</h2>
          <p style={{ color: '#c4d6f7', fontSize: 13, marginTop: 0, lineHeight: 1.45 }}>Use this order for the cleanest customer flow and fewer misfires.</p>
          <div style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))' }}>
            <Link href="/studio/models" style={flowBtn}>1) Pick presenter</Link>
            <Link href="/studio/avatar-video" style={flowBtn}>2) Choose background template</Link>
            <Link href="/studio/review" style={flowBtnMuted}>3) Check background analytics</Link>
          </div>
        </section>

        <section style={card}>
          <h2 style={{ marginTop: 0 }}>Create Avatar Video</h2>
          <p style={{ color: '#9fb2d6', fontSize: 12, marginTop: 0 }}>Approved voice renders available: {approvedCount} · pick a scene and generate in one pass.</p>
          {approvedCount === 0 ? (
            <form action={bootstrapSampleVoiceRenderAction}>
              <input type="hidden" name="workspace_id" value={workspaceId} />
              <button type="submit" style={btnSecondary}>Create sample voice render (one-click)</button>
            </form>
          ) : null}
          <form action={createAvatarVideoQuickAction}>
            <input type="hidden" name="workspace_id" value={workspaceId} />
            <textarea name="script_text" required placeholder="Paste script" style={inputArea} />
            <select name="background_template_id" style={input} defaultValue={rows[0]?.id || ''}>
              <option value="">No scene template</option>
              {rows.map((t: any) => {
                const tier = String(t.tier || 'free').toLowerCase();
                const premium = tier === 'premium' || tier === 'pro';
                return <option key={t.id} value={t.id}>{t.name || t.id} · {premium ? 'PREMIUM' : 'FREE'}</option>;
              })}
            </select>
            <div style={{ marginTop: 8 }}>
              <button type="submit" style={btn}>Generate Avatar Video</button>
            </div>
          </form>
          <p style={{ color: '#9fb2d6', fontSize: 12 }}>Uses latest approved voice render automatically.</p>
        </section>
      </div>
    </main>
  );
}

const card: React.CSSProperties = {
  border: '1px solid rgba(148,163,184,.28)',
  borderRadius: 14,
  background: 'linear-gradient(180deg, rgba(18,28,51,.86), rgba(15,23,42,.72))',
  padding: 16,
  boxShadow: '0 18px 40px rgba(2,6,23,.4)',
};
const flowCard: React.CSSProperties = {
  ...card,
  borderColor: 'rgba(56,189,248,.5)',
  marginBottom: 10,
  background: 'radial-gradient(420px 150px at 10% -20%, rgba(56,189,248,.22), transparent 62%), linear-gradient(180deg, rgba(14,165,233,.2), rgba(15,23,42,.72))',
};
const okCard: React.CSSProperties = { ...card, borderColor: 'rgba(34,197,94,.6)', marginBottom: 10 };
const errCard: React.CSSProperties = { ...card, borderColor: 'rgba(251,113,133,.6)', marginBottom: 10 };
const input: React.CSSProperties = { width: '100%', border: '1px solid rgba(148,163,184,.35)', borderRadius: 10, padding: '10px 12px', background: 'rgba(15,23,42,.55)', color: '#e8eefc', marginTop: 8 };
const inputArea: React.CSSProperties = { ...input, minHeight: 120 };
const btn: React.CSSProperties = { border: '1px solid #0284c7', background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', color: '#062437', borderRadius: 10, padding: '10px 12px', fontWeight: 800, cursor: 'pointer', boxShadow: '0 10px 24px rgba(14,165,233,.28)' };
const btnSecondary: React.CSSProperties = { border: '1px solid rgba(148,163,184,.5)', background: 'rgba(15,23,42,.55)', color: '#dbe7ff', borderRadius: 10, padding: '10px 12px', fontWeight: 700, cursor: 'pointer', marginBottom: 8 };
const flowBtn: React.CSSProperties = {
  color: '#e5f3ff',
  border: '1px solid rgba(56,189,248,.48)',
  borderRadius: 14,
  padding: '11px 13px',
  background: 'linear-gradient(180deg, rgba(56,189,248,.2), rgba(30,41,59,.4))',
  textDecoration: 'none',
  fontWeight: 800,
  letterSpacing: '.01em',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,.11), 0 8px 20px rgba(2,6,23,.32)',
  textAlign: 'center',
};
const flowBtnMuted: React.CSSProperties = {
  ...flowBtn,
  border: '1px solid rgba(148,163,184,.4)',
  background: 'linear-gradient(180deg, rgba(30,41,59,.56), rgba(15,23,42,.48))',
};

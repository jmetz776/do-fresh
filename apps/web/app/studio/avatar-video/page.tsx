import Link from 'next/link';
import type React from 'react';
import { bootstrapSampleVoiceRenderAction, createAvatarVideoQuickAction } from '../../actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';

async function getJson(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

export default async function AvatarVideoPage({ searchParams }: { searchParams?: { notice?: string; error?: string } }) {
  const [templates, approvedVoiceRenders] = await Promise.all([
    getJson('/video/background-templates'),
    getJson(`/v1/consent/voice/renders?workspaceId=${encodeURIComponent(WORKSPACE_ID)}&limit=25&status=approved`),
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
            <Link href="/ops" style={{ color: '#cce5ff' }}>Operator Console ↗</Link>
          </div>
        </div>

        {searchParams?.notice ? <section style={okCard}>✅ {decodeURIComponent(searchParams.notice)}</section> : null}
        {searchParams?.error ? <section style={errCard}>⚠️ {decodeURIComponent(searchParams.error)}</section> : null}

        <section style={card}>
          <h2 style={{ marginTop: 0 }}>Create Avatar Video</h2>
          <p style={{ color: '#9fb2d6', fontSize: 12, marginTop: 0 }}>Approved voice renders available: {approvedCount}</p>
          {approvedCount === 0 ? (
            <form action={bootstrapSampleVoiceRenderAction}>
              <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
              <button type="submit" style={btnSecondary}>Create sample voice render (one-click)</button>
            </form>
          ) : null}
          <form action={createAvatarVideoQuickAction}>
            <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
            <textarea name="script_text" required placeholder="Paste script" style={inputArea} />
            <select name="background_template_id" style={input} defaultValue={rows[0]?.id || ''}>
              <option value="">No scene template</option>
              {rows.map((t: any) => (
                <option key={t.id} value={t.id}>{t.name || t.id} · {t.tier || 'free'}</option>
              ))}
            </select>
            <div style={{ marginTop: 8 }}>
              <button type="submit" style={btn}>Create Video Job</button>
            </div>
          </form>
          <p style={{ color: '#9fb2d6', fontSize: 12 }}>Uses latest approved voice render automatically.</p>
        </section>
      </div>
    </main>
  );
}

const card: React.CSSProperties = { border: '1px solid rgba(148,163,184,.28)', borderRadius: 14, background: 'rgba(15,23,42,.7)', padding: 16 };
const okCard: React.CSSProperties = { ...card, borderColor: 'rgba(34,197,94,.6)', marginBottom: 10 };
const errCard: React.CSSProperties = { ...card, borderColor: 'rgba(251,113,133,.6)', marginBottom: 10 };
const input: React.CSSProperties = { width: '100%', border: '1px solid rgba(148,163,184,.35)', borderRadius: 10, padding: '10px 12px', background: 'rgba(15,23,42,.55)', color: '#e8eefc', marginTop: 8 };
const inputArea: React.CSSProperties = { ...input, minHeight: 120 };
const btn: React.CSSProperties = { border: '1px solid #0284c7', background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', color: '#062437', borderRadius: 10, padding: '10px 12px', fontWeight: 800, cursor: 'pointer' };
const btnSecondary: React.CSSProperties = { border: '1px solid rgba(148,163,184,.5)', background: 'rgba(15,23,42,.55)', color: '#dbe7ff', borderRadius: 10, padding: '10px 12px', fontWeight: 700, cursor: 'pointer', marginBottom: 8 };

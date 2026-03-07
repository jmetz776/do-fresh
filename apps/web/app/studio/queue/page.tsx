import Link from 'next/link';
import { cookies } from 'next/headers';
import type React from 'react';
import { applyCadenceAction, buildUnifiedQueueAction } from '../../actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const FALLBACK_WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';

async function getJson(path: string, headers?: Record<string, string>) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store', headers });
  if (!res.ok) return null;
  return res.json();
}

export default async function UnifiedQueuePage({ searchParams }: { searchParams?: { notice?: string; error?: string } }) {
  const c = cookies();
  const workspaceId = c.get('do_workspace_id')?.value || FALLBACK_WORKSPACE_ID;
  const token = c.get('do_api_token')?.value || '';
  const actorHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const [content, suggestions] = await Promise.all([
    getJson(`/content?workspaceId=${encodeURIComponent(workspaceId)}`, actorHeaders),
    getJson(`/intelligence/suggestions?workspaceId=${encodeURIComponent(workspaceId)}&limit=20&includeBelowThreshold=true`, actorHeaders),
  ]);

  const drafts = (Array.isArray(content) ? content : []).filter((r: any) => r.status === 'draft').slice(0, 60);
  const approved = (Array.isArray(content) ? content : []).filter((r: any) => r.status === 'approved').slice(0, 60);

  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 22, fontFamily: 'Inter, system-ui' }}>
      <div style={{ maxWidth: 980, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <h1 style={{ margin: 0 }}>Unified Queue Builder</h1>
            <p style={{ margin: '6px 0 0', color: '#9fb2d6' }}>One queue. Mixed content plan. Simple customer experience.</p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Link href="/studio" style={{ color: '#cce5ff' }}>Back to Studio</Link>
          </div>
        </div>

        {searchParams?.notice ? <section style={okCard}>✅ {decodeURIComponent(searchParams.notice)}</section> : null}
        {searchParams?.error ? <section style={errCard}>⚠️ {decodeURIComponent(searchParams.error)}</section> : null}

        <section style={card}>
          <h2 style={{ marginTop: 0 }}>1) Build Queue</h2>
          <form action={buildUnifiedQueueAction} className="stack">
            <input type="hidden" name="workspace_id" value={workspaceId} />
            <label style={label}>Idea / campaign objective</label>
            <textarea name="idea" required placeholder="Describe the campaign objective and audience" style={inputArea} />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 8 }}>
              <div>
                <label style={label}>Primary platform</label>
                <select name="platform" style={input} defaultValue="x">
                  <option value="x">X</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="instagram">Instagram</option>
                  <option value="tiktok">TikTok</option>
                  <option value="youtube">YouTube Shorts</option>
                </select>
              </div>
              <div>
                <label style={label}>Queue cap (hard limit)</label>
                <input name="queue_cap" type="number" min={3} max={60} defaultValue={20} style={input} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 8 }}>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={label}>Trend signal (optional, unlocks narrative branches)</label>
                <select name="suggestion_id" style={input} defaultValue="">
                  <option value="">None (use raw idea)</option>
                  {(Array.isArray(suggestions) ? suggestions : []).map((s: any) => (
                    <option key={s.id} value={s.id}>{s.topic} · score {Number(s.finalScore || 0).toFixed(2)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={label}>Objective</label>
                <select name="objective" style={input} defaultValue="engagement">
                  <option value="engagement">Engagement</option>
                  <option value="clicks">Clicks</option>
                  <option value="leads">Leads</option>
                </select>
              </div>
            </div>
            <div>
              <label style={label}>Audience context (optional)</label>
              <input name="audience" defaultValue="general" style={input} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 8 }}>
              <div><label style={label}>Text %</label><input name="mix_text" type="number" min={0} max={100} defaultValue={60} style={input} /></div>
              <div><label style={label}>Faceless %</label><input name="mix_faceless" type="number" min={0} max={100} defaultValue={25} style={input} /></div>
              <div><label style={label}>Avatar %</label><input name="mix_avatar" type="number" min={0} max={100} defaultValue={15} style={input} /></div>
            </div>

            <div>
              <label style={label}>Timezone</label>
              <input name="timezone" defaultValue="America/New_York" style={input} />
            </div>
            <div style={{ marginTop: 8 }}>
              <button type="submit" style={btn}>Build Unified Queue</button>
            </div>
            <p style={{ color: '#9fb2d6', fontSize: 12, marginTop: 8 }}>
              First pass: engine generates text queue now and plans video slots by cap/mix. Video execution remains operator-managed behind the scenes.
            </p>
          </form>
        </section>

        <section style={card}>
          <h2 style={{ marginTop: 0 }}>2) Scheduler Control Panel</h2>
          <p style={{ color: '#9fb2d6', fontSize: 12, marginTop: 0 }}>Apply cadence to approved items while respecting queue cap and tier limits.</p>
          <form action={applyCadenceAction} className="stack">
            <input type="hidden" name="workspace_id" value={workspaceId} />
            <input type="hidden" name="approved_ids" value={approved.map((x: any) => x.id).join(',')} />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 8 }}>
              <div>
                <label style={label}>Cadence</label>
                <select name="cadence" style={input} defaultValue="weekdays">
                  <option value="weekdays">Weekdays (default)</option>
                  <option value="daily">Daily</option>
                  <option value="three_weekly">3x per week</option>
                </select>
              </div>
              <div>
                <label style={label}>Timezone</label>
                <input name="timezone" defaultValue="America/New_York" style={input} />
              </div>
            </div>
            <div style={{ marginTop: 8 }}>
              <button type="submit" style={btnSecondary} disabled={approved.length === 0}>Apply Cadence to Approved Queue</button>
            </div>
          </form>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 10, marginTop: 10 }}>
            <div style={miniCard}>Drafts in queue: <b>{drafts.length}</b></div>
            <div style={miniCard}>Approved ready to schedule: <b>{approved.length}</b></div>
          </div>
        </section>
      </div>
    </main>
  );
}

const card: React.CSSProperties = { border: '1px solid rgba(148,163,184,.28)', borderRadius: 14, background: 'rgba(15,23,42,.7)', padding: 16, marginBottom: 10 };
const okCard: React.CSSProperties = { ...card, borderColor: 'rgba(34,197,94,.6)' };
const errCard: React.CSSProperties = { ...card, borderColor: 'rgba(251,113,133,.6)' };
const miniCard: React.CSSProperties = { border: '1px solid rgba(148,163,184,.28)', borderRadius: 12, background: 'rgba(15,23,42,.55)', padding: 10 };
const label: React.CSSProperties = { display: 'block', marginBottom: 6, fontSize: 12, color: '#9fb2d6' };
const input: React.CSSProperties = { width: '100%', border: '1px solid rgba(148,163,184,.35)', borderRadius: 10, padding: '10px 12px', background: 'rgba(15,23,42,.55)', color: '#e8eefc' };
const inputArea: React.CSSProperties = { ...input, minHeight: 90 };
const btn: React.CSSProperties = { border: '1px solid #0284c7', background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', color: '#062437', borderRadius: 10, padding: '10px 12px', fontWeight: 800, cursor: 'pointer' };
const btnSecondary: React.CSSProperties = { border: '1px solid rgba(148,163,184,.5)', background: 'rgba(15,23,42,.55)', color: '#dbe7ff', borderRadius: 10, padding: '10px 12px', fontWeight: 700, cursor: 'pointer' };

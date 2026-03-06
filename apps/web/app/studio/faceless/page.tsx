"use client";

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type TemplateKey = 'cinematic' | 'explainer' | 'story' | 'problem_solution';

const templates: Record<TemplateKey, { name: string; desc: string }> = {
  cinematic: { name: 'Cinematic Authority', desc: 'High-impact pacing, bold hooks, premium visual beats.' },
  explainer: { name: 'Fast Explainer', desc: 'Clear value in 30-45s with practical call-to-action.' },
  story: { name: 'Story + Lesson', desc: 'Narrative hook, key moment, actionable takeaway.' },
  problem_solution: { name: 'Problem / Solution', desc: 'Pain-first framing with fast credibility and proof.' },
};

export default function FacelessStudioPage() {
  const [contentType, setContentType] = useState<'faceless' | 'avatar' | 'post'>('faceless');
  const [niche, setNiche] = useState('AI marketing');
  const [audience, setAudience] = useState('founders and creators');
  const [goal, setGoal] = useState('leads');
  const [cadence, setCadence] = useState('daily');
  const [template, setTemplate] = useState<TemplateKey>('cinematic');
  const [voiceStyle, setVoiceStyle] = useState('authority');
  const [voiceDnaLabel, setVoiceDnaLabel] = useState('');
  const [sources, setSources] = useState({ reddit: true, youtube: true, x: true, trends: true, firstParty: true });
  const [batchSize, setBatchSize] = useState(10);
  const [status, setStatus] = useState('');
  const [queue, setQueue] = useState<Array<{ title: string; score: number; lane: 'intelligence' | 'premium_render'; script?: string }>>([]);
  const [renderStatus, setRenderStatus] = useState('');
  const [limitLabel, setLimitLabel] = useState('');
  const [backgroundRecs, setBackgroundRecs] = useState<Array<{ id: string; name: string; score: number; tier?: string; mood?: string }>>([]);
  const [selectedBackgroundTemplateId, setSelectedBackgroundTemplateId] = useState('');

  const activeSources = useMemo(() => Object.entries(sources).filter(([, v]) => v).map(([k]) => k), [sources]);

  useEffect(() => {
    (async () => {
      const res = await fetch('/api/faceless/limits', { cache: 'no-store' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return;
      const used = Number(data?.usage?.monthly_count || 0);
      const cap = Number(data?.limits?.monthly_video_cap || 0);
      const plan = String(data?.limits?.plan || 'starter');
      setLimitLabel(`${plan} plan · videos used ${used}/${cap} this month`);
    })();
  }, []);

  function currentWorkspaceId() {
    if (typeof document === 'undefined') return 'default';
    const m = document.cookie.match(/(?:^|; )do_workspace_id=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : 'default';
  }

  async function runBatch() {
    setStatus('Generating batch...');
    const workspaceId = currentWorkspaceId();
    const res = await fetch('/api/faceless/batch/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workspaceId,
        niche,
        audience,
        goal,
        cadence,
        template,
        voiceStyle,
        preferredMood: template === 'cinematic' ? 'bold' : template === 'explainer' ? 'calm' : 'premium',
        platform: 'vertical_9_16',
        sources: activeSources,
        batchSize,
      }),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setStatus(data?.detail || 'Failed to generate faceless batch.');
      return;
    }

    const dna = data?.voiceDna;
    if (dna?.seed) setVoiceDnaLabel(`${dna.style || voiceStyle} · seed ${dna.seed} · pace ${dna.pace} · energy ${dna.energy}`);

    const drafted = (data?.items || []).map((it: any) => ({
      title: it.title,
      score: Number(it?.scores?.render_readiness || 0),
      lane: it.lane,
      script: it.script,
    }));
    const recs = (data?.backgroundRecommendations || []).map((r: any) => ({
      id: String(r?.id || ''),
      name: String(r?.name || r?.id || 'template'),
      score: Number(r?.score || 0),
      tier: r?.tier,
      mood: r?.mood,
    }));
    setBackgroundRecs(recs);
    if (recs.length > 0) setSelectedBackgroundTemplateId(recs[0].id);
    setQueue(drafted);
    const promoted = Number(data?.promotedCount || drafted.filter((d: any) => d.lane === 'premium_render').length);
    setStatus(`Generated ${drafted.length}. Promoted ${promoted} to premium render lane.`);
  }

  async function renderTop3() {
    const top = queue.filter((q) => q.lane === 'premium_render').slice(0, 3);
    const scripts = (top.length ? top : queue.slice(0, 3)).map((q) => q.script).filter(Boolean);
    if (!scripts.length) {
      setRenderStatus('No scripts available to render yet.');
      return;
    }
    const workspaceId = currentWorkspaceId();
    setRenderStatus('Enqueuing top scripts for render...');
    const res = await fetch('/api/faceless/batch/render-top', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspaceId, scripts, topN: 3, selectedBackgroundTemplateId }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setRenderStatus(data?.detail || 'Failed to enqueue renders.');
      return;
    }
    const used = Number(data?.usage?.monthly_count || 0);
    const cap = Number(data?.limits?.monthly_video_cap || 0);
    if (cap > 0) setLimitLabel(`${data?.limits?.plan || 'starter'} plan · videos used ${used}/${cap} this month`);
    setRenderStatus(`Queued ${data?.count || 0} renders. Open Review Theater to preview when ready.`);
  }

  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 22, fontFamily: 'Inter, system-ui' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 34, letterSpacing: '-.02em' }}>Faceless Studio</h1>
            <p style={{ margin: '6px 0 0', color: '#a5b4d4' }}>Premium faceless content pipeline: source → script → gate → render.</p>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Link href="/studio" style={linkBtn}>Back to Studio</Link>
            <Link href="/studio/review" style={linkBtn}>Open Review Theater</Link>
            <button style={{ ...primaryBtn, opacity: contentType === 'faceless' ? 1 : 0.55 }} onClick={runBatch} disabled={contentType !== 'faceless'}>Generate Today’s Faceless Batch</button>
            <button style={{ ...primaryBtn, opacity: (contentType === 'faceless' && queue.length > 0) ? 1 : 0.55 }} onClick={renderTop3} disabled={contentType !== 'faceless' || queue.length === 0}>Render Top 3</button>
          </div>
        </div>

        <section style={card}>
          <h2 style={h2}>Mode Selection</h2>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" onClick={() => setContentType('faceless')} style={{ ...pillBtn, opacity: contentType === 'faceless' ? 1 : 0.65 }}>Faceless Video</button>
            <button type="button" onClick={() => setContentType('avatar')} style={{ ...pillBtn, opacity: contentType === 'avatar' ? 1 : 0.65 }}>Avatar Video</button>
            <button type="button" onClick={() => setContentType('post')} style={{ ...pillBtn, opacity: contentType === 'post' ? 1 : 0.65 }}>Image/Text Post</button>
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: '#9fb2d6' }}>
            {contentType === 'faceless' ? 'Faceless mode: no on-screen presenter.' : contentType === 'avatar' ? 'Avatar mode lives in Presenter flow.' : 'Post mode uses low-cost generation only.'}
          </div>
          {limitLabel ? <div style={{ marginTop: 8, fontSize: 12, color: '#93c5fd' }}>{limitLabel}</div> : null}
        </section>

        <section style={card}>
          <h2 style={h2}>1) Profile Setup</h2>
          <div style={grid2}>
            <input value={niche} onChange={(e) => setNiche(e.target.value)} placeholder="Niche" style={input} />
            <input value={audience} onChange={(e) => setAudience(e.target.value)} placeholder="Audience" style={input} />
            <select value={goal} onChange={(e) => setGoal(e.target.value)} style={input}>
              <option value="leads">Leads</option>
              <option value="authority">Authority</option>
              <option value="views">Views</option>
            </select>
            <select value={cadence} onChange={(e) => setCadence(e.target.value)} style={input}>
              <option value="daily">Daily</option>
              <option value="weekdays">Weekdays</option>
              <option value="three_weekly">3x weekly</option>
            </select>
          </div>
        </section>

        <section style={card}>
          <h2 style={h2}>2) Source Rails</h2>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries({ reddit: 'Reddit', youtube: 'YouTube', x: 'X', trends: 'Google Trends', firstParty: 'Your Winners' }).map(([k, label]) => (
              <label key={k} style={chip}>
                <input
                  type="checkbox"
                  checked={(sources as any)[k]}
                  onChange={(e) => setSources((s) => ({ ...s, [k]: e.target.checked }))}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: '#9fb2d6' }}>Active sources: {activeSources.join(', ') || 'none'}</div>
        </section>

        <section style={card}>
          <h2 style={h2}>3) Template + Batch Control</h2>
          <div style={grid2}>
            <select value={template} onChange={(e) => setTemplate(e.target.value as TemplateKey)} style={input}>
              {Object.entries(templates).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}
            </select>
            <select value={String(batchSize)} onChange={(e) => setBatchSize(Number(e.target.value))} style={input}>
              <option value="6">6 scripts</option>
              <option value="10">10 scripts</option>
              <option value="15">15 scripts</option>
            </select>
            <select value={voiceStyle} onChange={(e) => setVoiceStyle(e.target.value)} style={input}>
              <option value="authority">Voice Style: Authority</option>
              <option value="explainer">Voice Style: Explainer</option>
              <option value="story">Voice Style: Story</option>
            </select>
          </div>
          <div style={{ marginTop: 8, color: '#c7d2ee', fontSize: 13 }}>{templates[template].desc}</div>
          {voiceDnaLabel ? <div style={{ marginTop: 6, color: '#93c5fd', fontSize: 12 }}>Workspace Voice DNA: {voiceDnaLabel}</div> : null}
          {backgroundRecs.length > 0 ? (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 12, color: '#9fb2d6', marginBottom: 6 }}>Recommended background templates:</div>
              <select
                value={selectedBackgroundTemplateId}
                onChange={(e) => setSelectedBackgroundTemplateId(e.target.value)}
                style={{ ...input, marginBottom: 8 }}
              >
                {backgroundRecs.map((r) => (
                  <option key={r.id} value={r.id}>{r.name} · {Math.round(r.score * 100)}%</option>
                ))}
              </select>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {backgroundRecs.map((r) => (
                  <span key={r.id} style={chipStat}>{r.name} · {Math.round(r.score * 100)}% · {r.tier || 'free'}</span>
                ))}
              </div>
            </div>
          ) : null}
        </section>

        <section style={card}>
          <h2 style={h2}>4) Queue Preview</h2>
          <div style={{ marginBottom: 8, fontSize: 12, color: '#9fb2d6' }}>Expected render time after enqueue: usually under 10 minutes, occasionally up to 20.</div>
          {status ? <div style={{ marginBottom: 8, color: '#86efac', fontSize: 13 }}>{status}</div> : null}
          {renderStatus ? <div style={{ marginBottom: 8, color: '#7dd3fc', fontSize: 13 }}>{renderStatus}</div> : null}
          {queue.length === 0 ? (
            <div style={{ color: '#9fb2d6', fontSize: 13 }}>No batch yet. Generate one to preview routing decisions.</div>
          ) : (
            <>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                <span style={chipStat}>total: {queue.length}</span>
                <span style={chipStat}>premium: {queue.filter((q) => q.lane === 'premium_render').length}</span>
                <span style={chipStat}>rewrite: {queue.filter((q) => q.lane === 'intelligence').length}</span>
              </div>
              <div style={{ display: 'grid', gap: 8 }}>
                {queue.map((q, i) => (
                  <div key={i} style={{ border: '1px solid rgba(148,163,184,.24)', borderRadius: 10, padding: 10, background: 'rgba(2,6,23,.35)', display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                    <div style={{ fontSize: 13 }}>{q.title}</div>
                    <div style={{ fontSize: 12, color: '#c7d2ee' }}>score {q.score} · {q.lane === 'premium_render' ? 'premium lane' : 'rewrite lane'}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}

const card: React.CSSProperties = {
  border: '1px solid rgba(148,163,184,.28)',
  borderRadius: 14,
  background: 'linear-gradient(180deg, rgba(18,28,51,.86), rgba(15,23,42,.68))',
  padding: 16,
  marginBottom: 12,
};
const h2: React.CSSProperties = { marginTop: 0, marginBottom: 10, fontSize: 20 };
const grid2: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 8 };
const input: React.CSSProperties = { border: '1px solid rgba(148,163,184,.35)', borderRadius: 10, padding: '10px 12px', background: 'rgba(15,23,42,.55)', color: '#e8eefc' };
const primaryBtn: React.CSSProperties = { border: '1px solid #0284c7', background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', color: '#062437', borderRadius: 10, padding: '10px 12px', fontWeight: 800, cursor: 'pointer' };
const linkBtn: React.CSSProperties = { border: '1px solid rgba(148,163,184,.35)', background: 'rgba(15,23,42,.55)', color: '#e8eefc', borderRadius: 10, padding: '10px 12px', textDecoration: 'none' };
const chip: React.CSSProperties = { border: '1px solid rgba(148,163,184,.35)', borderRadius: 999, padding: '7px 10px', display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: 13, background: 'rgba(15,23,42,.45)' };
const chipStat: React.CSSProperties = { border: '1px solid rgba(148,163,184,.28)', borderRadius: 999, padding: '4px 10px', fontSize: 12, color: '#c7d2ee', background: 'rgba(15,23,42,.55)' };
const pillBtn: React.CSSProperties = { border: '1px solid rgba(56,189,248,.45)', background: 'rgba(14,165,233,.15)', color: '#dbeafe', borderRadius: 999, padding: '8px 12px', cursor: 'pointer', fontSize: 13, fontWeight: 700 };

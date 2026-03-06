import Link from 'next/link';
import {
  approveContentAction,
  createSourceAction,
  generateContentAction,
  normalizeSourceAction,
  runPublishAction,
  scheduleContentAction,
  retryFailedPublishAction,
  retryOneFailedPublishAction,
  updateContentAction,
  regenerateContentAction,
  apifyRunAction,
  apifyImportRunAction,
  importTrendSuggestionsAction,
  feedbackTrendSuggestionAction,
  approveXDraftAction,
  sendXDraftAction,
  createInviteAction,
  saveModelPreferencesAction,
  createVoiceProfileAction,
  createVoiceRenderAction,
  deleteVoiceProfileAction,
  approveVoiceRenderAction,
  retryVoiceRenderAction,
  createVideoRenderAction,
  approveVideoRenderAction,
  retryVideoRenderAction,
  refreshVideoRenderAction,
  refreshQueuedVideoRendersAction,
} from '../actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';

async function getJson(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

function toLocalDatetimeInputValue(minutesFromNow = 5) {
  const d = new Date(Date.now() + minutesFromNow * 60_000);
  const pad = (n: number) => `${n}`.padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatTs(ts?: string) {
  if (!ts) return '—';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

function isHttpUrl(v?: string) {
  if (!v) return false;
  return v.startsWith('http://') || v.startsWith('https://');
}

export default async function OpsPage({ searchParams }: { searchParams?: { apifyRunId?: string; sourceId?: string; invite?: string; video_notice?: string; video_error?: string } }) {
  const [dashboard, sources, content, schedules, failedPublishes, publishJobs, apifyHealth, heygenHealth, trendSuggestions, xDrafts, models, modelPrefs, costsSummary, voiceProfiles, voiceRenders, videoRenders, backgroundTemplates] = await Promise.all([
    getJson(`/dashboard?workspaceId=${WORKSPACE_ID}`),
    getJson(`/sources?workspaceId=${WORKSPACE_ID}`),
    getJson(`/content?workspaceId=${WORKSPACE_ID}`),
    getJson(`/schedules?workspaceId=${WORKSPACE_ID}`),
    getJson(`/publish/failed?workspaceId=${WORKSPACE_ID}`),
    getJson(`/publish/jobs?workspaceId=${WORKSPACE_ID}`),
    getJson('/integrations/apify/health'),
    getJson('/integrations/heygen/health'),
    getJson(`/intelligence/suggestions?workspaceId=${encodeURIComponent(WORKSPACE_ID)}&limit=20`),
    getJson('/integrations/x/drafts?status=draft&limit=12'),
    getJson('/integrations/models'),
    getJson(`/integrations/models/preferences?workspaceId=${encodeURIComponent(WORKSPACE_ID)}`),
    getJson(`/costs/summary?workspaceId=${encodeURIComponent(WORKSPACE_ID)}&limit=1000`),
    getJson(`/v1/consent/voice/profiles?workspaceId=${encodeURIComponent(WORKSPACE_ID)}&limit=50`),
    getJson(`/v1/consent/voice/renders?workspaceId=${encodeURIComponent(WORKSPACE_ID)}&limit=12`),
    getJson(`/v1/consent/video/renders?workspaceId=${encodeURIComponent(WORKSPACE_ID)}&limit=12`),
    getJson('/video/background-templates'),
  ]);

  const latestSource = Array.isArray(sources) && sources.length > 0 ? sources[0] : null;
  const sourceItems = latestSource ? ((await getJson(`/sources/${latestSource.id}/items`)) as Array<any>) : [];
  const defaultPublishAt = toLocalDatetimeInputValue(5);

  return (
    <main className="ops-root">
      <style>{`
        :root {
          --bg: #05070f;
          --surface: #0b1120;
          --surface-2: #111a31;
          --text: #eaf0ff;
          --muted: #99a8ca;
          --border: rgba(148,163,184,.24);
          --primary: #86efac;
          --primary-ink: #052e16;
          --accent: #7dd3fc;
          --danger: #fb7185;
          --radius: 14px;
        }
        .ops-root {
          min-height: 100vh;
          background:
            radial-gradient(900px 420px at -10% -20%, rgba(56,189,248,.18), transparent 65%),
            radial-gradient(900px 450px at 110% -10%, rgba(34,197,94,.12), transparent 60%),
            var(--bg);
          color: var(--text);
          padding: 22px;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
        }
        .wrap { max-width: 1180px; margin: 0 auto; }
        .topbar { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom: 14px; }
        .title h1 { margin: 0; font-size: 30px; letter-spacing: -.01em; }
        .title p { margin: 4px 0 0; color: var(--muted); }
        .badge {
          display:inline-flex; align-items:center; gap:8px;
          border:1px solid rgba(134,239,172,.34); background: rgba(134,239,172,.08); color: var(--primary);
          border-radius: 999px; padding: 6px 12px; font-size: 12px;
        }
        .pulse { width:7px; height:7px; border-radius:999px; background: var(--primary); box-shadow: 0 0 10px var(--primary); animation: pulse 1.7s infinite; }
        @keyframes pulse { 0%,100%{opacity:.45}50%{opacity:1} }

        .stats { display:grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap: 10px; margin-bottom: 14px; }
        .stat { border:1px solid var(--border); border-radius: 12px; padding: 10px; background: rgba(15,23,42,.55); }
        .stat .k { font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: .07em; }
        .stat .v { font-size: 24px; font-weight: 800; margin-top: 2px; }

        .grid { display:grid; grid-template-columns: 1.35fr .95fr; gap: 12px; }
        .stack { display:grid; gap: 12px; }
        .card {
          border:1px solid var(--border);
          border-radius: var(--radius);
          background: linear-gradient(180deg, rgba(15,23,42,.78), rgba(15,23,42,.48));
          padding: 14px;
          transition: transform .18s ease, border-color .2s ease;
        }
        .card:hover { transform: translateY(-1px); border-color: rgba(125,211,252,.42); }
        .card h2 { margin: 0 0 10px; font-size: 18px; }
        .tiny { font-size: 12px; color: var(--muted); }

        .row { display:flex; gap: 8px; flex-wrap: wrap; align-items:center; }
        input, textarea, select, button {
          border-radius: 10px;
          border: 1px solid rgba(148,163,184,.35);
          background: rgba(2,6,23,.5);
          color: #eaf0ff;
          padding: 9px 10px;
          font: inherit;
        }
        input, textarea, select { width: 100%; }
        textarea { resize: vertical; min-height: 84px; }
        button {
          width: auto;
          cursor: pointer;
          transition: transform .12s ease, box-shadow .18s ease, background .18s ease;
        }
        button:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(125,211,252,.18); }
        .btn-primary {
          background: var(--primary);
          color: var(--primary-ink);
          border-color: rgba(134,239,172,.7);
          font-weight: 800;
        }
        .btn-danger { border-color: rgba(251,113,133,.55); color: #ffdbe2; }

        .step-line {
          display:flex; gap:8px; flex-wrap:wrap; margin-bottom: 12px;
        }
        .chip {
          border:1px solid var(--border); border-radius: 999px; padding: 5px 10px; font-size: 12px; color: #c8d4f0;
          background: rgba(15,23,42,.56);
        }

        .list { list-style: none; padding: 0; margin: 0; display:grid; gap: 8px; }
        .item {
          border:1px solid rgba(148,163,184,.22);
          border-radius: 12px;
          padding: 10px;
          background: rgba(2,6,23,.35);
        }
        .meta { font-size: 12px; color: var(--muted); }
        .link { color: #cce5ff; text-decoration: none; }

        @media (max-width: 980px) { .grid { grid-template-columns: 1fr; } }
        @media (prefers-reduced-motion: reduce) { * { animation:none !important; transition:none !important; } }
      `}</style>

      <div className="wrap">
        <div className="topbar">
          <div className="title">
            <h1>DO Operator Console</h1>
            <p>Seamless content workflow, with audit + recovery built in.</p>
          </div>
          <div className="row">
            <span className="badge"><span className="pulse" /> Workspace: {WORKSPACE_ID}</span>
            <Link className="link" href="/auth/superuser-bypass">Force Enter Studio ↗</Link>
            <Link className="link" href="/waitlist">Waitlist ↗</Link>
          </div>
        </div>

        {searchParams?.invite ? (
          <section className="card" style={searchParams.invite.startsWith('ok') ? { marginBottom: 10, borderColor: 'rgba(34,197,94,.55)' } : { marginBottom: 10, borderColor: 'rgba(251,113,133,.55)' }}>
            <h2 style={{ marginBottom: 6 }}>{searchParams.invite.startsWith('ok') ? 'Invite created' : 'Invite failed'}</h2>
            <div className="tiny">{searchParams.invite.startsWith('ok') ? 'Tester invite created successfully.' : decodeURIComponent(String(searchParams.invite || '').replace(/^error:[^:]*:/, ''))}</div>
          </section>
        ) : null}

        {searchParams?.video_notice ? (
          <section className="card" style={{ marginBottom: 10, borderColor: 'rgba(34,197,94,.55)' }}>
            <h2 style={{ marginBottom: 6 }}>Video action completed</h2>
            <div className="tiny">{decodeURIComponent(String(searchParams.video_notice))}</div>
          </section>
        ) : null}

        {searchParams?.video_error ? (
          <section className="card" style={{ marginBottom: 10, borderColor: 'rgba(251,113,133,.55)' }}>
            <h2 style={{ marginBottom: 6 }}>Video action failed</h2>
            <div className="tiny">{decodeURIComponent(String(searchParams.video_error))}</div>
          </section>
        ) : null}

        {(searchParams?.apifyRunId || searchParams?.sourceId) ? (
          <section className="card" style={{ marginBottom: 10 }}>
            <h2 style={{ marginBottom: 6 }}>Latest Apify Action</h2>
            <div className="tiny">
              runId: <b>{searchParams?.apifyRunId || 'n/a'}</b>
              {searchParams?.sourceId ? <> · sourceId: <b>{searchParams.sourceId}</b></> : null}
            </div>
          </section>
        ) : null}

        <div className="step-line">
          <span className="chip">1. Ingest</span>
          <span className="chip">2. Normalize</span>
          <span className="chip">3. Generate</span>
          <span className="chip">4. Approve</span>
          <span className="chip">5. Schedule</span>
          <span className="chip">6. Publish + Recover</span>
        </div>

        <section className="stats">
          {['draft', 'approved', 'scheduled', 'published', 'failed'].map((k) => (
            <div key={k} className="stat">
              <div className="k">{k}</div>
              <div className="v">{dashboard?.[k] || 0}</div>
            </div>
          ))}
        </section>

        <div className="grid">
          <div className="stack">
            <section className="card">
              <h2>1) Create Source</h2>
              <form action={createSourceAction}>
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <div className="row" style={{ marginBottom: 8 }}>
                  <select name="type" defaultValue="csv" style={{ maxWidth: 160 }}>
                    <option value="csv">CSV</option>
                    <option value="url">URL</option>
                  </select>
                  <button className="btn-primary" type="submit">Create Source</button>
                </div>
                <textarea
                  name="raw_payload"
                  placeholder={'CSV: title,body\nMy title,My body\n\nor paste URL when type=url'}
                  required
                />
              </form>
            </section>

            <section className="card">
              <h2>2) Normalize + Generate</h2>
              {!latestSource ? (
                <p className="tiny">No source yet — create one above.</p>
              ) : (
                <>
                  <div className="meta">Latest source: <code>{latestSource.id}</code> · status: <b>{latestSource.status}</b></div>
                  <div className="row" style={{ marginTop: 8 }}>
                    <form action={normalizeSourceAction}>
                      <input type="hidden" name="source_id" value={latestSource.id} />
                      <button type="submit">Normalize Source</button>
                    </form>
                  </div>
                  <div className="tiny" style={{ marginTop: 8 }}>Source Items: {sourceItems?.length || 0}</div>

                  {sourceItems?.length > 0 && (
                    <form action={generateContentAction} className="row" style={{ marginTop: 10 }}>
                      <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                      <select name="source_item_id" defaultValue={sourceItems[0].id} style={{ minWidth: 220, flex: 2 }}>
                        {sourceItems.map((s: any) => (
                          <option key={s.id} value={s.id}>{s.title || s.id}</option>
                        ))}
                      </select>
                      <input name="channels" defaultValue="x,linkedin" placeholder="x,linkedin" style={{ maxWidth: 180 }} />
                      <input name="variant_count" defaultValue="1" type="number" min={1} max={10} style={{ maxWidth: 95 }} />
                      <button className="btn-primary" type="submit">Generate</button>
                    </form>
                  )}
                </>
              )}
            </section>

            <section className="card">
              <h2>3) Content Queue</h2>
              {!Array.isArray(content) || content.length === 0 ? (
                <p className="tiny">No content yet.</p>
              ) : (
                <ul className="list">
                  {content.map((c: any) => (
                    <li key={c.id} className="item">
                      <div><b>{c.channel}</b> · <i>{c.status}</i> · {c.title}</div>
                      <div className="meta" style={{ marginTop: 4 }}>{c.caption}</div>

                      <form action={updateContentAction} className="stack" style={{ marginTop: 8 }}>
                        <input type="hidden" name="content_id" value={c.id} />
                        <input name="title" defaultValue={c.title || ''} placeholder="Title" />
                        <input name="hook" defaultValue={c.hook || ''} placeholder="Hook" />
                        <textarea name="caption" defaultValue={c.caption || ''} rows={3} />
                        <div className="row">
                          <button type="submit">Save Edit</button>
                        </div>
                      </form>

                      <form action={regenerateContentAction} className="row" style={{ marginTop: 8 }}>
                        <input type="hidden" name="content_id" value={c.id} />
                        <input name="guidance" placeholder="Regenerate guidance (optional)" />
                        <button type="submit">Regenerate</button>
                      </form>

                      <div className="row" style={{ marginTop: 8 }}>
                        {c.status === 'draft' && (
                          <form action={approveContentAction}>
                            <input type="hidden" name="content_id" value={c.id} />
                            <button className="btn-primary" type="submit">Approve</button>
                          </form>
                        )}
                        {(c.status === 'approved' || c.status === 'draft') && (
                          <form action={scheduleContentAction} className="row">
                            <input type="hidden" name="content_id" value={c.id} />
                            <input name="publish_at" type="datetime-local" defaultValue={defaultPublishAt} required style={{ maxWidth: 210 }} />
                            <input name="timezone" defaultValue="America/New_York" style={{ maxWidth: 180 }} />
                            <button type="submit">Schedule</button>
                          </form>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <div className="stack">
            <section className="card">
              <h2>4) Publish Control</h2>
              <form action={runPublishAction}>
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <button className="btn-primary" type="submit">Run Publisher Now</button>
              </form>
              <div className="tiny" style={{ marginTop: 8 }}>
                Scheduled items: {Array.isArray(schedules) ? schedules.length : 0}
              </div>
              {!!Array.isArray(schedules) && schedules.length > 0 && (
                <ul className="list" style={{ marginTop: 10 }}>
                  {schedules.slice(0, 8).map((s: any) => (
                    <li className="item" key={s.id}>{formatTs(s.publishAt)} · {s.channel} · <i>{s.status}</i></li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card">
              <h2>Model Selection</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Mode: {modelPrefs?.mode || 'auto'} (Auto is recommended for most users)
              </div>
              <form action={saveModelPreferencesAction} className="stack">
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <div className="row">
                  <select name="mode" defaultValue={modelPrefs?.mode || 'auto'} style={{ maxWidth: 220 }}>
                    <option value="auto">Auto (recommended)</option>
                    <option value="advanced">Advanced (manual)</option>
                  </select>
                </div>
                <div className="row">
                  <select name="text_model_id" defaultValue={modelPrefs?.overrides?.text || ''} style={{ minWidth: 280 }}>
                    <option value="">Auto text model</option>
                    {(models?.items || []).filter((m: any) => (m.capabilities || []).includes('text')).map((m: any) => (
                      <option key={m.id} value={m.id}>{m.display_name} ({m.id})</option>
                    ))}
                  </select>
                  <select name="image_model_id" defaultValue={modelPrefs?.overrides?.image || ''} style={{ minWidth: 280 }}>
                    <option value="">Auto image model</option>
                    {(models?.items || []).filter((m: any) => (m.capabilities || []).includes('image')).map((m: any) => (
                      <option key={m.id} value={m.id}>{m.display_name} ({m.id})</option>
                    ))}
                  </select>
                  <select name="video_model_id" defaultValue={modelPrefs?.overrides?.video || ''} style={{ minWidth: 280 }}>
                    <option value="">Auto video model</option>
                    {(models?.items || []).filter((m: any) => (m.capabilities || []).includes('video')).map((m: any) => (
                      <option key={m.id} value={m.id}>{m.display_name} ({m.id})</option>
                    ))}
                  </select>
                </div>
                <div className="row">
                  <button className="btn-primary" type="submit">Save Model Preferences</button>
                </div>
              </form>
            </section>

            <section className="card">
              <h2>Cost Snapshot (Estimated)</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Events tracked: {costsSummary?.events || 0}
              </div>
              <div><b>Total est. cost:</b> ${Number(costsSummary?.estimatedCostUsd || 0).toFixed(4)}</div>
              <div className="tiny" style={{ marginTop: 6 }}>
                By model: {Object.entries(costsSummary?.byModel || {}).map(([k, v]) => `${k}: $${Number(v).toFixed(4)}`).join(' · ') || 'n/a'}
              </div>
            </section>

            <section className="card">
              <h2>Voice Studio (ElevenLabs)</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Profiles: {Array.isArray(voiceProfiles?.items) ? voiceProfiles.items.length : 0}
              </div>

              {(!Array.isArray(voiceProfiles?.items) || voiceProfiles.items.length === 0) && (
                <form action={createVoiceProfileAction} className="stack" style={{ marginBottom: 10 }}>
                  <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                  <input name="full_name" placeholder="Full name" required />
                  <input name="email" placeholder="Email" required />
                  <input name="display_name" placeholder="Voice display name" defaultValue="Jared Narration" />
                  <input name="provider_voice_id" placeholder="ElevenLabs voice ID" required />
                  <div className="row">
                    <button type="submit">Create Voice Profile</button>
                  </div>
                </form>
              )}

              <form action={createVoiceRenderAction} className="stack">
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <select name="voice_profile_id" defaultValue={(voiceProfiles?.items || [])[0]?.id || ''} required>
                  {(voiceProfiles?.items || []).map((v: any) => (
                    <option key={v.id} value={v.id}>{v.displayName} · {v.provider} · {v.status}</option>
                  ))}
                </select>
                <textarea name="script_text" placeholder="Paste script for voice render" required />
                <div className="row">
                  <button className="btn-primary" type="submit">Render Voice</button>
                </div>
              </form>

              {Array.isArray(voiceProfiles?.items) && voiceProfiles.items.length > 0 ? (
                <ul className="list" style={{ marginTop: 10 }}>
                  {voiceProfiles.items.map((v: any) => (
                    <li className="item" key={v.id}>
                      <div><b>{v.displayName}</b> · {v.provider} · {v.status}</div>
                      <div className="meta">id {v.id}{v.providerVoiceId ? ` · voice ${v.providerVoiceId}` : ''}</div>
                      {v.status !== 'disabled' ? (
                        <form action={deleteVoiceProfileAction} style={{ marginTop: 8 }}>
                          <input type="hidden" name="voice_profile_id" value={v.id} />
                          <button type="submit">Disable / Clear Voice ID</button>
                        </form>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : null}

              {!Array.isArray(voiceRenders?.items) || voiceRenders.items.length === 0 ? (
                <p className="tiny" style={{ marginTop: 8 }}>No voice renders yet.</p>
              ) : (
                <ul className="list" style={{ marginTop: 10 }}>
                  {voiceRenders.items.map((r: any) => (
                    <li className="item" key={r.id}>
                      <div><b>{r.status}</b> · ${Number(r.estimatedCostUsd || 0).toFixed(4)}</div>
                      <div className="meta">created {formatTs(r.createdAt)} · updated {formatTs(r.updatedAt)}</div>
                      {r.status !== 'failed' ? (
                        <audio controls preload="none" src={`${API_BASE}/v1/consent/voice/renders/${r.id}/audio`} style={{ width: '100%', marginTop: 6 }} />
                      ) : (
                        <div className="meta" style={{ marginTop: 6 }}>error: {r.error || 'unknown'}</div>
                      )}
                      {r.status === 'succeeded' && (
                        <form action={approveVoiceRenderAction} style={{ marginTop: 8 }}>
                          <input type="hidden" name="render_id" value={r.id} />
                          <button type="submit">Approve Voice Render</button>
                        </form>
                      )}
                      {r.status === 'failed' && (
                        <form action={retryVoiceRenderAction} style={{ marginTop: 8 }}>
                          <input type="hidden" name="render_id" value={r.id} />
                          <button type="submit">Retry Voice Render</button>
                        </form>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card">
              <h2>Video Queue (Stub)</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Build from approved voice renders
              </div>
              <form action={createVideoRenderAction} className="stack">
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <select name="voice_render_id" defaultValue={(voiceRenders?.items || []).find((r: any) => r.status === 'approved')?.id || ''} required>
                  {(voiceRenders?.items || []).filter((r: any) => r.status === 'approved').map((r: any) => (
                    <option key={r.id} value={r.id}>{r.id} · approved · ${Number(r.estimatedCostUsd || 0).toFixed(4)}</option>
                  ))}
                </select>
                <textarea name="script_text" placeholder="Optional override script for video stub" />
                <select name="background_template_id" defaultValue="">
                  <option value="">Avatar Scene Template (optional)</option>
                  {(backgroundTemplates?.items || []).map((t: any) => (
                    <option key={t.id} value={t.id}>{t.name || t.id} · {t.tier || 'free'} · {t.mood || 'premium'}</option>
                  ))}
                </select>
                <div className="row">
                  <button className="btn-primary" type="submit">Create Video Job</button>
                </div>
              </form>

              <form action={refreshQueuedVideoRendersAction} className="row" style={{ marginTop: 8 }}>
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <button type="submit">Refresh All Queued Jobs</button>
              </form>

              {!Array.isArray(videoRenders?.items) || videoRenders.items.length === 0 ? (
                <p className="tiny" style={{ marginTop: 8 }}>No video jobs yet.</p>
              ) : (
                <ul className="list" style={{ marginTop: 10 }}>
                  {videoRenders.items.map((v: any) => (
                    <li className="item" key={v.id}>
                      <div><b>{v.status}</b> · ${Number(v.estimatedCostUsd || 0).toFixed(4)} · provider: {v.provider || 'n/a'}</div>
                      {v.backgroundTemplateId ? <div className="meta">scene template: {v.backgroundTemplateId}</div> : null}
                      <div className="meta">created {formatTs(v.createdAt)} · updated {formatTs(v.updatedAt)}{v.providerJobId ? ` · job ${v.providerJobId}` : ''}</div>
                      {isHttpUrl(v.videoUri) ? (
                        <div style={{ marginTop: 8 }}>
                          <video controls preload="metadata" style={{ width: '100%', borderRadius: 10 }} src={v.videoUri} />
                          <div className="meta" style={{ marginTop: 6 }}>
                            <a className="link" href={v.videoUri} target="_blank" rel="noreferrer">Open video in new tab ↗</a>
                          </div>
                        </div>
                      ) : (
                        <div className="meta" style={{ marginTop: 6 }}>{v.videoUri || 'No artifact yet'}</div>
                      )}
                      {v.status === 'queued' && (
                        <form action={refreshVideoRenderAction} style={{ marginTop: 8 }}>
                          <input type="hidden" name="render_id" value={v.id} />
                          <button className="btn-primary" type="submit">Refresh Video Status</button>
                        </form>
                      )}
                      {v.status === 'succeeded' && (
                        <form action={approveVideoRenderAction} style={{ marginTop: 8 }}>
                          <input type="hidden" name="render_id" value={v.id} />
                          <button className="btn-primary" type="submit">Approve Video Job</button>
                        </form>
                      )}
                      {v.status === 'failed' && (
                        <form action={retryVideoRenderAction} style={{ marginTop: 8 }}>
                          <input type="hidden" name="render_id" value={v.id} />
                          <button type="submit">Retry Video Job</button>
                        </form>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card">
              <h2>HeyGen Integration</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Status: {heygenHealth?.configured ? 'Configured' : 'Not configured'} · Base: {heygenHealth?.baseUrl || 'n/a'}
              </div>
              <div className="tiny">
                Avatar ID: {heygenHealth?.avatarId || 'missing'} · Voice ID: {heygenHealth?.voiceId || 'optional'}
              </div>
              {!heygenHealth?.configured ? (
                <div className="tiny" style={{ marginTop: 8 }}>
                  Set <code>HEYGEN_API_KEY</code> and <code>HEYGEN_AVATAR_ID</code> in API env, then redeploy.
                </div>
              ) : null}
            </section>

            <section className="card">
              <h2>Apify Signal Intake</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Status: {apifyHealth?.configured ? 'Configured' : 'Not configured'} · Base: {apifyHealth?.baseUrl || 'n/a'}
              </div>
              <form action={apifyRunAction} className="stack">
                <input name="actor_id" placeholder="Actor ID (e.g. apidojo/tweet-scraper)" required />
                <textarea name="actor_input_json" rows={3} placeholder='Actor input JSON, e.g. {"searchTerms":["demand generation"]}' />
                <div className="row">
                  <button className="btn-primary" type="submit">Run Apify Actor</button>
                </div>
              </form>
              <form action={apifyImportRunAction} className="row" style={{ marginTop: 10 }}>
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <input name="run_id" placeholder="Run ID to import" required style={{ minWidth: 220 }} />
                <input name="limit" defaultValue="100" type="number" min={1} max={1000} style={{ maxWidth: 90 }} />
                <button type="submit">Import Run → Sources</button>
              </form>
            </section>

            <section className="card">
              <h2>Trend → Brand Intelligence</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Ranked suggestions with default quality gating.
              </div>
              <form action={importTrendSuggestionsAction} className="row" style={{ marginBottom: 10 }}>
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <input name="source_id" placeholder="Source ID to import suggestions from" required style={{ minWidth: 220 }} />
                <input name="limit" defaultValue="100" type="number" min={1} max={500} style={{ maxWidth: 90 }} />
                <button type="submit">Import Suggestions</button>
              </form>
              {!Array.isArray(trendSuggestions) || trendSuggestions.length === 0 ? (
                <p className="tiny">No qualified suggestions yet. Import from a fresh source.</p>
              ) : (
                <ul className="list">
                  {trendSuggestions.map((s: any) => (
                    <li className="item" key={s.id}>
                      <div><b>{s.topic}</b></div>
                      <div className="meta" style={{ marginTop: 4 }}>
                        final {Number(s.finalScore || 0).toFixed(3)} · risk {Number(s.policyRiskScore || 0).toFixed(2)} · {s.source}
                      </div>
                      <div className="tiny" style={{ marginTop: 6 }}>{s.whyNow}</div>
                      <div className="row" style={{ marginTop: 8 }}>
                        <form action={feedbackTrendSuggestionAction}>
                          <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                          <input type="hidden" name="suggestion_id" value={s.id} />
                          <input type="hidden" name="event_type" value="accepted" />
                          <button className="btn-primary" type="submit">Accept</button>
                        </form>
                        <form action={feedbackTrendSuggestionAction}>
                          <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                          <input type="hidden" name="suggestion_id" value={s.id} />
                          <input type="hidden" name="event_type" value="rejected" />
                          <button type="submit">Reject</button>
                        </form>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card">
              <h2>Beta Invites (Superuser)</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Create tester invites from console. Requires superuser email authorization.
              </div>
              <form action={createInviteAction} className="stack">
                <input name="email" type="email" placeholder="tester@example.com" required />
                <input name="workspace_name" defaultValue="Tester Workspace" placeholder="Workspace name" />
                <div className="row">
                  <select name="role" defaultValue="owner" style={{ maxWidth: 180 }}>
                    <option value="owner">owner</option>
                    <option value="admin">admin</option>
                    <option value="editor">editor</option>
                    <option value="publisher">publisher</option>
                    <option value="viewer">viewer</option>
                  </select>
                  <input name="expires_in_hours" type="number" defaultValue="168" min={1} max={2160} style={{ maxWidth: 140 }} />
                  <input name="max_uses" type="number" defaultValue="1" min={1} max={10} style={{ maxWidth: 100 }} />
                </div>
                <div className="row">
                  <button className="btn-primary" type="submit">Create Invite</button>
                </div>
              </form>
            </section>

            <section className="card">
              <h2>X Reply Draft Queue</h2>
              <div className="tiny" style={{ marginBottom: 8 }}>
                Drafts: {Array.isArray(xDrafts?.items) ? xDrafts.items.length : 0} · Auto reply: {xDrafts?.autoReplyEnabled ? 'ON' : 'OFF'}
              </div>
              {!Array.isArray(xDrafts?.items) || xDrafts.items.length === 0 ? (
                <p className="tiny">No draft replies queued yet.</p>
              ) : (
                <ul className="list">
                  {xDrafts.items.map((d: any) => (
                    <li className="item" key={d.tweet_id}>
                      <div><b>tweet</b> {d.tweet_id}</div>
                      <div className="meta" style={{ marginTop: 4 }}>{d.context || 'No context'}</div>
                      <div style={{ marginTop: 6 }}>{d.draft}</div>
                      <div className="row" style={{ marginTop: 8 }}>
                        <form action={approveXDraftAction}>
                          <input type="hidden" name="tweet_id" value={d.tweet_id} />
                          <button type="submit">Approve (no send)</button>
                        </form>
                        <form action={sendXDraftAction}>
                          <input type="hidden" name="tweet_id" value={d.tweet_id} />
                          <button className="btn-primary" type="submit">Send Reply</button>
                        </form>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card">
              <h2>Needs Attention</h2>
              <form action={retryFailedPublishAction}>
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <button className="btn-danger" type="submit">Retry All Failed</button>
              </form>
              {!Array.isArray(failedPublishes) || failedPublishes.length === 0 ? (
                <p className="tiny" style={{ marginTop: 8 }}>No failed publishes.</p>
              ) : (
                <ul className="list" style={{ marginTop: 10 }}>
                  {failedPublishes.map((f: any) => (
                    <li className="item" key={f.schedule.id}>
                      <div>{formatTs(f.schedule.publishAt)} · {f.content.channel} · <b>{f.content.title || f.content.id}</b></div>
                      <div className="meta">{f.content.lastError || 'Unknown error'}</div>
                      <form action={retryOneFailedPublishAction} style={{ marginTop: 8 }}>
                        <input type="hidden" name="schedule_id" value={f.schedule.id} />
                        <button type="submit">Retry This One</button>
                      </form>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card">
              <h2>Provider Audit Trail</h2>
              {!Array.isArray(publishJobs) || publishJobs.length === 0 ? (
                <p className="tiny">No publish jobs yet.</p>
              ) : (
                <ul className="list">
                  {publishJobs.slice(0, 12).map((p: any) => (
                    <li className="item" key={p.job.id}>
                      <div><b>{p.content.channel}</b> · {p.job.status} · attempt {p.job.attempt}</div>
                      <div className="meta">job {p.job.id} · {formatTs(p.job.createdAt)}</div>
                      <div className="meta" style={{ marginTop: 2 }}>
                        provider: {p.providerResponse?.provider || 'n/a'}
                        {p.providerResponse?.post_id ? ` · post_id: ${p.providerResponse.post_id}` : ''}
                        {p.providerResponse?.post_url ? ` · url: ${p.providerResponse.post_url}` : ''}
                        {p.job.error ? ` · error: ${p.job.error}` : ''}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}

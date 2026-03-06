import Link from 'next/link';
import { cookies } from 'next/headers';
import {
  approveContentAction,
  createIdeaSourceAction,
  generateContentAction,
  runPublishAction,
  scheduleContentAction,
  applyCadenceAction,
  updateContentAction,
  regenerateContentAction,
} from '../actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const FALLBACK_WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';

async function getJson(path: string, headers?: Record<string, string>) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store', headers });
  if (!res.ok) return null;
  return res.json();
}

function toLocalDatetimeInputValue(minutesFromNow = 5) {
  const d = new Date(Date.now() + minutesFromNow * 60_000);
  const pad = (n: number) => `${n}`.padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default async function StudioPage({ searchParams }: { searchParams?: { platform?: string; error?: string; notice?: string } }) {
  const c = cookies();
  const WORKSPACE_ID = c.get('do_workspace_id')?.value || FALLBACK_WORKSPACE_ID;
  const token = c.get('do_api_token')?.value || '';
  const actorHeaders = token ? { Authorization: `Bearer ${token}` } : {};
  const userEmail = (c.get('do_user_email')?.value || '').toLowerCase();
  const operatorAllowlist = new Set(
    String(process.env.AUTH_SUPERUSER_EMAILS || process.env.WEB_SUPERUSER_EMAILS || process.env.AUTH_OWNER_EMAILS || '')
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
  const isOperator = operatorAllowlist.has(userEmail);

  const [sources, content, accountsResp, meResp, trendSuggestions, heygenHealth] = await Promise.all([
    getJson(`/sources?workspaceId=${WORKSPACE_ID}`, actorHeaders),
    getJson(`/content?workspaceId=${WORKSPACE_ID}`, actorHeaders),
    getJson(`/integrations/accounts?workspaceId=${WORKSPACE_ID}`, actorHeaders),
    getJson(`/auth/me`, actorHeaders),
    getJson(`/intelligence/suggestions?workspaceId=${WORKSPACE_ID}&limit=6`, actorHeaders),
    getJson(`/integrations/heygen/health`, actorHeaders),
  ]);

  const latestSource = Array.isArray(sources) && sources.length > 0 ? sources[0] : null;
  const sourceItems = latestSource ? ((await getJson(`/sources/${latestSource.id}/items`)) as Array<any>) : [];
  const selectedPlatform = (searchParams?.platform || 'x').toLowerCase();
  const nextPlatformLink = (key: string) => `/studio?platform=${key}`;
  const channelMap: Record<string, string> = { x: 'x', linkedin: 'linkedin', instagram: 'instagram', tiktok: 'tiktok', youtube: 'youtube' };
  const selectedChannel = channelMap[selectedPlatform] || 'x';
  const latestSourceItemIds = new Set((sourceItems || []).map((s: any) => s.id));
  const drafts = (Array.isArray(content) ? content : [])
    .filter((c: any) => c.channel === selectedChannel && latestSourceItemIds.has(c.sourceItemId))
    .slice(0, 20);
  const approved = drafts.filter((c: any) => c.status === 'approved');
  const accountItems = (accountsResp?.items || []) as Array<any>;
  const defaultCountMap: Record<string, number> = { x: 8, linkedin: 6, instagram: 8, tiktok: 4, youtube: 4 };
  const selectedCount = defaultCountMap[selectedPlatform] || 8;
  const queueCap = 20;
  const accountType = String(meResp?.accountType || 'personal').toLowerCase();
  const isCorporate = accountType === 'corporate';
  const isTopTier = isCorporate;

  return (
    <main className="studio-root">
      <style suppressHydrationWarning>{`
        :root {
          --bg: #0b1220;
          --bg-soft: #111b31;
          --surface: #121c33;
          --surface-2: #16223d;
          --text: #e8eefc;
          --muted: #a5b4d4;
          --line: rgba(148, 163, 184, 0.28);
          --primary: #38bdf8;
          --primary-ink: #062437;
          --accent: #22c55e;
          --ok: #22c55e;
          --radius: 16px;
        }
        .studio-root {
          min-height: 100vh;
          background:
            radial-gradient(1100px 520px at -10% -25%, rgba(56,189,248,.22), transparent 62%),
            radial-gradient(1000px 500px at 120% -10%, rgba(34,197,94,.16), transparent 60%),
            radial-gradient(900px 420px at 50% 120%, rgba(99,102,241,.18), transparent 62%),
            linear-gradient(180deg, var(--bg-soft) 0%, var(--bg) 100%);
          color: var(--text);
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
          padding: 22px;
          position: relative;
          overflow-x: clip;
        }
        .studio-root::before {
          content: '';
          position: absolute;
          inset: 0;
          pointer-events: none;
          background-image: linear-gradient(rgba(148,163,184,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.06) 1px, transparent 1px);
          background-size: 30px 30px;
          mask-image: radial-gradient(circle at 50% 20%, black 35%, transparent 82%);
        }
        .wrap { max-width: 1080px; margin: 0 auto; position: relative; z-index: 2; }
        .top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; gap: 12px; }
        h1 { margin: 0; font-size: clamp(30px, 4vw, 42px); letter-spacing: -0.03em; line-height: 1.05; }
        .sub { margin: 8px 0 0; color: var(--muted); max-width: 620px; }
        .grid-two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .link { color: #c5d3f8; text-decoration: none; }
        .steps { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 10px; margin: 16px 0 22px; }
        .step {
          background: linear-gradient(180deg, rgba(22,34,61,.92), rgba(15,23,42,.7));
          border: 1px solid rgba(56,189,248,.25);
          border-radius: 999px;
          padding: 10px 12px;
          font-size: 12px;
          font-weight: 700;
          text-align: center;
          color: #e2ebff;
          box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 10px 24px rgba(2,6,23,.4);
        }
        .card {
          background: linear-gradient(180deg, rgba(18,28,51,.86), rgba(22,34,61,.72));
          border: 1px solid rgba(148,163,184,.24);
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          border-radius: var(--radius);
          padding: 18px;
          margin-bottom: 12px;
          box-shadow: 0 18px 42px rgba(2,6,23,.44);
          transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }
        .card:hover {
          transform: translateY(-1px);
          box-shadow: 0 20px 44px rgba(2,6,23,.45);
          border-color: rgba(56,189,248,.45);
        }
        .card h2 { margin: 0 0 10px; font-size: 20px; letter-spacing: -.01em; }
        .tiny { font-size: 12px; color: var(--muted); }
        .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        input, textarea, button, select {
          border: 1px solid rgba(148,163,184,.35);
          border-radius: 10px;
          padding: 10px 12px;
          font: inherit;
          background: rgba(15,23,42,.55);
          color: var(--text);
        }
        input, textarea, select { width: 100%; }
        textarea { min-height: 78px; resize: vertical; }
        button { width: auto; cursor: pointer; transition: transform .14s ease, box-shadow .16s ease, opacity .16s ease; }
        button:hover { transform: translateY(-1px); box-shadow: 0 10px 22px rgba(56,189,248,.25); }
        .primary {
          background: linear-gradient(180deg, #38bdf8, #0ea5e9);
          color: var(--primary-ink);
          border-color: #0284c7;
          font-weight: 800;
        }
        .ok { color: var(--ok); font-weight: 700; }
        .list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
        .item { border: 1px solid var(--line); border-radius: 12px; padding: 12px; background: rgba(15,23,42,.55); }
        .caption { color: #dbe7ff; margin-top: 8px; line-height: 1.5; }
        .empty { color: var(--muted); margin: 0; }
        @media (max-width: 980px) { .grid-two { grid-template-columns: 1fr; } }
        @media (max-width: 760px) {
          .steps { grid-template-columns: 1fr 1fr; }
          .top { flex-direction: column; }
        }
      `}</style>

      <div className="wrap">
        <div className="top">
          <div>
            <h1>Demand Orchestrator Studio</h1>
            <p className="sub">From idea to scheduled X post in under 3 minutes.</p>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Link className="link" href="/studio/queue">Unified Queue</Link>
            {isTopTier ? <Link className="link" href="/studio/models">Presenter Directory</Link> : <span className="tiny">Presenter Directory (Top Tier)</span>}
            {isOperator ? <>
              <Link className="link" href="/studio/faceless">Faceless Studio</Link>
              <Link className="link" href="/studio/avatar-video">Avatar Video</Link>
              <Link className="link" href="/studio/review">Review Theater</Link>
            </> : null}
            {isCorporate ? <>
              <Link className="link" href="/studio/corporate/team-avatars">Team Avatars</Link>
              <Link className="link" href="/studio/corporate/seats-roles">Seats & Roles</Link>
              <Link className="link" href="/studio/corporate/brand-kits">Brand Kits</Link>
            </> : <span className="tiny">Corporate Suite (Team Avatars · Roles · Brand Kits)</span>}
            {isOperator ? <Link className="link" href="/ops">Operator Console ↗</Link> : null}
            <form action="/auth/logout" method="post" style={{ margin: 0 }}>
              <button type="submit">Logout</button>
            </form>
          </div>
        </div>

        <section className="card" style={{ marginBottom: 10 }}>
          <h2 style={{ marginBottom: 8 }}>Publishing Platform</h2>
          <div className="row">
            {[
              ['x', 'X'],
              ['linkedin', 'LinkedIn'],
              ['instagram', 'Instagram'],
              ['tiktok', 'TikTok'],
              ['youtube', 'YouTube Shorts'],
            ].map(([key, label]) => (
              <Link
                key={key}
                href={nextPlatformLink(key)}
                className="link"
                style={{
                  border: key === selectedPlatform ? '1px solid #67e8f9' : '1px solid rgba(148,163,184,.35)',
                  borderRadius: 999,
                  padding: '7px 12px',
                  background: key === selectedPlatform ? 'rgba(103,232,249,.12)' : 'rgba(15,23,42,.45)',
                }}
              >
                {label}
              </Link>
            ))}
            <span className="tiny">Selected: <b>{selectedPlatform}</b> · rules auto-adjusted.</span>
          </div>
        </section>

        <section className="card" style={{ marginBottom: 10 }}>
          <h2 style={{ marginBottom: 8 }}>Connection Health</h2>
          <p className="tiny">Set once, then forget it. Reconnect only if a platform drops.</p>
          <div className="row">
            {['x', 'linkedin', 'instagram', 'youtube'].map((p) => {
              const row = accountItems.find((a: any) => a.platform === p) || { connected: false };
              return (
                <span
                  key={p}
                  style={{
                    border: '1px solid rgba(148,163,184,.35)',
                    borderRadius: 999,
                    padding: '7px 12px',
                    background: row.connected ? 'rgba(34,197,94,.14)' : 'rgba(251,113,133,.14)',
                    fontSize: 12,
                    fontWeight: 700,
                  }}
                >
                  {p.toUpperCase()} {row.connected ? '✅' : '⚠️'}
                </span>
              );
            })}
            {isOperator ? <Link className="link" href="/ops">Manage Connections</Link> : <span className="tiny">Connections managed by Ops</span>}
          </div>
        </section>

        {searchParams?.error ? (
          <section className="card" style={{ borderColor: 'rgba(251,113,133,.55)', background: 'linear-gradient(180deg, rgba(127,29,29,.30), rgba(22,34,61,.78))' }}>
            <h2 style={{ marginBottom: 6 }}>Action failed</h2>
            <p className="tiny">{searchParams.error}</p>
          </section>
        ) : null}

        {searchParams?.notice ? (
          <section className="card" style={{ borderColor: 'rgba(34,197,94,.55)', background: 'linear-gradient(180deg, rgba(20,83,45,.30), rgba(22,34,61,.78))' }}>
            <h2 style={{ marginBottom: 6 }}>Success</h2>
            <p className="tiny">{searchParams.notice}</p>
          </section>
        ) : null}

        <div className="steps">
          <div className="step">1. Add Idea</div>
          <div className="step">2. Generate Queue</div>
          <div className="step">3. Review & Approve</div>
          <div className="step">4. Schedule</div>
        </div>

        <section className="card" style={{ marginBottom: 10 }}>
          <h2>Trend → Brand Script Builder</h2>
          <p className="tiny">Pick one qualified signal and inject it into your current platform queue flow.</p>
          {!Array.isArray(trendSuggestions) || trendSuggestions.length === 0 ? (
            <p className="empty">No qualified suggestions yet. Import fresh signals from Operator Console.</p>
          ) : (
            <ul className="list">
              {trendSuggestions.slice(0, 4).map((s: any) => (
                <li className="item" key={s.id}>
                  <div><b>{s.topic}</b></div>
                  <div className="tiny" style={{ marginTop: 4 }}>final {Number(s.finalScore || 0).toFixed(3)} · risk {Number(s.policyRiskScore || 0).toFixed(2)}</div>
                  <div className="caption">{s.whyNow}</div>
                  <form action={createIdeaSourceAction} className="row" style={{ marginTop: 8 }}>
                    <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                    <input type="hidden" name="platform" value={selectedPlatform} />
                    <input type="hidden" name="video_mode" value="avatar" />
                    <input type="hidden" name="idea" value={`${s.topic}. ${s.whyNow}`} />
                    <button type="submit">Use for {selectedPlatform} queue</button>
                  </form>
                </li>
              ))}
            </ul>
          )}
        </section>

        {approved.length > 0 && (
          <section className="card" style={{ borderColor: 'rgba(34,197,94,.55)', background: 'linear-gradient(180deg, rgba(20,83,45,.35), rgba(22,34,61,.8))' }}>
            <h2 style={{ marginBottom: 6 }}>Nice — draft approved ✅</h2>
            <p className="tiny" style={{ marginBottom: 8 }}>Next step: schedule it now.</p>
            <a className="link" href="#step-4">Jump to Step 4 ↓</a>
          </section>
        )}

        <div className="grid-two">
          <section className="card">
            <h2>Step 1 · Add your idea</h2>
            <p className="tiny">Paste your idea and optionally attach docs/images for richer context.</p>
            <form action={createIdeaSourceAction}>
              <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
              <input type="hidden" name="platform" value={selectedPlatform} />
              {(selectedPlatform === 'tiktok' || selectedPlatform === 'youtube' || selectedPlatform === 'instagram') && (
                <div className="row" style={{ marginBottom: 8 }}>
                  <select name="video_mode" defaultValue="avatar" style={{ maxWidth: 280 }}>
                    <option value="avatar">Video Mode: Avatar Presenter</option>
                    <option value="cinematic">Video Mode: Cinematic</option>
                    <option value="faceless">Video Mode: Faceless Explainer</option>
                  </select>
                  <span className="tiny">Choose one modality per run for cleaner output contracts.</span>
                </div>
              )}
              <textarea
                name="idea"
                placeholder="Example: US Youth Soccer moved to school-year age groups. I need clear, parent-friendly posts about tryouts, roster impact, and development path."
                required
              />
              <input type="file" name="context_files" multiple accept=".txt,.md,.csv,.json,.pdf,.doc,.docx,image/*" />
              <div className="tiny">Upload docs, images, logo, or briefs. We’ll use them as context.</div>
              <div className="row" style={{ marginTop: 8 }}>
                <button className="primary" type="submit">Save Idea + Context</button>
              </div>
            </form>
          </section>

          <section className="card">
            <h2>Step 2 · Build queue for {selectedPlatform} (max {queueCap})</h2>
            {!latestSource ? (
              <p className="empty">No idea yet — complete Step 1 first.</p>
            ) : (
              <>
                <div className="tiny">Load one platform at a time, cap queue length, then do a final review pass.</div>
                {sourceItems?.length > 0 && (
                  <form action={generateContentAction} className="row" style={{ marginTop: 8 }}>
                    <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                    <input type="hidden" name="source_item_id" value={sourceItems[0].id} />
                    <input type="hidden" name="platform" value={selectedPlatform} />
                    <input type="hidden" name="channels" value={selectedChannel} />
                    <label className="tiny" style={{ display: 'grid', gap: 4 }}>
                      Queue size
                      <input name="variant_count" type="number" min={1} max={queueCap} defaultValue={selectedCount} style={{ maxWidth: 100 }} />
                    </label>
                    <button className="primary" type="submit">Generate Queue</button>
                    <a className="link" href="#step-3">Done → Final review</a>
                  </form>
                )}
              </>
            )}
          </section>
        </div>

        <section className="card" id="step-3">
          <h2>Step 3 · Final review, accept/edit/reject</h2>
          <p className="tiny">Showing drafts for your latest idea only.</p>
          {!drafts.length ? (
            <p className="empty">No {selectedPlatform} drafts yet — generate in Step 2.</p>
          ) : (
            <>
              <div className="item" style={{ marginBottom: 10 }}>
                <div><b>Live preview</b> · latest draft</div>
                <div className="caption">{drafts[0]?.caption}</div>
              </div>
              <details>
                <summary className="tiny" style={{ cursor: 'pointer', marginBottom: 8 }}>Review full queue ({drafts.length} posts)</summary>
                <ul className="list">
                  {drafts.map((c: any) => (
                    <li className="item" key={c.id}>
                      <div><b>{c.title || 'Draft'}</b> {c.status === 'approved' ? <span className="ok">· approved</span> : null}</div>
                      <div className="caption">{c.caption}</div>

                      <form action={updateContentAction} style={{ marginTop: 8 }}>
                        <input type="hidden" name="content_id" value={c.id} />
                        <textarea name="caption" defaultValue={c.caption || ''} rows={3} />
                        <div className="row" style={{ marginTop: 6 }}>
                          <button type="submit">Save</button>
                        </div>
                      </form>

                      <div className="row" style={{ marginTop: 8 }}>
                        {c.status === 'draft' && (
                          <form action={approveContentAction}>
                            <input type="hidden" name="content_id" value={c.id} />
                            <button className="primary" type="submit">Approve</button>
                          </form>
                        )}
                        <form action={regenerateContentAction}>
                          <input type="hidden" name="content_id" value={c.id} />
                          <button type="submit">Rewrite</button>
                        </form>
                      </div>
                    </li>
                  ))}
                </ul>
              </details>
            </>
          )}
        </section>

        {(selectedPlatform === 'tiktok' || selectedPlatform === 'youtube' || selectedPlatform === 'instagram') && (
          <section className="card">
            <h2>Video Avatar Setup (for video platforms)</h2>
            <p className="tiny">Before rendering, complete your avatar onboarding once, then reuse it in every video queue.</p>
            <ul className="tiny" style={{ lineHeight: 1.7 }}>
              <li>✅ Eye-level framing (head + upper torso)</li>
              <li>✅ Quiet room, low background noise</li>
              <li>✅ Soft front lighting, clean backdrop</li>
              <li>✅ Neutral attire, no busy patterns</li>
              <li>✅ 3–5 minute natural speaking clip</li>
            </ul>
            {!heygenHealth?.configured ? (
              <div className="item" style={{ marginTop: 8 }}>
                <div><b>Avatar service setup in progress.</b></div>
                <div className="tiny" style={{ marginTop: 4 }}>You can still complete onboarding now. Rendering unlocks automatically once setup is finalized.</div>
              </div>
            ) : null}
            <div className="row" style={{ marginTop: 8 }}>
              <Link
                href="/studio/model-signup"
                style={{
                  background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)',
                  color: '#062437',
                  border: '1px solid #0284c7',
                  borderRadius: 10,
                  padding: '10px 12px',
                  fontWeight: 800,
                  textDecoration: 'none',
                }}
              >
                🎥 Record My Avatar
              </Link>
              {isCorporate ? <Link className="link" href="/studio/corporate/team-avatars">Manage Team Avatars</Link> : null}
            </div>
          </section>
        )}

        <section className="card" id="step-4">
          <h2>Step 4 · Schedule and publish</h2>
          {!approved.length ? (
            <p className="empty">Approve at least one draft in Step 3.</p>
          ) : (
            <>
              <form action={applyCadenceAction} className="row" style={{ marginBottom: 10 }}>
                <input type="hidden" name="approved_ids" value={approved.map((c: any) => c.id).join(',')} />
                <select name="cadence" defaultValue="weekdays" style={{ maxWidth: 220 }}>
                  <option value="weekdays">Weekdays (Mon–Fri, 9:15 AM)</option>
                  <option value="daily">Daily (9:15 AM)</option>
                  <option value="three_weekly">3x Weekly</option>
                </select>
                <input name="timezone" defaultValue="America/New_York" style={{ maxWidth: 180 }} />
                <button className="primary" type="submit">Apply Cadence to Approved</button>
              </form>

              <form action={scheduleContentAction} className="row">
                <select name="content_id" defaultValue={approved[0].id} style={{ minWidth: 220, flex: 2 }}>
                  {approved.map((c: any) => (
                    <option key={c.id} value={c.id}>{c.title || c.id}</option>
                  ))}
                </select>
                <input name="publish_at" type="datetime-local" defaultValue={toLocalDatetimeInputValue(5)} required autoFocus style={{ maxWidth: 210 }} />
                <input name="timezone" defaultValue="America/New_York" style={{ maxWidth: 180 }} />
                <button type="submit">Schedule One</button>
              </form>
              <form action={runPublishAction} style={{ marginTop: 10 }}>
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <button className="primary" type="submit">Publish now</button>
              </form>
            </>
          )}
        </section>
      </div>
    </main>
  );
}

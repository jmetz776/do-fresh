import Link from 'next/link';
import { cookies } from 'next/headers';
import { approveVideoRenderAction, refreshVideoRenderAction, refreshQueuedVideoRendersAction, retryVideoRenderAction } from '../../actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const FALLBACK_WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';

async function getJson(path: string, headers?: Record<string, string>) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store', headers });
  if (!res.ok) return null;
  return res.json();
}

export default async function ReviewPage() {
  const c = cookies();
  const workspaceId = c.get('do_workspace_id')?.value || FALLBACK_WORKSPACE_ID;
  const token = c.get('do_api_token')?.value || '';
  const actorHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const renders = (await getJson(`/v1/consent/video/renders?workspaceId=${encodeURIComponent(workspaceId)}&limit=50`, actorHeaders))?.items || [];
  const bgAnalytics = (await getJson(`/v1/consent/video/background-analytics?workspaceId=${encodeURIComponent(workspaceId)}&limit=200`, actorHeaders))?.items || [];

  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 22, fontFamily: 'Inter, system-ui' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 32 }}>Review Theater</h1>
            <p style={{ margin: '6px 0 0', color: '#9fb2d6' }}>Preview rendered videos before publish. Approve only what meets the bar.</p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Link href="/studio/faceless" style={linkBtn}>Faceless Studio</Link>
            <form action={refreshQueuedVideoRendersAction}>
              <input type="hidden" name="workspace_id" value={workspaceId} />
              <button type="submit" style={primaryBtn}>Refresh Queue</button>
            </form>
          </div>
        </div>

        <section style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <h2 style={{ margin: 0, fontSize: 18 }}>Background Performance</h2>
            <span style={{ fontSize: 12, color: '#9fb2d6' }}>Top templates by approval rate</span>
          </div>
          {bgAnalytics.length === 0 ? (
            <div style={{ color: '#9fb2d6', fontSize: 13 }}>No background analytics yet.</div>
          ) : (
            <div style={{ display: 'grid', gap: 8 }}>
              {bgAnalytics.slice(0, 6).map((row: any) => (
                <div key={row.backgroundTemplateId} style={{ border: '1px solid rgba(148,163,184,.24)', borderRadius: 10, padding: 10, background: 'rgba(2,6,23,.35)', display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                  <div style={{ fontSize: 13, fontWeight: 700 }}>{row.backgroundTemplateId}</div>
                  <div style={{ fontSize: 12, color: '#c7d2ee' }}>approved {Math.round(Number(row.approvalRate || 0) * 100)}% · pass {Math.round(Number(row.passRate || 0) * 100)}% · n={row.total}</div>
                </div>
              ))}
            </div>
          )}
        </section>

        {renders.length === 0 ? (
          <section style={card}><div style={{ color: '#9fb2d6' }}>No renders yet. Run Faceless batch and enqueue renders first.</div></section>
        ) : (
          <section style={{ display: 'grid', gap: 10 }}>
            {renders.map((r: any) => {
              const canPlay = typeof r.videoUri === 'string' && r.videoUri.startsWith('http');
              return (
                <article key={r.id} style={card}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700 }}>{r.provider || 'video'} · {r.status}</div>
                      <div style={{ fontSize: 12, color: '#9fb2d6' }}>id: {r.id}</div>
                      {r.backgroundTemplateId ? <div style={{ fontSize: 12, color: '#9fb2d6' }}>background: {r.backgroundTemplateId}</div> : null}
                    </div>
                    <div style={{ fontSize: 12, color: '#9fb2d6' }}>created: {r.createdAt || '—'}</div>
                  </div>

                  {canPlay ? (
                    <video controls preload="metadata" style={{ width: '100%', borderRadius: 10, marginBottom: 8 }} src={r.videoUri} />
                  ) : (
                    <div style={{ border: '1px dashed rgba(148,163,184,.4)', borderRadius: 10, padding: 12, color: '#9fb2d6', marginBottom: 8 }}>
                      Preview not ready yet. Status: {r.status}. URI: {r.videoUri || 'pending'}
                      {r.error ? <div style={{ marginTop: 6, color: '#fca5a5' }}>Error: {r.error}</div> : null}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <form action={refreshVideoRenderAction}>
                      <input type="hidden" name="render_id" value={r.id} />
                      <button type="submit" style={btn}>Refresh</button>
                    </form>
                    <form action={retryVideoRenderAction}>
                      <input type="hidden" name="render_id" value={r.id} />
                      <button type="submit" style={btn}>Retry</button>
                    </form>
                    <form action={approveVideoRenderAction}>
                      <input type="hidden" name="render_id" value={r.id} />
                      <button type="submit" style={{ ...primaryBtn, opacity: (r.status === 'succeeded' && canPlay) ? 1 : 0.5 }} disabled={!(r.status === 'succeeded' && canPlay)}>Approve</button>
                    </form>
                  </div>
                </article>
              );
            })}
          </section>
        )}
      </div>
    </main>
  );
}

const card: React.CSSProperties = {
  border: '1px solid rgba(148,163,184,.28)',
  borderRadius: 14,
  background: 'linear-gradient(180deg, rgba(18,28,51,.86), rgba(15,23,42,.68))',
  padding: 14,
};
const btn: React.CSSProperties = { border: '1px solid rgba(148,163,184,.35)', background: 'rgba(15,23,42,.55)', color: '#e8eefc', borderRadius: 10, padding: '8px 12px', cursor: 'pointer' };
const primaryBtn: React.CSSProperties = { border: '1px solid #0284c7', background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', color: '#062437', borderRadius: 10, padding: '8px 12px', fontWeight: 800, cursor: 'pointer' };
const linkBtn: React.CSSProperties = { border: '1px solid rgba(148,163,184,.35)', background: 'rgba(15,23,42,.55)', color: '#e8eefc', borderRadius: 10, padding: '8px 12px', textDecoration: 'none' };

import Link from 'next/link';
import { cookies } from 'next/headers';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const FALLBACK_WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';

async function getJson(path: string, headers?: Record<string, string>) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store', headers });
  if (!res.ok) return null;
  return res.json();
}

export default async function StudioAnalyticsPage() {
  const c = cookies();
  const workspaceId = c.get('do_workspace_id')?.value || FALLBACK_WORKSPACE_ID;
  const token = c.get('do_api_token')?.value || '';
  const actorHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const [dashboard, content, schedules, publishJobs, analyticsSummary] = await Promise.all([
    getJson(`/dashboard?workspaceId=${encodeURIComponent(workspaceId)}`, actorHeaders),
    getJson(`/content?workspaceId=${encodeURIComponent(workspaceId)}`, actorHeaders),
    getJson(`/schedules?workspaceId=${encodeURIComponent(workspaceId)}`, actorHeaders),
    getJson(`/publish/jobs?workspaceId=${encodeURIComponent(workspaceId)}`, actorHeaders),
    getJson(`/analytics/summary?workspaceId=${encodeURIComponent(workspaceId)}&days=30`, actorHeaders),
  ]);

  const items = Array.isArray(content) ? content : [];
  const approved = items.filter((x: any) => x.status === 'approved').length;
  const drafts = items.filter((x: any) => x.status === 'draft').length;
  const scheduled = Array.isArray(schedules) ? schedules.filter((x: any) => x.status === 'scheduled').length : 0;
  const jobs = Array.isArray(publishJobs) ? publishJobs : [];
  const successJobs = jobs.filter((j: any) => String(j.status || '').toLowerCase() === 'succeeded').length;

  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 22, fontFamily: 'Inter, system-ui' }}>
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <h1 style={{ margin: 0 }}>Analytics</h1>
            <p style={{ margin: '6px 0 0', color: '#9fb2d6' }}>Simple performance pulse for your workspace.</p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Link href="/studio" style={{ color: '#cce5ff' }}>Back to Studio</Link>
            <Link href="/help" style={{ color: '#cce5ff' }}>FAQ / Help</Link>
          </div>
        </div>

        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 10, marginBottom: 10 }}>
          <Metric title="Impressions (30d)" value={Number(analyticsSummary?.totals?.impressions || 0)} />
          <Metric title="Engagement Rate %" value={Number(analyticsSummary?.engagementRatePct || 0)} />
          <Metric title="Clicks (30d)" value={Number(analyticsSummary?.totals?.clicks || 0)} />
          <Metric title="Leads (30d)" value={Number(analyticsSummary?.totals?.leads || 0)} />
        </section>

        <section style={card}>
          <h2 style={{ marginTop: 0 }}>What’s working</h2>
          <div style={{ color: '#9fb2d6', fontSize: 12, marginBottom: 8 }}>Top approved items (latest first)</div>
          {(analyticsSummary?.topContent || []).length === 0 ? (
            <div style={{ color: '#9fb2d6' }}>No ranked content yet. Analytics will populate as events are ingested.</div>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 8 }}>
              {(analyticsSummary?.topContent || []).map((x: any) => {
                const match = items.find((c: any) => c.id === x.contentItemId);
                return (
                  <li key={x.contentItemId} style={{ border: '1px solid rgba(148,163,184,.24)', borderRadius: 10, padding: 10, background: 'rgba(2,6,23,.35)' }}>
                    <div style={{ fontWeight: 700 }}>{match?.title || match?.hook || x.contentItemId}</div>
                    <div style={{ fontSize: 12, color: '#9fb2d6', marginTop: 4 }}>
                      {(match?.channel || 'channel')} · impressions {x.impressions || 0} · engagements {x.engagements || 0} · clicks {x.clicks || 0} · leads {x.leads || 0}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section style={card}>
          <h2 style={{ marginTop: 0 }}>Engine recommendations</h2>
          <ul style={{ margin: 0, paddingLeft: 18, color: '#dbe7ff' }}>
            <li>Keep queue full with at least 7 approved posts ahead.</li>
            <li>Increase publishing cadence when success rate stays high for 7 days.</li>
            <li>Use premium video/background slots on highest-confidence campaigns.</li>
          </ul>
          <div style={{ color: '#9fb2d6', fontSize: 12, marginTop: 8 }}>Workspace: {workspaceId} · Dashboard snapshots available: {dashboard ? 'yes' : 'no'}</div>
        </section>
      </div>
    </main>
  );
}

function Metric({ title, value }: { title: string; value: number }) {
  return (
    <div style={{ border: '1px solid rgba(148,163,184,.24)', borderRadius: 12, padding: 12, background: 'rgba(15,23,42,.7)' }}>
      <div style={{ color: '#9fb2d6', fontSize: 12 }}>{title}</div>
      <div style={{ fontSize: 24, fontWeight: 800, marginTop: 4 }}>{Number(value || 0)}</div>
    </div>
  );
}

const card = { border: '1px solid rgba(148,163,184,.24)', borderRadius: 12, padding: 14, background: 'rgba(15,23,42,.7)', marginBottom: 10 } as const;

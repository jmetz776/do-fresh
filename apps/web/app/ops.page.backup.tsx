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
} from './actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'ws-main';

async function getJson(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

export default async function Home() {
  const [dashboard, sources, content, schedules, failedPublishes, publishJobs] = await Promise.all([
    getJson(`/dashboard?workspaceId=${WORKSPACE_ID}`),
    getJson(`/sources?workspaceId=${WORKSPACE_ID}`),
    getJson(`/content?workspaceId=${WORKSPACE_ID}`),
    getJson(`/schedules?workspaceId=${WORKSPACE_ID}`),
    getJson(`/publish/failed?workspaceId=${WORKSPACE_ID}`),
    getJson(`/publish/jobs?workspaceId=${WORKSPACE_ID}`),
  ]);

  const latestSource = Array.isArray(sources) && sources.length > 0 ? sources[0] : null;
  const sourceItems = latestSource
    ? ((await getJson(`/sources/${latestSource.id}/items`)) as Array<any>)
    : [];

  return (
    <main style={{ padding: 24, fontFamily: 'sans-serif', maxWidth: 1100, margin: '0 auto' }}>
      <h1>DemandOrchestrator Queue</h1>
      <p>Source → Normalize → Generate → Approve → Schedule → Publish</p>
      <p style={{ marginTop: 6 }}>
        <Link href="/waitlist">Open waitlist landing page ↗</Link>
      </p>

      <section style={{ margin: '16px 0', padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
        <h2>1) Create Source</h2>
        <form action={createSourceAction}>
          <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <select name="type" defaultValue="csv">
              <option value="csv">CSV</option>
              <option value="url">URL</option>
            </select>
            <button type="submit">Create Source</button>
          </div>
          <textarea
            name="raw_payload"
            rows={4}
            style={{ width: '100%' }}
            placeholder={'CSV: title,body\nMy title,My body\n\nor paste URL when type=url'}
            required
          />
        </form>
      </section>

      <section style={{ margin: '16px 0', padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
        <h2>2) Latest Source</h2>
        {!latestSource ? (
          <p>No source yet.</p>
        ) : (
          <>
            <div>
              <b>ID:</b> {latestSource.id} | <b>Status:</b> {latestSource.status}
            </div>
            <form action={normalizeSourceAction} style={{ marginTop: 8 }}>
              <input type="hidden" name="source_id" value={latestSource.id} />
              <button type="submit">Normalize Source</button>
            </form>
            <div style={{ marginTop: 8 }}>
              <b>Source Items:</b> {sourceItems?.length || 0}
            </div>
            {sourceItems?.length > 0 && (
              <form action={generateContentAction} style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
                <select name="source_item_id" defaultValue={sourceItems[0].id}>
                  {sourceItems.map((s: any) => (
                    <option key={s.id} value={s.id}>
                      {s.title || s.id}
                    </option>
                  ))}
                </select>
                <input name="channels" defaultValue="x" placeholder="x,linkedin" />
                <input name="variant_count" defaultValue="1" type="number" min={1} max={10} />
                <button type="submit">Generate Content</button>
              </form>
            )}
          </>
        )}
      </section>

      <section style={{ margin: '16px 0', padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
        <h2>3) Content Queue</h2>
        {!Array.isArray(content) || content.length === 0 ? (
          <p>No content items yet.</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {content.map((c: any) => (
              <li key={c.id} style={{ marginBottom: 10, padding: 10, border: '1px solid #eee', borderRadius: 8 }}>
                <div>
                  <b>{c.channel}</b> — <i>{c.status}</i> — {c.title}
                </div>
                <div style={{ margin: '6px 0' }}>{c.caption}</div>
                <form action={updateContentAction} style={{ display: 'grid', gap: 6, marginBottom: 8 }}>
                  <input type="hidden" name="content_id" value={c.id} />
                  <input name="title" defaultValue={c.title || ''} placeholder="Title" />
                  <input name="hook" defaultValue={c.hook || ''} placeholder="Hook" />
                  <textarea name="caption" defaultValue={c.caption || ''} rows={3} />
                  <button type="submit">Save Edit</button>
                </form>
                <form action={regenerateContentAction} style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
                  <input type="hidden" name="content_id" value={c.id} />
                  <input name="guidance" placeholder="Regenerate guidance (optional)" />
                  <button type="submit">Regenerate</button>
                </form>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {c.status === 'draft' && (
                    <form action={approveContentAction}>
                      <input type="hidden" name="content_id" value={c.id} />
                      <button type="submit">Approve</button>
                    </form>
                  )}
                  {(c.status === 'approved' || c.status === 'draft') && (
                    <form action={scheduleContentAction} style={{ display: 'flex', gap: 6 }}>
                      <input type="hidden" name="content_id" value={c.id} />
                      <input name="publish_at" type="datetime-local" required />
                      <input name="timezone" defaultValue="America/New_York" />
                      <button type="submit">Schedule</button>
                    </form>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ margin: '16px 0', padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
        <h2>4) Schedules + Publish</h2>
        <form action={runPublishAction} style={{ marginBottom: 8 }}>
          <button type="submit">Run Publisher Now</button>
        </form>
        {!Array.isArray(schedules) || schedules.length === 0 ? (
          <p>No schedules yet.</p>
        ) : (
          <ul>
            {schedules.map((s: any) => (
              <li key={s.id}>
                {s.publishAt} — {s.channel} — <i>{s.status}</i>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ margin: '16px 0', padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
        <h2>Needs Attention (Failed Publishes)</h2>
        <form action={retryFailedPublishAction} style={{ marginBottom: 8 }}>
          <input type="hidden" name="workspace_id" value={WORKSPACE_ID} />
          <button type="submit">Retry All Failed</button>
        </form>
        {!Array.isArray(failedPublishes) || failedPublishes.length === 0 ? (
          <p>No failed publishes right now.</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {failedPublishes.map((f: any) => (
              <li key={f.schedule.id} style={{ marginBottom: 8, border: '1px solid #eee', borderRadius: 8, padding: 8 }}>
                <div>
                  {f.schedule.publishAt} — {f.content.channel} — <b>{f.content.title || f.content.id}</b>
                  {f.content.lastError ? ` — ${f.content.lastError}` : ''}
                </div>
                <form action={retryOneFailedPublishAction} style={{ marginTop: 6 }}>
                  <input type="hidden" name="schedule_id" value={f.schedule.id} />
                  <button type="submit">Retry This One</button>
                </form>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ margin: '16px 0', padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
        <h2>Provider Audit Trail</h2>
        {!Array.isArray(publishJobs) || publishJobs.length === 0 ? (
          <p>No publish jobs yet.</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {publishJobs.slice(0, 20).map((p: any) => (
              <li key={p.job.id} style={{ marginBottom: 8, border: '1px solid #eee', borderRadius: 8, padding: 8 }}>
                <div>
                  <b>{p.content.channel}</b> — {p.job.status} — attempt {p.job.attempt}
                </div>
                <div style={{ fontSize: 12, opacity: 0.8 }}>
                  job {p.job.id} | {p.job.createdAt}
                </div>
                <div style={{ fontSize: 12, marginTop: 4 }}>
                  provider: {p.providerResponse?.provider || 'n/a'}
                  {p.providerResponse?.post_id ? ` | post_id: ${p.providerResponse.post_id}` : ''}
                  {p.providerResponse?.post_url ? ` | url: ${p.providerResponse.post_url}` : ''}
                  {p.job.error ? ` | error: ${p.job.error}` : ''}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ margin: '16px 0', padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
        <h2>Dashboard</h2>
        {!dashboard ? (
          <p>No dashboard yet.</p>
        ) : (
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {['draft', 'approved', 'scheduled', 'published', 'failed'].map((k) => (
              <div key={k} style={{ border: '1px solid #eee', borderRadius: 6, padding: 8, minWidth: 110 }}>
                <div style={{ fontSize: 12, textTransform: 'uppercase' }}>{k}</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>{dashboard[k] || 0}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

import Link from 'next/link';
import CopyEmailsButton from './CopyEmailsButton';
import { updateLeadStatusAction } from './actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

async function getLeads(searchParams: any) {
  const source = searchParams?.source ? `&source=${encodeURIComponent(searchParams.source)}` : '';
  const campaign = searchParams?.campaign ? `&campaign=${encodeURIComponent(searchParams.campaign)}` : '';
  const status = searchParams?.status ? `&status=${encodeURIComponent(searchParams.status)}` : '';
  const q = searchParams?.q ? `&q=${encodeURIComponent(searchParams.q)}` : '';
  const dedupe = searchParams?.dedupe === '1' ? '&dedupe=1' : '';
  const includeTests = searchParams?.include_tests === '1' ? '&include_tests=1' : '';
  const res = await fetch(`${API_BASE}/v1/leads?limit=200${source}${campaign}${status}${q}${dedupe}${includeTests}`, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

async function getLeadStats() {
  const res = await fetch(`${API_BASE}/v1/leads/stats`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

function formatTs(ts?: string) {
  if (!ts) return '—';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

export default async function WaitlistAdminPage({ searchParams }: { searchParams?: any }) {
  const qp = searchParams || {};
  const [leads, stats] = await Promise.all([getLeads(qp), getLeadStats()]);
  const emails = leads.map((l: any) => l.email).filter(Boolean);
  const statusCounts = leads.reduce((acc: Record<string, number>, l: any) => {
    const key = l.status || 'unknown';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  const p = new URLSearchParams();
  if (qp.q) p.set('q', qp.q);
  if (qp.source) p.set('source', qp.source);
  if (qp.campaign) p.set('campaign', qp.campaign);
  if (qp.status) p.set('status', qp.status);
  if (qp.dedupe === '1') p.set('dedupe', '1');
  if (qp.include_tests === '1') p.set('include_tests', '1');
  p.set('limit', '2000');
  const csvHref = `${API_BASE}/v1/leads/export.csv?${p.toString()}`;

  return (
    <main className="admin-root">
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
          --radius: 14px;
        }
        .admin-root {
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
        .top {
          display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom: 14px;
        }
        .top h1 { margin: 0; font-size: 30px; letter-spacing: -.01em; }
        .sub { margin-top: 4px; color: var(--muted); }
        .link { color: #cce5ff; text-decoration: none; }

        .card {
          border:1px solid var(--border);
          border-radius: var(--radius);
          background: linear-gradient(180deg, rgba(15,23,42,.78), rgba(15,23,42,.48));
          padding: 14px;
        }
        .card + .card { margin-top: 12px; }

        .row { display:flex; gap: 8px; flex-wrap: wrap; align-items:center; }
        input, select, button, a.btn {
          border-radius: 10px;
          border: 1px solid rgba(148,163,184,.35);
          background: rgba(2,6,23,.5);
          color: #eaf0ff;
          padding: 9px 10px;
          font: inherit;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }
        input { min-width: 180px; }
        button, a.btn { cursor: pointer; transition: transform .12s ease, box-shadow .18s ease; }
        button:hover, a.btn:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(125,211,252,.18); }
        .btn-primary {
          background: var(--primary);
          color: var(--primary-ink);
          border-color: rgba(134,239,172,.7);
          font-weight: 800;
        }

        .chips { display:flex; gap:8px; flex-wrap: wrap; }
        .chip {
          border:1px solid var(--border); border-radius:999px; padding: 6px 10px;
          font-size: 12px; background: rgba(15,23,42,.56); color: #c8d4f0;
        }

        .table-wrap {
          border:1px solid var(--border);
          border-radius: 12px;
          overflow: auto;
          background: rgba(2,6,23,.35);
        }
        table { width: 100%; border-collapse: collapse; min-width: 980px; }
        thead th {
          text-align: left;
          padding: 10px;
          font-size: 12px;
          letter-spacing: .06em;
          text-transform: uppercase;
          color: #bdd0f3;
          background: rgba(15,23,42,.82);
          border-bottom: 1px solid rgba(148,163,184,.2);
          position: sticky;
          top: 0;
          z-index: 1;
        }
        tbody td { padding: 10px; border-top: 1px solid rgba(148,163,184,.14); font-size: 14px; }
        tbody tr:hover { background: rgba(15,23,42,.35); }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; color: #b7c8ea; }
        .muted { color: var(--muted); }

        @media (prefers-reduced-motion: reduce) { * { animation:none !important; transition:none !important; } }
      `}</style>

      <div className="wrap">
        <div className="top">
          <div>
            <h1>Waitlist Admin</h1>
            <div className="sub">Lead operations with export, status workflow, and clean filtering.</div>
          </div>
          <div className="row">
            <Link className="link" href="/waitlist">← Waitlist</Link>
            <Link className="link" href="/ops">Operator Console ↗</Link>
          </div>
        </div>

        <section className="card">
          <div className="row" style={{ marginBottom: 10 }}>
            <Link href="/waitlist/admin" className="btn">All leads</Link>
            <Link href="/waitlist/admin?status=new" className="btn">New only</Link>
            <Link href="/waitlist/admin?status=qualified" className="btn">Qualified</Link>
            <Link href="/waitlist/admin?status=contacted" className="btn">Contacted</Link>
          </div>

          <form method="GET" className="row">
            <input name="q" placeholder="Search email/source/campaign" defaultValue={searchParams?.q || ''} />
            <input name="source" placeholder="Source filter" defaultValue={searchParams?.source || ''} />
            <input name="campaign" placeholder="Campaign filter" defaultValue={searchParams?.campaign || ''} />
            <select name="status" defaultValue={searchParams?.status || ''}>
              <option value="">all statuses</option>
              {['new', 'not_contacted', 'contacted', 'replied', 'qualified', 'closed'].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <label className="row" style={{ gap: 6 }}>
              <input type="checkbox" name="dedupe" value="1" defaultChecked={searchParams?.dedupe === '1'} style={{ minWidth: 0 }} />
              dedupe
            </label>
            <label className="row" style={{ gap: 6 }}>
              <input type="checkbox" name="include_tests" value="1" defaultChecked={searchParams?.include_tests === '1'} style={{ minWidth: 0 }} />
              include test leads
            </label>
            <button type="submit" className="btn-primary">Apply Filters</button>
          </form>

          <div className="row" style={{ marginTop: 10 }}>
            <a href={csvHref} className="btn">Export CSV</a>
            <CopyEmailsButton emails={emails} />
            <span className="muted">{leads.length} leads loaded</span>
          </div>
        </section>

        <section className="card">
          <div className="chips" style={{ marginBottom: 8 }}>
            <span className="chip">total: <b>{stats?.total ?? '—'}</b></span>
            <span className="chip">today: <b>{stats?.today ?? '—'}</b></span>
            <span className="chip">loaded: <b>{leads.length}</b></span>
            <span className="chip">new (loaded): <b>{statusCounts['new'] || 0}</b></span>
            <span className="chip">qualified (loaded): <b>{statusCounts['qualified'] || 0}</b></span>
          </div>
          <div className="chips">
            {['new', 'not_contacted', 'contacted', 'replied', 'qualified', 'closed'].map((s) => (
              <span key={s} className="chip">{s}: <b>{statusCounts[s] || 0}</b></span>
            ))}
          </div>
        </section>

        <section className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Email</th>
                  <th>Source</th>
                  <th>Campaign</th>
                  <th>Medium</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {leads.length === 0 ? (
                  <tr><td colSpan={7} style={{ padding: 12 }}>No leads found.</td></tr>
                ) : (
                  leads.map((l: any) => (
                    <tr key={l.id}>
                      <td className="mono">{l.id}</td>
                      <td>{l.email}</td>
                      <td>{l.source || '—'}</td>
                      <td>{l.utm_campaign || '—'}</td>
                      <td>{l.utm_medium || '—'}</td>
                      <td>
                        <form action={updateLeadStatusAction} className="row" style={{ flexWrap: 'nowrap' }}>
                          <input type="hidden" name="lead_id" value={l.id} />
                          <select name="status" defaultValue={l.status || 'new'} style={{ minWidth: 150 }}>
                            {['new', 'not_contacted', 'contacted', 'replied', 'qualified', 'closed'].map((s) => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                          <button type="submit">Save</button>
                        </form>
                      </td>
                      <td>{formatTs(l.created_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}

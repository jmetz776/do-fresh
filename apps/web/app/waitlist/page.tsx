import Link from 'next/link';
import { joinWaitlistAction } from './actions';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

async function getLeadStats() {
  const res = await fetch(`${API_BASE}/v1/leads/stats`, { cache: 'no-store' });
  if (!res.ok) return { total: 0, today: 0 };
  return res.json();
}

export default async function WaitlistPage({ searchParams }: { searchParams?: { submitted?: string; error?: string } }) {
  const submitted = searchParams?.submitted === '1';
  const hasError = searchParams?.error === '1';
  const stats = await getLeadStats();
  const showSignupCount = (stats.total || 0) >= 25;

  return (
    <main className="wl-root">
      <style>{`
        :root {
          --bg: #05070f;
          --surface: #0b1120;
          --border: rgba(148,163,184,.24);
          --text: #eaf0ff;
          --muted: #9aa7c7;
          --primary: #86efac;
          --primary-ink: #052e16;
        }
        .wl-root {
          min-height: 100vh;
          color: var(--text);
          background:
            radial-gradient(900px 420px at -10% -20%, rgba(56,189,248,.2), transparent 65%),
            radial-gradient(900px 450px at 110% -10%, rgba(34,197,94,.14), transparent 60%),
            var(--bg);
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
          position: relative;
          overflow: hidden;
        }
        .ambient {
          position: absolute;
          width: 520px;
          height: 520px;
          border-radius: 999px;
          filter: blur(60px);
          opacity: .22;
          pointer-events: none;
        }
        .ambient.one { background: #22d3ee; left: -160px; top: -120px; animation: drift 12s ease-in-out infinite; }
        .ambient.two { background: #86efac; right: -180px; top: 120px; animation: drift 14s ease-in-out infinite; }
        @keyframes drift { 0%,100% { transform: translateY(0px);} 50% { transform: translateY(-18px);} }
        .wrap { max-width: 860px; margin: 0 auto; padding: 38px 22px 72px; }
        .top a { color: #b8c6ea; text-decoration: none; font-size: 14px; }
        .top a:hover { color: #d8e4ff; }
        .hero h1 { margin: 14px 0 8px; font-size: clamp(2rem, 5vw, 3rem); line-height: 1.08; }
        .hero p { margin: 0; color: var(--muted); line-height: 1.6; font-size: 1.02rem; max-width: 760px; }
        .card {
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 18px;
          margin-top: 18px;
          background: linear-gradient(180deg, rgba(15,23,42,.82), rgba(15,23,42,.48));
        }
        .card h2 { margin: 0 0 10px; font-size: 24px; }
        .card ul { margin: 0 0 14px 18px; color: #c2cdec; line-height: 1.5; }
        .stats { display:flex; gap:10px; flex-wrap: wrap; margin: 10px 0 14px; }
        .stat {
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 10px;
          min-width: 140px;
          background: rgba(2,6,23,.45);
        }
        .stat .k { font-size: 12px; text-transform: uppercase; opacity: .75; letter-spacing: .05em; }
        .stat .v { font-size: 22px; font-weight: 800; margin-top: 2px; }
        .banner-ok { background: rgba(34,197,94,.14); border: 1px solid rgba(34,197,94,.45); color: #d7ffe5; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
        .banner-err { background: rgba(239,68,68,.14); border: 1px solid rgba(239,68,68,.45); color: #ffd9d9; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
        .form { display:grid; gap: 9px; }
        .form-label {
          font-size: 12px;
          letter-spacing: .08em;
          text-transform: uppercase;
          color: #b8c6ea;
          margin-bottom: 2px;
        }
        .input {
          padding: 12px;
          border-radius: 10px;
          border: 1px solid rgba(148,163,184,.35);
          background: rgba(2,6,23,.5);
          color: #e6ecff;
          outline: none;
        }
        .input:focus { border-color: rgba(134,239,172,.8); box-shadow: 0 0 0 3px rgba(134,239,172,.15); }
        .btn {
          padding: 12px;
          border-radius: 10px;
          border: none;
          background: var(--primary);
          color: var(--primary-ink);
          font-weight: 800;
          cursor: pointer;
          box-shadow: 0 8px 26px rgba(134,239,172,.28);
        }
      `}</style>

      <div className="ambient one" />
      <div className="ambient two" />
      <div className="wrap" style={{ position: 'relative', zIndex: 2 }}>
        <div className="top" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <Link href="/">← Back to Home</Link>
          <span style={{ opacity: 0.35 }}>|</span>
          <Link href="/waitlist/admin">Open Waitlist Admin</Link>
        </div>

        <section className="hero">
          <h1>DemandOrchestrator Waitlist</h1>
          <p>
            Advanced content operations infrastructure: source ingest → generation → approval → scheduling → publish,
            with retry-safe execution, provider audit trails, and lead pipeline attribution.
          </p>
        </section>

        <section className="card">
          <h2>Get Early Access</h2>
          <ul>
            <li>Ship 3–5x faster with a single content queue</li>
            <li>Retry-safe publisher with provider audit trail and recovery controls</li>
            <li>Lead intelligence layer: source/campaign attribution + outreach statuses</li>
            <li>Built for operators, not dashboard tourists</li>
          </ul>

          <div className="stats">
            <div className="stat">
              <div className="k">{showSignupCount ? 'Total Waitlist' : 'Early Cohort'}</div>
              <div className="v">{showSignupCount ? (stats.total || 0) : 'Private'}</div>
            </div>
            <div className="stat">
              <div className="k">Access Window</div>
              <div className="v">Limited</div>
            </div>
          </div>

          {submitted && <div className="banner-ok">You’re in. We’ll reach out with access steps. Approved beta users will receive a guided onboarding link (including Trend-to-Brand profile setup + optional voice/video setup).</div>}
          {hasError && <div className="banner-err">Couldn’t submit right now. Try again in a minute.</div>}

          <div style={{ border: '1px solid rgba(148,163,184,.25)', background: 'rgba(2,6,23,.35)', borderRadius: 10, padding: 12, marginBottom: 12 }}>
            <div style={{ fontSize: 12, letterSpacing: '.06em', textTransform: 'uppercase', opacity: .75 }}>Operator note</div>
            <div style={{ marginTop: 6, color: '#c9d4ef', lineHeight: 1.55 }}>
              “We built this because posting tools weren’t solving execution. We needed one system from content to qualified pipeline.”
            </div>
          </div>

          <form action={joinWaitlistAction} className="form">
            <input type="hidden" name="source" value="waitlist-landing" />
            <input type="hidden" name="utm_source" value="demandorchestrator-site" />
            <input type="hidden" name="utm_medium" value="web" />
            <input type="hidden" name="utm_campaign" value="early-access" />

            <label htmlFor="waitlist-email" className="form-label">Work Email</label>
            <input id="waitlist-email" className="input" name="email" type="email" placeholder="Enter your best email address" required />

            <label htmlFor="full-name" className="form-label">Full Name</label>
            <input id="full-name" className="input" name="full_name" placeholder="Your name" required />

            <label htmlFor="company" className="form-label">Company</label>
            <input id="company" className="input" name="company" placeholder="Company name" />

            <label htmlFor="role" className="form-label">Role</label>
            <input id="role" className="input" name="role" placeholder="Founder, PMM, Content Lead…" />

            <label htmlFor="team-size" className="form-label">Team Size</label>
            <select id="team-size" className="input" name="team_size" defaultValue="">
              <option value="" disabled>Select size</option>
              <option value="1">1 (solo)</option>
              <option value="2-5">2–5</option>
              <option value="6-20">6–20</option>
              <option value="21-100">21–100</option>
              <option value="100+">100+</option>
            </select>

            <label htmlFor="platforms" className="form-label">Priority Platforms</label>
            <input id="platforms" className="input" name="platforms" placeholder="X, LinkedIn, YouTube…" />

            <label htmlFor="use-case" className="form-label">Primary Use Case</label>
            <textarea id="use-case" className="input" name="use_case" rows={3} placeholder="What do you want the engine to do for you?" />

            <label htmlFor="timeline" className="form-label">Adoption Timeline</label>
            <select id="timeline" className="input" name="timeline" defaultValue="">
              <option value="" disabled>Select timeline</option>
              <option value="now">Now</option>
              <option value="30-days">Within 30 days</option>
              <option value="quarter">This quarter</option>
              <option value="exploring">Just exploring</option>
            </select>

            <label htmlFor="beta" className="form-label">Interested in Beta + onboarding interview?</label>
            <select id="beta" className="input" name="beta_interest" defaultValue="yes">
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>

            <label htmlFor="email-updates" className="form-label">Email updates</label>
            <select id="email-updates" className="input" name="email_updates" defaultValue="yes">
              <option value="yes">Yes, send updates</option>
              <option value="no">No updates</option>
            </select>

            <button className="btn" type="submit">Join Waitlist</button>
          </form>
        </section>
      </div>
    </main>
  );
}

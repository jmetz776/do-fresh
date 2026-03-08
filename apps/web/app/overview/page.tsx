import Link from 'next/link';

const platformMatrix: Array<{ name: string; publish: string[]; generate: string[]; status: 'live' | 'next' }> = [
  {
    name: 'X',
    publish: ['Text posts', 'Threads', 'Image + caption'],
    generate: ['Hooks', 'Replies', 'Thread variants'],
    status: 'live',
  },
  {
    name: 'LinkedIn',
    publish: ['Text posts', 'Image posts', 'Document/carousel'],
    generate: ['Authority posts', 'Carousel slide plans', 'Thought-leadership variants'],
    status: 'live',
  },
  {
    name: 'Instagram',
    publish: ['Feed caption + image', 'Carousels', 'Reel caption packs'],
    generate: ['Short hooks', 'Carousel narratives', 'Story sequence copy'],
    status: 'live',
  },
  {
    name: 'YouTube Shorts',
    publish: ['Short scripts', 'Title/description package'],
    generate: ['Hook-first scripts', 'CTA variants', 'Thumbnail briefs'],
    status: 'live',
  },
  {
    name: 'Email / Newsletter',
    publish: ['Campaign emails', 'Newsletter snippets', 'Follow-up emails'],
    generate: ['Subject lines', 'Preview text', 'Segment variants'],
    status: 'next',
  },
  {
    name: 'Reddit / Pinterest / Threads',
    publish: ['Community-native posts', 'Pin packages', 'Series posts'],
    generate: ['Platform-native variants', 'Conversation starters'],
    status: 'next',
  },
];

export default function OverviewPage() {
  return (
    <main className="ov-root">
      <style>{`
        .ov-root {
          min-height: 100vh;
          background: radial-gradient(1200px 600px at -5% -20%, rgba(103,232,249,.12), transparent 60%), #070b14;
          color: #eaf0ff;
          font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
        }
        .wrap { max-width: 980px; margin: 0 auto; padding: 28px 20px 70px; }
        .nav { display:flex; justify-content:space-between; align-items:center; margin-bottom: 34px; }
        .brand { font-weight: 700; letter-spacing:.08em; }
        .links { display:flex; gap:10px; flex-wrap:wrap; }
        .link { color:#dbe7ff; text-decoration:none; border:1px solid rgba(148,163,184,.35); padding:7px 11px; border-radius:999px; font-size:12px; }
        .hero h1 { font-size: clamp(2rem,5.4vw,3.7rem); margin: 0 0 10px; letter-spacing:-.02em; }
        .hero p { color:#9fb1d8; max-width: 720px; line-height:1.65; }
        .cta { display:flex; gap:10px; margin-top:18px; flex-wrap:wrap; }
        .btn { text-decoration:none; border-radius:10px; padding:11px 15px; font-weight:700; }
        .primary { background: linear-gradient(180deg,#67e8f9,#22d3ee); color:#052633; }
        .ghost { border:1px solid rgba(148,163,184,.35); color:#eaf0ff; }
        .grid { margin-top:26px; display:grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap:10px; }
        .card { border:1px solid rgba(148,163,184,.25); border-radius:12px; padding:14px; background: rgba(15,23,42,.38); }
        .card h3 { margin:0 0 6px; font-size: 15px; }
        .card p { margin:0; color:#9fb1d8; font-size: 14px; line-height:1.5; }
        .pwrap { margin-top: 24px; }
        .chips { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
        .chip { border:1px solid rgba(103,232,249,.35); border-radius:999px; padding:7px 10px; font-size:12px; color:#d7ecff; }
        .matrix { margin-top: 26px; display:grid; gap:12px; }
        .row { border:1px solid rgba(148,163,184,.28); border-radius:14px; padding:14px; background:linear-gradient(180deg, rgba(15,23,42,.52), rgba(15,23,42,.35)); }
        .row h4 { margin:0 0 8px; font-size: 18px; letter-spacing:-.01em; }
        .badge { font-size:11px; border-radius:999px; padding:5px 9px; border:1px solid rgba(148,163,184,.35); text-transform:uppercase; letter-spacing:.07em; }
        .badge.live { border-color: rgba(34,197,94,.5); color:#bbf7d0; background:rgba(34,197,94,.12); }
        .badge.next { border-color: rgba(56,189,248,.5); color:#bae6fd; background:rgba(56,189,248,.12); }
        .cols { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
        .cols ul { margin:6px 0 0; padding-left:18px; color:#c9d6f3; }
        .cols li { margin:4px 0; }
        @media (max-width: 760px) { .cols { grid-template-columns: 1fr; } }
      `}</style>

      <div className="wrap">
        <nav className="nav">
          <div className="brand">DEMANDORCHESTRATOR</div>
          <div className="links">
            <Link className="link" href="/overview">What we do</Link>
            <Link className="link" href="/login">Sign in</Link>
            <Link className="link" href="/register">Register</Link>
            <Link className="link" href="/waitlist">Waitlist</Link>
            <a className="link" href="mailto:support@demandorchestrator.ai">Support</a>
          </div>
        </nav>

        <section className="hero">
          <h1>Automate content ops without losing control.</h1>
          <p>
            DemandOrchestrator helps you move from idea to approved publish in minutes. Generate platform-native queues,
            apply cadence, and publish with governance guardrails built in.
          </p>
          <div className="cta">
            <Link className="btn primary" href="/register">Get Started</Link>
            <Link className="btn ghost" href="/studio">See Studio</Link>
          </div>
        </section>

        <section className="grid">
          <article className="card">
            <h3>Utility</h3>
            <p>Idea ingest, AI queue generation, approval flow, scheduling, and publish execution in one path.</p>
          </article>
          <article className="card">
            <h3>Services</h3>
            <p>Personal creator flow and premium corporate governance controls for role-based publishing.</p>
          </article>
          <article className="card">
            <h3>Control Layer</h3>
            <p>Authorization-aware workflow with explicit publish permissions and policy-first safeguards.</p>
          </article>
        </section>

        <section className="pwrap">
          <h3>Platform + Content Coverage</h3>
          <p className="hero" style={{ marginTop: 6, fontSize: 14, color: '#9fb1d8' }}>
            Major selling point: one engine that generates and publishes platform-native content across channels.
          </p>
          <div className="matrix">
            {platformMatrix.map((p) => (
              <article className="row" key={p.name}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <h4>{p.name}</h4>
                  <span className={`badge ${p.status}`}>{p.status === 'live' ? 'Live' : 'Next'}</span>
                </div>
                <div className="cols">
                  <div>
                    <div className="chip" style={{ display: 'inline-block' }}>Publish formats</div>
                    <ul>{p.publish.map((x) => <li key={x}>{x}</li>)}</ul>
                  </div>
                  <div>
                    <div className="chip" style={{ display: 'inline-block' }}>Generate outputs</div>
                    <ul>{p.generate.map((x) => <li key={x}>{x}</li>)}</ul>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

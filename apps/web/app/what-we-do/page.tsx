import Link from 'next/link';

const platforms = ['X', 'LinkedIn', 'Instagram', 'TikTok', 'YouTube'];

export default function WhatWeDoPage() {
  return (
    <main className="wwd-root">
      <style>{`
        .wwd-root { min-height:100vh; background:#070b14; color:#eaf0ff; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }
        .wrap { max-width: 1000px; margin: 0 auto; padding: 28px 20px 70px; }
        .nav { display:flex; justify-content:space-between; align-items:center; margin-bottom: 30px; gap:12px; flex-wrap:wrap; }
        .brand { font-weight: 700; letter-spacing:.08em; }
        .links { display:flex; gap:10px; flex-wrap:wrap; }
        .link { color:#dbe7ff; text-decoration:none; border:1px solid rgba(148,163,184,.35); padding:7px 11px; border-radius:999px; font-size:12px; }
        .waitlist { background:linear-gradient(180deg,#67e8f9,#22d3ee); color:#052633; border-color:transparent; font-weight:700; }
        h1 { font-size: clamp(2rem,5vw,3.4rem); margin: 0 0 10px; letter-spacing:-.02em; }
        .sub { color:#9fb1d8; line-height:1.65; max-width: 850px; }
        .theme { margin-top: 16px; font-size: 13px; letter-spacing:.08em; text-transform:uppercase; color:#8bdaf0; }
        .grid { margin-top: 24px; display:grid; grid-template-columns: repeat(auto-fit,minmax(250px,1fr)); gap:10px; }
        .card { border:1px solid rgba(148,163,184,.25); border-radius:12px; padding:14px; background: rgba(15,23,42,.38); }
        .card h3 { margin:0 0 6px; font-size: 15px; }
        .card p { margin:0; color:#9fb1d8; font-size: 14px; line-height:1.55; }
        .chips { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
        .chip { border:1px solid rgba(103,232,249,.35); border-radius:999px; padding:7px 10px; font-size:12px; color:#d7ecff; }
      `}</style>

      <div className="wrap">
        <nav className="nav">
          <div className="brand">DEMANDORCHESTRATOR</div>
          <div className="links">
            <Link className="link" href="/what-we-do">What we do</Link>
            <Link className="link" href="/provider-directory">Presenter Directory (Beta)</Link>
            <a className="link" href="mailto:support@demandorchestrator.ai">Support</a>
            <Link className="link" href="/waitlist">Waitlist</Link>
            <Link className="link waitlist" href="/login">Sign in</Link>
          </div>
        </nav>

        <section>
          <div className="theme">Trend to Brand Intelligence</div>
          <h1>From signal to safe publish, in one intelligent engine.</h1>
          <p className="sub">
            DemandOrchestrator turns trends, news, and brand context into platform-native content recommendations, then executes
            with policy guardrails. For individuals, it removes content bottlenecks. For companies, it adds governance, authorization,
            and auditability without slowing down execution.
          </p>
        </section>

        <section className="grid">
          <article className="card">
            <h3>Individuals</h3>
            <p>One operator can run the full stack: idea → queue generation → review → schedule → publish, with less clutter and faster cycle time.</p>
          </article>
          <article className="card">
            <h3>Companies</h3>
            <p>Corporate controls include role-aware workflows, publishing authorization, and policy-first execution paths suitable for brand-sensitive teams.</p>
          </article>
          <article className="card">
            <h3>Benefits</h3>
            <p>Higher throughput, fewer mistakes, clearer accountability, and a repeatable system that scales content operations without chaos.</p>
          </article>
          <article className="card">
            <h3>Mixed Queue Across Platforms</h3>
            <p>Build one coordinated queue that includes X, LinkedIn, Instagram, TikTok, and YouTube so each post works as part of a system, not random one-offs.</p>
          </article>
          <article className="card">
            <h3>Cadence Engine</h3>
            <p>Apply cadence rules to approved content so the engine maps posts into a consistent publishing rhythm without manual calendar juggling.</p>
          </article>
          <article className="card">
            <h3>Review Before Publish</h3>
            <p>Approve, edit, and schedule in one flow so quality and brand alignment stay high while speed stays high too.</p>
          </article>
        </section>

        <section style={{ marginTop: 22 }}>
          <h3>How it works</h3>
          <div className="grid" style={{ marginTop: 10 }}>
            <article className="card">
              <h3>1) Detect what matters now</h3>
              <p>We track current trends and relevant signals so you are creating content around what people already care about.</p>
            </article>
            <article className="card">
              <h3>2) Match to your brand</h3>
              <p>The engine filters opportunities based on your audience, goals, and brand rules so suggestions stay useful and on-brand.</p>
            </article>
            <article className="card">
              <h3>3) Turn insight into output</h3>
              <p>It generates queue-ready content, supports review and scheduling, and helps you publish consistently across platforms.</p>
            </article>
          </div>
        </section>

        <section style={{ marginTop: 22 }}>
          <h3>Platforms</h3>
          <div className="chips">
            {platforms.map((p) => <span className="chip" key={p}>{p}</span>)}
          </div>
        </section>
      </div>
    </main>
  );
}

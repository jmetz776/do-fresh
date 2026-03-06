import Link from 'next/link';

export default function ProviderDirectoryPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#070b14', color: '#eaf0ff', fontFamily: 'Inter, system-ui', padding: '28px 20px 70px' }}>
      <div style={{ maxWidth: 980, margin: '0 auto' }}>
        <nav style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', marginBottom: 26 }}>
          <strong style={{ letterSpacing: '.08em' }}>DEMANDORCHESTRATOR</strong>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Link href="/what-we-do" style={{ color: '#dbe7ff', textDecoration: 'none', border: '1px solid rgba(148,163,184,.35)', borderRadius: 999, padding: '7px 11px', fontSize: 12 }}>What we do</Link>
            <Link href="/provider-directory" style={{ color: '#dbe7ff', textDecoration: 'none', border: '1px solid rgba(148,163,184,.35)', borderRadius: 999, padding: '7px 11px', fontSize: 12 }}>Presenter Directory (Beta)</Link>
            <a href="mailto:support@demandorchestrator.ai" style={{ color: '#dbe7ff', textDecoration: 'none', border: '1px solid rgba(148,163,184,.35)', borderRadius: 999, padding: '7px 11px', fontSize: 12 }}>Support</a>
            <Link href="/waitlist" style={{ color: '#dbe7ff', textDecoration: 'none', border: '1px solid rgba(148,163,184,.35)', borderRadius: 999, padding: '7px 11px', fontSize: 12 }}>Waitlist</Link>
            <Link href="/login" style={{ color: '#052633', textDecoration: 'none', border: '1px solid transparent', background: 'linear-gradient(180deg,#67e8f9,#22d3ee)', borderRadius: 999, padding: '7px 11px', fontSize: 12, fontWeight: 700 }}>Sign in</Link>
          </div>
        </nav>

        <h1 style={{ margin: '0 0 10px', fontSize: 'clamp(2rem,5vw,3.2rem)', letterSpacing: '-.02em' }}>Provider Directory (Beta)</h1>
        <p style={{ margin: 0, color: '#9fb1d8', lineHeight: 1.65, maxWidth: 860 }}>
          The Provider Directory allows approved individuals to join as digital spokespersons whose likeness can be used in generated content experiences. Providers are compensated for usage and can define clear restrictions on the types of content they do not want to participate in.
        </p>

        <section style={{ marginTop: 18, display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))', gap: 10 }}>
          <article style={{ border: '1px solid rgba(148,163,184,.25)', borderRadius: 12, padding: 14, background: 'rgba(15,23,42,.38)' }}>
            <h3 style={{ margin: '0 0 6px', fontSize: 15 }}>Who can join</h3>
            <p style={{ margin: 0, color: '#9fb1d8', lineHeight: 1.55 }}>Anyone can apply to become a provider in beta, subject to review and acceptance criteria.</p>
          </article>
          <article style={{ border: '1px solid rgba(148,163,184,.25)', borderRadius: 12, padding: 14, background: 'rgba(15,23,42,.38)' }}>
            <h3 style={{ margin: '0 0 6px', fontSize: 15 }}>Consent & release</h3>
            <p style={{ margin: 0, color: '#9fb1d8', lineHeight: 1.55 }}>A signed release and consent agreement is required before any likeness is activated for platform use.</p>
          </article>
          <article style={{ border: '1px solid rgba(148,163,184,.25)', borderRadius: 12, padding: 14, background: 'rgba(15,23,42,.38)' }}>
            <h3 style={{ margin: '0 0 6px', fontSize: 15 }}>Usage controls</h3>
            <p style={{ margin: 0, color: '#9fb1d8', lineHeight: 1.55 }}>Providers can set restrictions on disallowed content categories and participation boundaries.</p>
          </article>
          <article style={{ border: '1px solid rgba(148,163,184,.25)', borderRadius: 12, padding: 14, background: 'rgba(15,23,42,.38)' }}>
            <h3 style={{ margin: '0 0 6px', fontSize: 15 }}>Customer access model</h3>
            <p style={{ margin: 0, color: '#9fb1d8', lineHeight: 1.55 }}>Provider Directory access is available to premium top-tier customers as an add-on, priced per provider.</p>
          </article>
        </section>

        <p style={{ marginTop: 14, color: '#8fb0d8', fontSize: 13 }}>
          Pricing details are currently being finalized and will be published before general availability.
        </p>
      </div>
    </main>
  );
}

export default function EarlyAccessPage({ searchParams }: { searchParams?: { next?: string } }) {
  const nextPath = searchParams?.next || '/studio';

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: '#0b1220', color: '#e8eefc', padding: 24 }}>
      <section style={{ width: '100%', maxWidth: 460, border: '1px solid rgba(148,163,184,.35)', borderRadius: 14, background: 'rgba(18,28,51,.8)', padding: 18 }}>
        <h1 style={{ marginTop: 0 }}>Early Access</h1>
        <p style={{ color: '#a5b4d4' }}>Studio is currently invite-only while we finalize platform OAuth and video integrations.</p>

        <form action="/early-access/unlock" method="post" style={{ display: 'grid', gap: 10 }}>
          <input type="hidden" name="next" value={nextPath} />
          <input
            name="access_key"
            type="password"
            placeholder="Enter access key"
            required
            style={{ border: '1px solid rgba(148,163,184,.4)', borderRadius: 10, padding: '10px 12px', background: 'rgba(15,23,42,.55)', color: '#e8eefc' }}
          />
          <button type="submit" style={{ border: '1px solid #0284c7', borderRadius: 10, padding: '10px 12px', background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', color: '#062437', fontWeight: 800 }}>
            Unlock Studio
          </button>
        </form>
      </section>
    </main>
  );
}

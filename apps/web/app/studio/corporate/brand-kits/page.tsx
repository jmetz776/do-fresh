import Link from 'next/link';

export default function BrandKitsPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 24 }}>
      <div style={{ maxWidth: 980, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1>Corporate · Brand Kits</h1>
          <Link href="/studio" style={{ color: '#c5d3f8' }}>← Back to Studio</Link>
        </div>
        <p style={{ color: '#a5b4d4' }}>Store brand voice, banned terms, logo assets, and CTA preferences by team/brand.</p>
        <section style={{ border: '1px solid rgba(148,163,184,.3)', borderRadius: 12, padding: 14, background: 'rgba(18,28,51,.75)' }}>
          <div style={{ display: 'grid', gap: 8 }}>
            <button style={btn}>Create Brand Kit</button>
            <button style={btn}>Upload Logos + Visual Assets</button>
            <button style={btn}>Set Voice Rules + Compliance Terms</button>
          </div>
        </section>
      </div>
    </main>
  );
}

const btn = { background: 'rgba(15,23,42,.6)', color: '#e8eefc', border: '1px solid rgba(148,163,184,.35)', borderRadius: 10, padding: '10px 12px', textAlign: 'left' as const };

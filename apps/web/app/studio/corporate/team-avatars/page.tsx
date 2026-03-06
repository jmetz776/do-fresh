import Link from 'next/link';

export default function TeamAvatarsPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 24 }}>
      <div style={{ maxWidth: 980, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1>Corporate · Team Avatars</h1>
          <Link href="/studio" style={{ color: '#c5d3f8' }}>← Back to Studio</Link>
        </div>
        <p style={{ color: '#a5b4d4' }}>Create and manage presenter profiles for your full team with consent + usage controls.</p>
        <section style={{ border: '1px solid rgba(148,163,184,.3)', borderRadius: 12, padding: 14, background: 'rgba(18,28,51,.75)' }}>
          <div style={{ display: 'grid', gap: 8 }}>
            <button style={btn}>Add Team Avatar</button>
            <button style={btn}>Import Existing Presenter</button>
            <button style={btn}>Set Usage Permissions</button>
          </div>
        </section>
      </div>
    </main>
  );
}

const btn = { background: 'rgba(15,23,42,.6)', color: '#e8eefc', border: '1px solid rgba(148,163,184,.35)', borderRadius: 10, padding: '10px 12px', textAlign: 'left' as const };

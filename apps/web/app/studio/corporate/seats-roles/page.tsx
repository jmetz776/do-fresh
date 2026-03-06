import Link from 'next/link';

export default function SeatsRolesPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 24 }}>
      <div style={{ maxWidth: 980, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1>Corporate · Seats & Roles</h1>
          <Link href="/studio" style={{ color: '#c5d3f8' }}>← Back to Studio</Link>
        </div>
        <p style={{ color: '#a5b4d4' }}>Control who can draft, approve, schedule, and publish.</p>
        <section style={{ border: '1px solid rgba(148,163,184,.3)', borderRadius: 12, padding: 14, background: 'rgba(18,28,51,.75)' }}>
          <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.8 }}>
            <li>Admin: workspace + billing + policies</li>
            <li>Editor: draft + rewrite + approve</li>
            <li>Publisher: schedule + publish only</li>
            <li>Viewer: read-only analytics/review</li>
          </ul>
        </section>
      </div>
    </main>
  );
}

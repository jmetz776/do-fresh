import Link from 'next/link';

const presenters = [
  { id: 'synth-01', name: 'Avery', style: 'Confident explainer', tone: 'Warm, professional' },
  { id: 'synth-02', name: 'Noah', style: 'Founder-operator', tone: 'Direct, tactical' },
  { id: 'synth-03', name: 'Maya', style: 'Marketing strategist', tone: 'Sharp, upbeat' },
  { id: 'synth-04', name: 'Liam', style: 'Calm educator', tone: 'Clear, grounded' },
  { id: 'synth-05', name: 'Zara', style: 'Story-led presenter', tone: 'Energetic, polished' },
  { id: 'synth-06', name: 'Ethan', style: 'B2B advisor', tone: 'Concise, credible' },
  { id: 'synth-07', name: 'Sofia', style: 'Brand storyteller', tone: 'Friendly, modern' },
  { id: 'synth-08', name: 'Kai', style: 'Technical walkthrough', tone: 'Precise, calm' },
  { id: 'synth-09', name: 'Amara', style: 'Social growth host', tone: 'High-energy, confident' },
  { id: 'synth-10', name: 'Jonah', style: 'Executive brief', tone: 'Authoritative, clean' },
  { id: 'synth-11', name: 'Rin', style: 'Product demo host', tone: 'Clear, approachable' },
  { id: 'synth-12', name: 'Leila', style: 'Lifestyle UGC', tone: 'Natural, conversational' },
];

export default function ModelsPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 24 }}>
      <div style={{ maxWidth: 1060, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 34, letterSpacing: '-.02em' }}>Presenter Directory</h1>
            <p style={{ marginTop: 8, color: '#a5b4d4' }}>Start with synthetic presenters now. Human model marketplace next.</p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Link href="/studio" style={{ color: '#c5d3f8' }}>← Back to Studio</Link>
            <Link href="/studio/model-signup" style={{ color: '#38bdf8' }}>Model signup ↗</Link>
          </div>
        </div>

        <section style={{ border: '1px solid rgba(148,163,184,.3)', borderRadius: 14, padding: 14, background: 'rgba(18,28,51,.75)', marginBottom: 14 }}>
          <h2 style={{ marginTop: 0 }}>Usage notes</h2>
          <ul style={{ color: '#c7d2ee', lineHeight: 1.6 }}>
            <li>All synthetic presenters are licensed for standard commercial use inside DO.</li>
            <li>No political deception, impersonation, or misleading identity claims.</li>
            <li>Human model marketplace will require explicit waiver + payout terms.</li>
          </ul>
        </section>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 12 }}>
          {presenters.map((p) => (
            <article key={p.id} style={{ border: '1px solid rgba(148,163,184,.26)', borderRadius: 12, padding: 12, background: 'rgba(22,34,61,.8)' }}>
              <div style={{ fontSize: 12, color: '#93c5fd', marginBottom: 6 }}>{p.id}</div>
              <h3 style={{ margin: '0 0 6px 0' }}>{p.name}</h3>
              <div style={{ fontSize: 13, color: '#c7d2ee' }}>{p.style}</div>
              <div style={{ fontSize: 12, color: '#a5b4d4', marginTop: 4 }}>{p.tone}</div>
              <button style={{ marginTop: 10, width: '100%', background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', border: '1px solid #0284c7', color: '#062437', borderRadius: 10, padding: '8px 10px', fontWeight: 700 }}>Use presenter</button>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}

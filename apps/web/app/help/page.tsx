import Link from 'next/link';

const faq = [
  {
    q: 'How does queue generation work?',
    a: 'You provide an idea and channel goals. The engine generates a queue mix and prepares drafts based on your plan caps and quality rules.',
  },
  {
    q: 'Why did my video render fail?',
    a: 'Most failures are provider delays, missing integration keys, or plan/cap constraints. The system retries where possible and logs exact failure reason in operator diagnostics.',
  },
  {
    q: 'How are premium backgrounds billed?',
    a: 'Each plan includes a monthly premium background allowance. Usage above included allowance is billed at overage pricing configured for your workspace.',
  },
  {
    q: 'How do avatar marketplace purchases work?',
    a: 'Workspaces can purchase licensed avatar listings. Render usage is tied to active purchases and tracked for provider payout accrual.',
  },
  {
    q: 'How do I get support?',
    a: 'Use your internal support channel or operator console diagnostics to capture run IDs, source IDs, and error states for fast resolution.',
  },
];

export default function HelpPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 22, fontFamily: 'Inter, system-ui' }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <h1 style={{ margin: 0 }}>Help & FAQ</h1>
            <p style={{ margin: '6px 0 0', color: '#9fb2d6' }}>Quick answers without the noise.</p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Link href="/studio" style={{ color: '#cce5ff' }}>Back to Studio</Link>
            <Link href="/studio/analytics" style={{ color: '#cce5ff' }}>Analytics</Link>
          </div>
        </div>

        <section style={{ border: '1px solid rgba(148,163,184,.24)', borderRadius: 12, padding: 14, background: 'rgba(15,23,42,.7)' }}>
          <div style={{ display: 'grid', gap: 10 }}>
            {faq.map((x) => (
              <details key={x.q} style={{ border: '1px solid rgba(148,163,184,.24)', borderRadius: 10, padding: 10, background: 'rgba(2,6,23,.35)' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 700 }}>{x.q}</summary>
                <p style={{ color: '#c7d2ee', margin: '8px 0 0' }}>{x.a}</p>
              </details>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

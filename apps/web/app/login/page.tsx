"use client";

import { useEffect, useState } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [magicUrl, setMagicUrl] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token');
    if (!token) return;

    (async () => {
      setBusy(true);
      setError('');
      const res = await fetch('/api/auth/magic-link/consume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data?.detail || 'Magic link invalid/expired');
        setBusy(false);
        return;
      }

      await fetch('/auth/set-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: data?.user?.id,
          userEmail: data?.user?.email,
          workspaceId: data?.workspaceId,
          token: data?.token,
        }),
      });

      window.location.href = '/studio';
    })();
  }, []);

  async function requestMagicLink(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    setMagicUrl('');

    const res = await fetch(`/api/auth/magic-link/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    const data = await res.json().catch(() => ({}));
    setBusy(false);
    if (!res.ok) {
      setError(data?.detail || 'Unable to issue magic link');
      return;
    }

    setMagicUrl(data?.magicUrl || '');
  }

  return (
    <main style={rootStyle}>
      <style>{`
        .field::placeholder { color: #8ea3cb; }
      `}</style>
      <div style={cinemaOverlay} />
      <section style={cardStyle}>
        <div style={{ fontSize: 12, letterSpacing: '.16em', opacity: 0.8 }}>DEMANDORCHESTRATOR</div>
        <h1 style={{ margin: '8px 0 8px', fontSize: 'clamp(1.9rem,4vw,2.6rem)', letterSpacing: '-.02em' }}>Enter Studio</h1>
        <p style={{ color: '#b8c8e8', marginTop: 0, lineHeight: 1.6 }}>
          Invite-only beta. Use your invited email and we’ll send a secure magic link.
        </p>

        <form onSubmit={requestMagicLink} style={{ display: 'grid', gap: 10 }}>
          <input
            className="field"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle}
          />
          <button type="submit" disabled={busy} style={{ ...primaryBtn, opacity: busy ? 0.75 : 1 }}>
            {busy ? 'Sending link…' : 'Send magic link'}
          </button>
        </form>

        {magicUrl ? (
          <div style={successCard}>
            <div style={{ marginBottom: 6, fontWeight: 700 }}>Magic link ready</div>
            <a href={magicUrl} style={{ color: '#7dd3fc', wordBreak: 'break-all' }}>{magicUrl}</a>
          </div>
        ) : null}

        {error ? <p style={{ color: '#fb7185', marginTop: 10 }}>{error}</p> : null}

        <div style={{ marginTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <a href="/register" style={linkPill}>Create account</a>
          <a href="/waitlist" style={linkPill}>Need access? Join waitlist</a>
        </div>
      </section>
    </main>
  );
}

const rootStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: 'radial-gradient(900px 500px at 0% -10%, rgba(56,189,248,.18), transparent 60%), radial-gradient(900px 500px at 100% 0%, rgba(59,130,246,.16), transparent 60%), #060b16',
  color: '#eaf0ff',
  fontFamily: 'Inter, system-ui',
  position: 'relative',
  overflow: 'hidden',
  display: 'grid',
  placeItems: 'center',
  padding: 24,
};

const cinemaOverlay: React.CSSProperties = {
  position: 'absolute',
  inset: 0,
  backgroundImage: 'linear-gradient(rgba(148,163,184,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.05) 1px, transparent 1px)',
  backgroundSize: '34px 34px',
  maskImage: 'radial-gradient(circle at 50% 30%, black 35%, transparent 82%)',
  pointerEvents: 'none',
};

const cardStyle: React.CSSProperties = {
  width: '100%',
  maxWidth: 500,
  border: '1px solid rgba(148,163,184,.26)',
  borderRadius: 20,
  padding: 24,
  background: 'linear-gradient(180deg, rgba(18,28,51,.88), rgba(12,18,32,.82))',
  boxShadow: '0 30px 80px rgba(2,6,23,.5)',
  position: 'relative',
  zIndex: 1,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  borderRadius: 10,
  border: '1px solid rgba(148,163,184,.35)',
  background: 'rgba(2,6,23,.5)',
  color: '#eaf0ff',
  padding: 10,
};

const primaryBtn: React.CSSProperties = {
  background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)',
  border: '1px solid #0284c7',
  color: '#062437',
  borderRadius: 10,
  padding: '10px 14px',
  fontWeight: 800,
  cursor: 'pointer',
};

const successCard: React.CSSProperties = {
  marginTop: 12,
  padding: 10,
  border: '1px solid rgba(56,189,248,.45)',
  borderRadius: 10,
  background: 'rgba(12,74,110,.25)',
};

const linkPill: React.CSSProperties = {
  textDecoration: 'none',
  color: '#dbe7ff',
  border: '1px solid rgba(148,163,184,.35)',
  borderRadius: 999,
  padding: '7px 12px',
  fontSize: 12,
};

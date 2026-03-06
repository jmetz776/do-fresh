"use client";

import { useState } from 'react';

export default function RegisterPage() {
  const [mode, setMode] = useState<'personal' | 'corporate'>('personal');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [workspaceName, setWorkspaceName] = useState('My Workspace');
  const [companyDomain, setCompanyDomain] = useState('');
  const [error, setError] = useState('');

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    const path = mode === 'corporate' ? '/api/auth/register/corporate' : '/api/auth/register/personal';
    const payload: any = { email, password, workspaceName };
    if (mode === 'corporate') payload.companyDomain = companyDomain;

    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(data?.detail || 'Registration failed');
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
  }

  return (
    <main style={{ maxWidth: 460, margin: '48px auto', padding: 16 }}>
      <h1>Create account</h1>
      <p style={{ opacity: 0.8 }}>Invite-only beta: registration works only for invited emails.</p>
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <button onClick={() => setMode('personal')} type="button">Personal</button>
        <button onClick={() => setMode('corporate')} type="button">Corporate</button>
      </div>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 10 }}>
        <input placeholder="Work email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <input placeholder="Workspace name" value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} required />
        {mode === 'corporate' ? (
          <input placeholder="Company domain (e.g. acme.com)" value={companyDomain} onChange={(e) => setCompanyDomain(e.target.value)} required />
        ) : null}
        <button type="submit">Create {mode} account</button>
      </form>
      {error ? <p style={{ color: '#ef4444' }}>{error}</p> : null}
      <p style={{ marginTop: 12 }}><a href="/login">Already have an account?</a></p>
    </main>
  );
}

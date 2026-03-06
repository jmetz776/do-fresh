'use server';

import { redirect } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export async function joinWaitlistAction(formData: FormData) {
  const email = String(formData.get('email') || '').trim();
  if (!email) return;

  const payload = {
    email,
    source: String(formData.get('source') || 'waitlist'),
    utm_source: String(formData.get('utm_source') || ''),
    utm_medium: String(formData.get('utm_medium') || ''),
    utm_campaign: String(formData.get('utm_campaign') || ''),
    profile: {
      full_name: String(formData.get('full_name') || ''),
      company: String(formData.get('company') || ''),
      role: String(formData.get('role') || ''),
      team_size: String(formData.get('team_size') || ''),
      platforms: String(formData.get('platforms') || ''),
      use_case: String(formData.get('use_case') || ''),
      timeline: String(formData.get('timeline') || ''),
      beta_interest: String(formData.get('beta_interest') || ''),
      email_updates: String(formData.get('email_updates') || ''),
    },
  };

  const res = await fetch(`${API_BASE}/v1/leads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    redirect('/waitlist?error=1');
  }

  redirect('/waitlist?submitted=1');
}

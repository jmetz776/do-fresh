'use server';

import { revalidatePath } from 'next/cache';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export async function updateLeadStatusAction(formData: FormData) {
  const leadId = Number(formData.get('lead_id'));
  const status = String(formData.get('status') || '').trim();
  if (!leadId || !status) return;

  const res = await fetch(`${API_BASE}/v1/leads/${leadId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });

  if (!res.ok) {
    throw new Error(`Failed to update lead status: ${res.status}`);
  }

  revalidatePath('/waitlist/admin');
}

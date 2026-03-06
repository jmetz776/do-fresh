const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const DEFAULT_WORKSPACE = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';

export async function getSources(workspaceId: string = DEFAULT_WORKSPACE) {
  const res = await fetch(`${API_BASE}/sources?workspaceId=${workspaceId}`, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

export async function getContent(workspaceId: string = DEFAULT_WORKSPACE, status?: string) {
  const q = status ? `&status=${encodeURIComponent(status)}` : '';
  const res = await fetch(`${API_BASE}/content?workspaceId=${workspaceId}${q}`, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

export async function getSchedules(workspaceId: string = DEFAULT_WORKSPACE, status?: string) {
  const q = status ? `&status=${encodeURIComponent(status)}` : '';
  const res = await fetch(`${API_BASE}/schedules?workspaceId=${workspaceId}${q}`, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

export async function getDashboard(workspaceId: string = DEFAULT_WORKSPACE) {
  const res = await fetch(`${API_BASE}/dashboard?workspaceId=${workspaceId}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

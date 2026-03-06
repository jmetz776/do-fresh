'use server';

import { revalidatePath } from 'next/cache';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const DEFAULT_WORKSPACE = process.env.NEXT_PUBLIC_WORKSPACE_ID || 'default';
function actorHeaders() {
  const c = cookies();
  const token = c.get('do_api_token')?.value || '';
  if (!token) redirect('/login?next=/studio');
  return { Authorization: `Bearer ${token}` };
}

async function post(path: string, body?: unknown) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...actorHeaders() },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) redirect('/login?next=/studio');
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    console.error(`POST ${path} failed: ${res.status}${detail ? ` :: ${detail.slice(0, 300)}` : ''}`);
    let parsedDetail = detail;
    try {
      const j = JSON.parse(detail || '{}');
      parsedDetail = String(j?.detail || detail || '');
    } catch {}
    return { ok: false, status: res.status, detail: parsedDetail } as const;
  }
  return res.json();
}

export async function createSourceAction(formData: FormData) {
  const rawPayload = String(formData.get('raw_payload') || '').trim();
  const type = String(formData.get('type') || 'csv');
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE);
  if (!rawPayload) return;

  await post('/sources', { workspaceId, type, rawPayload });
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function createIdeaSourceAction(formData: FormData) {
  const idea = String(formData.get('idea') || '').trim();
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE);
  if (!idea) return;

  const selectedPlatform = String(formData.get('platform') || 'x').trim().toLowerCase();
  const studioPath = `/studio?platform=${encodeURIComponent(selectedPlatform)}`;

  const oneLine = idea.replace(/\s+/g, ' ').trim();
  const titleSeed = oneLine.split(/[.!?]/)[0].slice(0, 80).trim() || 'New idea';
  const platform = String(formData.get('platform') || 'x').trim().toLowerCase();
  const videoMode = String(formData.get('video_mode') || 'avatar').trim().toLowerCase();

  const files = (formData.getAll('context_files') || []) as File[];
  const contextChunks: string[] = [];
  for (const f of files) {
    if (!f || !f.name) continue;
    const type = (f.type || '').toLowerCase();
    const isTextLike = type.startsWith('text/') || /\.(txt|md|csv|json)$/i.test(f.name);
    if (isTextLike) {
      try {
        const text = (await f.text()).replace(/\s+/g, ' ').trim();
        if (text) contextChunks.push(`[file:${f.name}] ${text.slice(0, 600)}`);
      } catch {
        contextChunks.push(`[file:${f.name}] (unable to parse text)`);
      }
    } else if (type.startsWith('image/') || /\.(png|jpg|jpeg|webp|gif|svg)$/i.test(f.name)) {
      contextChunks.push(`[image:${f.name}] visual brand/context reference provided`);
    } else {
      contextChunks.push(`[file:${f.name}] additional context provided`);
    }
  }

  const modeTag = (platform === 'tiktok' || platform === 'youtube' || platform === 'instagram')
    ? `[video_mode:${videoMode}]`
    : '';
  const mergedBody = [oneLine, modeTag, ...contextChunks].filter(Boolean).join(' | ');
  const escCsv = (v: string) => `"${v.replace(/"/g, '""')}"`;
  const rawPayload = `title,body\n${escCsv(titleSeed)},${escCsv(mergedBody)}`;

  const src = await post('/sources', { workspaceId, type: 'csv', rawPayload });
  if (!src || !(src as any).id) {
    redirect(`${studioPath}&error=idea_create_failed`);
  }

  await post(`/sources/${encodeURIComponent((src as any).id)}/normalize`);
  revalidatePath('/studio');
  redirect(`${studioPath}&notice=idea_saved`);
}

export async function normalizeSourceAction(formData: FormData) {
  const sourceId = String(formData.get('source_id') || '').trim();
  if (!sourceId) return;
  await post(`/sources/${sourceId}/normalize`);
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function generateContentAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE);
  const sourceItemId = String(formData.get('source_item_id') || '').trim();
  const platform = String(formData.get('platform') || 'x').trim().toLowerCase();
  const studioPath = `/studio?platform=${encodeURIComponent(platform)}`;
  const channels = String(formData.get('channels') || platform || 'x')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  let variantCount = Number(formData.get('variant_count') || 1);
  if (platform === 'linkedin') variantCount = Math.min(6, variantCount || 6);
  if (platform === 'instagram') variantCount = Math.min(8, variantCount || 8);
  if (platform === 'tiktok' || platform === 'youtube') variantCount = Math.min(4, variantCount || 4);

  if (!sourceItemId || channels.length === 0) return;

  const res = await post('/content/generate', { workspaceId, sourceItemId, channels, variantCount });
  if (!res || !(res as any).contentItems) {
    const status = String((res as any)?.status || 'unknown');
    const detail = encodeURIComponent(String((res as any)?.detail || 'no_detail'));
    redirect(`${studioPath}&error=queue_generate_failed:${status}:${detail}`);
  }
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
  redirect(`${studioPath}&notice=queue_generated`);
}

export async function buildUnifiedQueueAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const idea = String(formData.get('idea') || '').trim();
  const platform = String(formData.get('platform') || 'x').trim().toLowerCase();
  const queueCap = Math.max(3, Math.min(60, Number(formData.get('queue_cap') || 20)));
  const timezone = String(formData.get('timezone') || 'America/New_York').trim();

  if (!idea) {
    redirect('/studio/queue?error=missing_idea');
  }

  const mixText = Math.max(0, Number(formData.get('mix_text') || 60));
  const mixFaceless = Math.max(0, Number(formData.get('mix_faceless') || 25));
  const mixAvatar = Math.max(0, Number(formData.get('mix_avatar') || 15));
  const sum = Math.max(1, mixText + mixFaceless + mixAvatar);
  const textCount = Math.max(1, Math.round((queueCap * mixText) / sum));
  const facelessCount = Math.max(0, Math.round((queueCap * mixFaceless) / sum));
  const avatarCount = Math.max(0, queueCap - textCount - facelessCount);

  const oneLine = idea.replace(/\s+/g, ' ').trim();
  const escCsv = (v: string) => `"${v.replace(/"/g, '""')}"`;
  const rawPayload = `title,body\n${escCsv(oneLine.slice(0, 80) || 'Unified queue idea')},${escCsv(oneLine)}`;

  const src = await post('/sources', { workspaceId, type: 'csv', rawPayload });
  const sourceId = String((src as any)?.id || '').trim();
  if (!sourceId) {
    redirect('/studio/queue?error=queue_source_create_failed');
  }

  await post(`/sources/${encodeURIComponent(sourceId)}/normalize`);

  let sourceItemId = '';
  try {
    const itemsRes = await fetch(`${API_BASE}/sources/${encodeURIComponent(sourceId)}/items`, {
      cache: 'no-store',
      headers: actorHeaders(),
    });
    const items = (await itemsRes.json().catch(() => [])) as Array<any>;
    sourceItemId = String((items?.[0] as any)?.id || '').trim();
  } catch {}

  if (!sourceItemId) {
    redirect('/studio/queue?error=queue_source_item_missing');
  }

  const channels = [platform || 'x'];
  const gen = await post('/content/generate', { workspaceId, sourceItemId, channels, variantCount: textCount });
  if ((gen as any)?.ok === false) {
    const detail = String((gen as any)?.detail || 'generate_failed').slice(0, 140);
    redirect(`/studio/queue?error=${encodeURIComponent(detail)}`);
  }

  revalidatePath('/studio');
  revalidatePath('/studio/queue');
  revalidatePath('/ops');
  redirect(`/studio/queue?notice=${encodeURIComponent(`Unified queue built: ${textCount} text ready · ${facelessCount} faceless planned · ${avatarCount} avatar planned · timezone ${timezone}`)}`);
}

export async function approveContentAction(formData: FormData) {
  const contentId = String(formData.get('content_id') || '').trim();
  if (!contentId) return;
  await post(`/content/${contentId}/approve`);
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function updateContentAction(formData: FormData) {
  const contentId = String(formData.get('content_id') || '').trim();
  if (!contentId) return;

  const title = String(formData.get('title') || '').trim();
  const hook = String(formData.get('hook') || '').trim();
  const caption = String(formData.get('caption') || '').trim();

  const res = await fetch(`${API_BASE}/content/${encodeURIComponent(contentId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...actorHeaders() },
    body: JSON.stringify({ title, hook, caption }),
  });
  if (!res.ok) throw new Error(`PATCH /content/${contentId} failed: ${res.status}`);
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function regenerateContentAction(formData: FormData) {
  const contentId = String(formData.get('content_id') || '').trim();
  const guidance = String(formData.get('guidance') || '').trim();
  if (!contentId) return;

  await post(`/content/${encodeURIComponent(contentId)}/regenerate`, { guidance });
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function scheduleContentAction(formData: FormData) {
  const contentItemId = String(formData.get('content_id') || '').trim();
  const publishAt = String(formData.get('publish_at') || '').trim();
  const timezone = String(formData.get('timezone') || 'America/New_York');
  if (!contentItemId || !publishAt) return;

  const iso = new Date(publishAt).toISOString();
  await post('/schedules', { contentItemId, publishAt: iso, timezone });
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

function nextWeekdaySlot(base: Date, hour = 9, minute = 15) {
  const d = new Date(base);
  d.setHours(hour, minute, 0, 0);
  while (d.getDay() === 0 || d.getDay() === 6 || d <= base) {
    d.setDate(d.getDate() + 1);
  }
  return d;
}

export async function applyCadenceAction(formData: FormData) {
  const timezone = String(formData.get('timezone') || 'America/New_York').trim();
  const preset = String(formData.get('cadence') || 'weekdays').trim();
  const rawIds = String(formData.get('approved_ids') || '').trim();
  const ids = rawIds.split(',').map((s) => s.trim()).filter(Boolean);
  if (!ids.length) return;

  const now = new Date();
  let cursor = new Date(now);

  for (let i = 0; i < ids.length; i += 1) {
    let publish = new Date(cursor);

    if (preset === 'daily') {
      publish.setDate(publish.getDate() + (i === 0 ? 0 : 1));
      publish.setHours(9, 15, 0, 0);
      if (publish <= now) publish.setDate(publish.getDate() + 1);
    } else if (preset === 'three_weekly') {
      if (i === 0) {
        publish = nextWeekdaySlot(now, 9, 15);
      } else {
        publish = new Date(cursor);
        publish.setDate(publish.getDate() + 2);
        publish = nextWeekdaySlot(publish, 9, 15);
      }
    } else {
      // weekdays default
      publish = nextWeekdaySlot(cursor, 9, 15);
    }

    await post('/schedules', {
      contentItemId: ids[i],
      publishAt: publish.toISOString(),
      timezone,
    });

    cursor = new Date(publish);
    cursor.setDate(cursor.getDate() + 1);
  }

  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function runPublishAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE);
  await post(`/publish/run?workspaceId=${encodeURIComponent(workspaceId)}`);
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function retryFailedPublishAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE);
  await post(`/publish/retry-failed?workspaceId=${encodeURIComponent(workspaceId)}`);
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function retryOneFailedPublishAction(formData: FormData) {
  const scheduleId = String(formData.get('schedule_id') || '').trim();
  if (!scheduleId) return;
  await post(`/publish/retry/${encodeURIComponent(scheduleId)}`);
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/ops');
}

export async function apifyRunAction(formData: FormData) {
  const actorId = String(formData.get('actor_id') || '').trim();
  const rawInput = String(formData.get('actor_input_json') || '').trim();
  if (!actorId) return;

  let input: Record<string, unknown> = {};
  if (rawInput) {
    try {
      input = JSON.parse(rawInput);
    } catch {
      throw new Error('Apify input must be valid JSON');
    }
  }

  const res = await post('/integrations/apify/run', { actorId, input });
  revalidatePath('/ops');
  const runId = String((res as any)?.runId || '').trim();
  if (runId) {
    cookies().set('do_last_apify_run_id', runId, { httpOnly: true, sameSite: 'lax', path: '/', secure: process.env.NODE_ENV === 'production' });
  }
  if (runId) redirect(`/ops?apifyRunId=${encodeURIComponent(runId)}`);
  redirect('/ops?apifyRunId=unknown');
}

export async function apifyImportRunAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const runId = String(formData.get('run_id') || '').trim();
  const limit = Number(formData.get('limit') || 100);
  if (!runId) return;

  const res = await post(`/integrations/apify/import/${encodeURIComponent(runId)}`, { workspaceId, limit });
  revalidatePath('/ops');
  cookies().set('do_last_apify_run_id', runId, { httpOnly: true, sameSite: 'lax', path: '/', secure: process.env.NODE_ENV === 'production' });

  if ((res as any)?.ok === false) {
    const detail = String((res as any)?.detail || 'Apify import failed').slice(0, 160);
    redirect(`/ops?notice=${encodeURIComponent(`Apify import failed: ${detail}`)}`);
  }

  const sourceId = String((res as any)?.sourceId || '').trim();
  if (!sourceId) {
    redirect(`/ops?apifyRunId=${encodeURIComponent(runId)}&notice=${encodeURIComponent('Apify run imported but no sourceId returned')}`);
  }

  const sug = await post('/intelligence/suggestions/import-from-source', { workspaceId, sourceId, limit });
  revalidatePath('/ops');
  const imported = Number((sug as any)?.imported || 0);
  const skipped = Number((sug as any)?.skippedDuplicates || 0);
  redirect(`/ops?apifyRunId=${encodeURIComponent(runId)}&sourceId=${encodeURIComponent(sourceId)}&notice=${encodeURIComponent(`Imported source and ${imported} suggestions (${skipped} duplicates skipped)`)}`);
}

export async function importTrendSuggestionsAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const sourceId = String(formData.get('source_id') || '').trim();
  const limit = Number(formData.get('limit') || 100);
  if (!sourceId) return;

  const res = await post('/intelligence/suggestions/import-from-source', { workspaceId, sourceId, limit });
  revalidatePath('/ops');
  if ((res as any)?.ok === false) {
    const detail = String((res as any)?.detail || 'Import failed').slice(0, 160);
    redirect(`/ops?notice=${encodeURIComponent(`Import failed: ${detail}`)}`);
  }
  const imported = Number((res as any)?.imported || 0);
  const skipped = Number((res as any)?.skippedDuplicates || 0);
  redirect(`/ops?notice=${encodeURIComponent(`Imported ${imported} suggestions (${skipped} duplicates skipped)`)}`);
}

export async function feedbackTrendSuggestionAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const suggestionId = String(formData.get('suggestion_id') || '').trim();
  const eventType = String(formData.get('event_type') || '').trim();
  if (!suggestionId || !eventType) return;

  await post('/intelligence/feedback', { workspaceId, suggestionId, eventType });
  revalidatePath('/ops');
  redirect(`/ops?notice=${encodeURIComponent(`Suggestion ${eventType}`)}`);
}

export async function approveXDraftAction(formData: FormData) {
  const tweetId = String(formData.get('tweet_id') || '').trim();
  if (!tweetId) return;
  await post(`/integrations/x/drafts/${encodeURIComponent(tweetId)}/send`, { dryRun: true });
  revalidatePath('/ops');
}

export async function sendXDraftAction(formData: FormData) {
  const tweetId = String(formData.get('tweet_id') || '').trim();
  if (!tweetId) return;
  await post(`/integrations/x/drafts/${encodeURIComponent(tweetId)}/send`, { dryRun: false });
  revalidatePath('/ops');
}

export async function createInviteAction(formData: FormData) {
  const email = String(formData.get('email') || '').trim();
  const workspaceName = String(formData.get('workspace_name') || 'Beta Workspace').trim();
  const role = String(formData.get('role') || 'owner').trim().toLowerCase();
  const expiresInHours = Number(formData.get('expires_in_hours') || 168);
  const maxUses = Number(formData.get('max_uses') || 1);
  if (!email) return;

  const res = await post('/auth/invites', { email, workspaceName, role, expiresInHours, maxUses });
  revalidatePath('/ops');
  if (!res || (res as any).ok === false) {
    const status = String((res as any)?.status || 'unknown');
    const detail = encodeURIComponent(String((res as any)?.detail || 'invite_create_failed'));
    redirect(`/ops?invite=error:${status}:${detail}`);
  }
  redirect('/ops?invite=ok');
}

export async function connectPlatformAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const platform = String(formData.get('platform') || '').trim().toLowerCase();
  if (!platform) return;

  const res = await post('/integrations/accounts/connect', { workspaceId, platform });
  if (res?.authUrl) {
    redirect(res.authUrl);
  }
  revalidatePath('/studio');
}

export async function selectLinkedInOrgAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const orgUrn = String(formData.get('org_urn') || '').trim();
  if (!orgUrn) return;
  await post('/integrations/linkedin/orgs/select', { workspaceId, orgUrn });
  revalidatePath('/studio');
}

export async function disconnectPlatformAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const platform = String(formData.get('platform') || '').trim().toLowerCase();
  if (!platform) return;

  await post('/integrations/accounts/disconnect', { workspaceId, platform });
  revalidatePath('/studio');
}

export async function authorizePublisherAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const platform = String(formData.get('platform') || '').trim().toLowerCase();
  const userId = String(formData.get('user_id') || '').trim();
  if (!platform || !userId) return;

  await post('/integrations/accounts/authorize-publisher', { workspaceId, platform, userId });
  revalidatePath('/studio');
}

export async function saveModelPreferencesAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const mode = String(formData.get('mode') || 'auto').trim();
  const textModelId = String(formData.get('text_model_id') || '').trim();
  const imageModelId = String(formData.get('image_model_id') || '').trim();
  const videoModelId = String(formData.get('video_model_id') || '').trim();

  await post('/integrations/models/preferences', {
    workspaceId,
    mode,
    textModelId,
    imageModelId,
    videoModelId,
  });
  revalidatePath('/ops');
}

export async function createVoiceProfileAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const fullName = String(formData.get('full_name') || '').trim();
  const email = String(formData.get('email') || '').trim().toLowerCase();
  const displayName = String(formData.get('display_name') || 'Custom Voice').trim();
  const providerVoiceId = String(formData.get('provider_voice_id') || '').trim();
  if (!fullName || !email || !providerVoiceId) return;

  const rec = await post('/v1/consent/records', {
    workspaceId,
    subjectFullName: fullName,
    subjectEmail: email,
    consentType: 'voice',
    scope: { usage: 'voice_generation', provider: 'elevenlabs' },
  });
  if (!rec || !(rec as any).id) return;

  await post(`/v1/consent/records/${encodeURIComponent((rec as any).id)}/verify-identity`, {
    provider: 'manual',
    status: 'verified',
    score: 1.0,
    metadata: { source: 'ops-voice-profile-bootstrap' },
  });

  await post('/v1/consent/voice/profiles', {
    workspaceId,
    consentRecordId: (rec as any).id,
    provider: 'elevenlabs',
    providerVoiceId,
    displayName,
  });

  revalidatePath('/ops');
}

export async function createVoiceRenderAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const voiceProfileId = String(formData.get('voice_profile_id') || '').trim();
  const scriptText = String(formData.get('script_text') || '').trim();
  if (!voiceProfileId || !scriptText) return;

  await post('/v1/consent/voice/renders', { workspaceId, voiceProfileId, scriptText });
  revalidatePath('/ops');
}

export async function deleteVoiceProfileAction(formData: FormData) {
  const profileId = String(formData.get('voice_profile_id') || '').trim();
  if (!profileId) return;
  await post(`/v1/consent/voice/profiles/${encodeURIComponent(profileId)}/delete`);
  revalidatePath('/ops');
}

export async function approveVoiceRenderAction(formData: FormData) {
  const renderId = String(formData.get('render_id') || '').trim();
  if (!renderId) return;
  await post(`/v1/consent/voice/renders/${encodeURIComponent(renderId)}/approve`);
  revalidatePath('/ops');
}

export async function retryVoiceRenderAction(formData: FormData) {
  const renderId = String(formData.get('render_id') || '').trim();
  if (!renderId) return;
  await post(`/v1/consent/voice/renders/${encodeURIComponent(renderId)}/retry`);
  revalidatePath('/ops');
}

export async function createVideoRenderAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const voiceRenderId = String(formData.get('voice_render_id') || '').trim();
  const scriptText = String(formData.get('script_text') || '').trim();
  const backgroundTemplateId = String(formData.get('background_template_id') || '').trim();
  if (!voiceRenderId) return;
  const res = await post('/v1/consent/video/renders', { workspaceId, voiceRenderId, scriptText, backgroundTemplateId });
  revalidatePath('/ops');
  revalidatePath('/studio/review');
  if ((res as any)?.ok === false) {
    redirect(`/ops?video_error=${encodeURIComponent(String((res as any)?.detail || 'create_video_failed'))}`);
  }
  redirect('/ops?video_notice=video_job_created');
}

export async function approveVideoRenderAction(formData: FormData) {
  const renderId = String(formData.get('render_id') || '').trim();
  if (!renderId) return;
  await post(`/v1/consent/video/renders/${encodeURIComponent(renderId)}/approve`);
  revalidatePath('/ops');
}

export async function retryVideoRenderAction(formData: FormData) {
  const renderId = String(formData.get('render_id') || '').trim();
  if (!renderId) return;
  await post(`/v1/consent/video/renders/${encodeURIComponent(renderId)}/retry`);
  revalidatePath('/ops');
}

export async function refreshVideoRenderAction(formData: FormData) {
  const renderId = String(formData.get('render_id') || '').trim();
  if (!renderId) return;
  const res = await post(`/v1/consent/video/renders/${encodeURIComponent(renderId)}/refresh`);
  revalidatePath('/ops');
  if ((res as any)?.ok === false) {
    redirect(`/ops?video_error=${encodeURIComponent(String((res as any)?.detail || 'refresh_failed'))}`);
  }
  redirect('/ops?video_notice=video_status_refreshed');
}

export async function refreshQueuedVideoRendersAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const res = await post(`/v1/consent/video/renders/refresh-queued?workspaceId=${encodeURIComponent(workspaceId)}&limit=50`);
  revalidatePath('/ops');
  if ((res as any)?.ok === false) {
    redirect(`/ops?video_error=${encodeURIComponent(String((res as any)?.detail || 'refresh_queued_failed'))}`);
  }
  redirect('/ops?video_notice=queued_jobs_refreshed');
}

export async function createAvatarVideoQuickAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();
  const scriptText = String(formData.get('script_text') || '').trim();
  const backgroundTemplateId = String(formData.get('background_template_id') || '').trim();
  if (!scriptText) {
    redirect('/studio/avatar-video?error=script_required');
  }

  const vrRes = await fetch(`${API_BASE}/v1/consent/voice/renders?workspaceId=${encodeURIComponent(workspaceId)}&limit=25&status=approved`, {
    method: 'GET',
    headers: { ...actorHeaders() },
    cache: 'no-store',
  });
  if (!vrRes.ok) {
    redirect(`/studio/avatar-video?error=${encodeURIComponent(`voice_render_lookup_${vrRes.status}`)}`);
  }
  const vrData = await vrRes.json().catch(() => ({}));
  const approved = Array.isArray(vrData?.items) ? vrData.items : [];
  const voiceRenderId = String(approved?.[0]?.id || '').trim();
  if (!voiceRenderId) {
    redirect('/studio/avatar-video?error=no_approved_voice_render');
  }

  const create = await post('/v1/consent/video/renders', { workspaceId, voiceRenderId, scriptText, backgroundTemplateId });
  if ((create as any)?.ok === false) {
    redirect(`/studio/avatar-video?error=${encodeURIComponent(String((create as any)?.detail || 'video_create_failed'))}`);
  }

  const renderId = String((create as any)?.id || '');
  revalidatePath('/ops');
  revalidatePath('/studio/review');
  redirect(`/studio/avatar-video?notice=${encodeURIComponent(renderId ? `video_job_created:${renderId}` : 'video_job_created')}`);
}

export async function bootstrapSampleVoiceRenderAction(formData: FormData) {
  const workspaceId = String(formData.get('workspace_id') || DEFAULT_WORKSPACE).trim();

  const vpRes = await fetch(`${API_BASE}/v1/consent/voice/profiles?workspaceId=${encodeURIComponent(workspaceId)}&limit=20&status=active`, {
    method: 'GET',
    headers: { ...actorHeaders() },
    cache: 'no-store',
  });
  if (!vpRes.ok) {
    redirect(`/studio/avatar-video?error=${encodeURIComponent(`voice_profile_lookup_${vpRes.status}`)}`);
  }
  const vpData = await vpRes.json().catch(() => ({}));
  const profiles = Array.isArray(vpData?.items) ? vpData.items : [];
  const voiceProfileId = String(profiles?.[0]?.id || '').trim();
  if (!voiceProfileId) {
    redirect('/studio/avatar-video?error=no_active_voice_profile');
  }

  const sampleScript = 'Quick voice bootstrap for avatar video generation. This verifies your voice pipeline end to end.';
  const render = await post('/v1/consent/voice/renders', { workspaceId, voiceProfileId, scriptText: sampleScript });
  if ((render as any)?.ok === false) {
    redirect(`/studio/avatar-video?error=${encodeURIComponent(String((render as any)?.detail || 'voice_render_bootstrap_failed'))}`);
  }

  const renderId = String((render as any)?.id || '').trim();
  if (!renderId) {
    redirect('/studio/avatar-video?error=voice_render_bootstrap_no_id');
  }

  const approve = await post(`/v1/consent/voice/renders/${encodeURIComponent(renderId)}/approve`);
  if ((approve as any)?.ok === false) {
    redirect(`/studio/avatar-video?error=${encodeURIComponent(String((approve as any)?.detail || 'voice_render_bootstrap_approve_failed'))}`);
  }

  revalidatePath('/ops');
  redirect(`/studio/avatar-video?notice=${encodeURIComponent(`voice_bootstrap_ready:${renderId}`)}`);
}

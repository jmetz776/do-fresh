export type UUID = string;

export type SourceType = 'csv' | 'url';
export type SourceStatus = 'pending' | 'normalized' | 'failed';
export type ContentStatus = 'draft' | 'approved' | 'scheduled' | 'published' | 'failed';
export type ScheduleStatus = 'scheduled' | 'processing' | 'published' | 'failed' | 'canceled';
export type JobStatus = 'queued' | 'processing' | 'succeeded' | 'failed';

export interface Source {
  id: UUID;
  workspaceId: UUID;
  type: SourceType;
  rawPayload: string;
  status: SourceStatus;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface SourceItem {
  id: UUID;
  sourceId: UUID;
  externalRef?: string | null;
  title?: string | null;
  body?: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
}

export interface ContentItem {
  id: UUID;
  workspaceId: UUID;
  sourceItemId?: UUID | null;
  channel: string;
  title?: string | null;
  hook?: string | null;
  caption: string;
  variantNo: number;
  status: ContentStatus;
  providerPostId?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Schedule {
  id: UUID;
  contentItemId: UUID;
  publishAt: string;
  timezone: string;
  status: ScheduleStatus;
  createdAt: string;
  updatedAt: string;
}

export interface PublishJob {
  id: UUID;
  scheduleId: UUID;
  attempt: number;
  idempotencyKey: string;
  status: JobStatus;
  providerResponse?: Record<string, unknown> | null;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateSourceRequest {
  workspaceId: UUID;
  type: SourceType;
  rawPayload: string;
}

export interface CreateSourceResponse {
  id: UUID;
  status: SourceStatus;
}

export interface NormalizeSourceResponse {
  sourceId: UUID;
  status: SourceStatus;
  itemsCreated: number;
}

export interface GenerateContentRequest {
  workspaceId: UUID;
  sourceItemId: UUID;
  channels: string[];
  variantCount: number;
}

export interface ScheduleContentRequest {
  contentItemId: UUID;
  publishAt: string;
  timezone?: string;
}

export interface PublishRunResponse {
  processed: number;
  succeeded: number;
  failed: number;
}

export interface DashboardResponse {
  draft: number;
  approved: number;
  scheduled: number;
  published: number;
  failed: number;
  recentPublishes: Array<{
    contentItemId: UUID;
    channel: string;
    publishedAt: string;
    providerPostId?: string | null;
  }>;
}

export function buildIdempotencyKey(input: {
  channel: string;
  contentItemId: UUID;
  publishAt: string;
}): string {
  return `${input.channel}:${input.contentItemId}:${input.publishAt}`;
}

import {
  COLLECTION_RUN_ADMIN_ENDPOINTS,
  COLLECTION_RUN_ADMIN_PATH,
  type CollectionRunListQuery,
  type CollectionRunStatus,
  type CollectionRunTriggerType,
  type CollectionRunType,
} from '../types/collectionRun.js';

export const ADMIN_SESSION_PATH = '/api/v1/admin/session';
export const COLLECTION_RUNS_PATH = COLLECTION_RUN_ADMIN_PATH;
export const COLLECTION_RUN_TRIGGER_PATH =
  COLLECTION_RUN_ADMIN_ENDPOINTS.trigger.path;

const COLLECTION_RUN_STATUSES = new Set<CollectionRunStatus>([
  'running',
  'succeeded',
  'partial_failure',
  'failed',
]);

const COLLECTION_RUN_TYPES = new Set<CollectionRunType>([
  'seed_import',
  'runtime_import',
  'collection',
]);

const COLLECTION_RUN_TRIGGER_TYPES = new Set<CollectionRunTriggerType>([
  'cli',
  'scheduler',
  'admin',
]);

export interface ResolvedCollectionRunListQuery {
  page: number;
  size: number;
  source_id?: string;
  status?: CollectionRunStatus;
  run_type?: CollectionRunType;
  trigger_type?: CollectionRunTriggerType;
  start_date?: string;
  end_date?: string;
}

export interface AdminApiRequestOptions {
  /** Bearer access token from `createAdminSession` (FE3-01 will persist in memory). */
  accessToken?: string;
}

export function buildAdminAuthorizationHeader(
  accessToken: string | undefined,
): Record<string, string> {
  const trimmed = accessToken?.trim();
  if (!trimmed) {
    return {};
  }

  return {
    Authorization: `Bearer ${trimmed}`,
  };
}

export function buildCollectionRunDetailPath(runId: string): string {
  const trimmed = runId.trim();
  if (trimmed.length === 0) {
    throw new Error('Collection run id must not be empty.');
  }

  return `${COLLECTION_RUN_ADMIN_ENDPOINTS.detail.pathPrefix}${encodeURIComponent(trimmed)}`;
}

export function resolveCollectionRunListQuery(
  query: CollectionRunListQuery = {},
): ResolvedCollectionRunListQuery {
  const page = query.page ?? 1;
  const size = query.size ?? 20;

  if (!Number.isSafeInteger(page) || page < 1) {
    throw new Error('Collection run list page must be an integer greater than 0.');
  }

  if (!Number.isSafeInteger(size) || size < 1 || size > 100) {
    throw new Error('Collection run list size must be an integer from 1 to 100.');
  }

  if (query.status !== undefined && !COLLECTION_RUN_STATUSES.has(query.status)) {
    throw new Error('Collection run list status filter is invalid.');
  }

  if (query.run_type !== undefined && !COLLECTION_RUN_TYPES.has(query.run_type)) {
    throw new Error('Collection run list run_type filter is invalid.');
  }

  if (
    query.trigger_type !== undefined &&
    !COLLECTION_RUN_TRIGGER_TYPES.has(query.trigger_type)
  ) {
    throw new Error('Collection run list trigger_type filter is invalid.');
  }

  if (
    query.source_id !== undefined &&
    (query.source_id.length < 1 || query.source_id.length > 200)
  ) {
    throw new Error('Collection run source_id filter must contain 1 to 200 characters.');
  }

  return {
    page,
    size,
    ...(query.source_id ? { source_id: query.source_id } : {}),
    ...(query.status ? { status: query.status } : {}),
    ...(query.run_type ? { run_type: query.run_type } : {}),
    ...(query.trigger_type ? { trigger_type: query.trigger_type } : {}),
    ...(query.start_date ? { start_date: query.start_date } : {}),
    ...(query.end_date ? { end_date: query.end_date } : {}),
  };
}

/** Admin frontend routes (client router — not API paths). */
export const ADMIN_APP_ROUTES = {
  login: '/admin/login',
  dashboard: '/admin',
  collectors: '/admin/collectors',
  runs: '/admin/runs',
  runDetail: (runId: string) => `/admin/runs/${encodeURIComponent(runId.trim())}`,
  quality: '/admin/quality',
} as const;

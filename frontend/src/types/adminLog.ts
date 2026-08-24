/** Backend Admin Logs OpenAPI consumer contract. */

export const ADMIN_LOG_BASE_PATH = '/api/v1/admin/logs';
export const ADMIN_LOG_FILES_PATH = `${ADMIN_LOG_BASE_PATH}/files`;
export const ADMIN_LOG_EVENTS_PATH = `${ADMIN_LOG_BASE_PATH}/events`;
export const ADMIN_LOG_ROTATE_CURRENT_PATH = `${ADMIN_LOG_BASE_PATH}/rotate-current`;

export const ADMIN_LOG_ENDPOINTS = {
  fileList: { method: 'GET' as const, path: ADMIN_LOG_FILES_PATH },
  eventList: { method: 'GET' as const, path: ADMIN_LOG_EVENTS_PATH },
  archiveDelete: {
    method: 'DELETE' as const,
    pathPrefix: `${ADMIN_LOG_BASE_PATH}/archives/`,
  },
  rotateCurrent: {
    method: 'POST' as const,
    path: ADMIN_LOG_ROTATE_CURRENT_PATH,
  },
} as const;

export const ADMIN_LOG_LEVELS = [
  'DEBUG',
  'INFO',
  'WARNING',
  'ERROR',
  'CRITICAL',
] as const;

export type AdminLogLevel = (typeof ADMIN_LOG_LEVELS)[number];

export interface AdminLogFileListItemDto {
  file_id: string;
  filename: string;
  size_bytes: number;
  is_active: boolean;
  modified_at: string;
}

export interface AdminLogFileListResponse {
  files: AdminLogFileListItemDto[];
}

export interface AdminLogEventListItemDto {
  timestamp: string;
  level: AdminLogLevel;
  component: string;
  event: string;
  request_id: string | null;
  collection_run_id: string | null;
  source_id: string | null;
  duration_ms: number | null;
  error_type: string | null;
}

export interface AdminLogEventListQuery {
  file_id?: string;
  page?: number;
  limit?: number;
  level?: AdminLogLevel;
  component?: string;
  q?: string;
}

export interface AdminLogEventListResponse {
  total: number;
  page: number;
  limit: number;
  events: AdminLogEventListItemDto[];
}

export interface AdminLogDeleteResultDto {
  file_id: string;
  deleted: boolean;
  audit_id: string;
  message: string;
}

export interface AdminLogRotateResultDto {
  rotated_file_id: string;
  deleted_archive_file_id: string;
  audit_id: string;
  message: string;
}

export interface AdminObservabilityErrorBody {
  detail: string;
}

export const ADMIN_LOG_LIST_LIMITS = {
  min: 1,
  max: 100,
  default: 20,
} as const;

export interface ResolvedAdminLogEventListQuery {
  file_id: string;
  page: number;
  limit: number;
  level?: AdminLogLevel;
  component?: string;
  q?: string;
}

const LOG_LEVELS = new Set<AdminLogLevel>(ADMIN_LOG_LEVELS);

export function buildAdminLogArchiveDeletePath(fileId: string): string {
  const trimmed = fileId.trim();
  if (trimmed.length === 0) {
    throw new Error('Admin log file id must not be empty.');
  }
  return `${ADMIN_LOG_ENDPOINTS.archiveDelete.pathPrefix}${encodeURIComponent(trimmed)}`;
}

export function getAdminLogEventKey(event: AdminLogEventListItemDto): string {
  return [
    event.timestamp,
    event.component,
    event.request_id ?? '',
    event.collection_run_id ?? '',
    event.source_id ?? '',
    event.event,
  ].join('|');
}

export function resolveAdminLogEventListQuery(
  query: AdminLogEventListQuery = {},
): ResolvedAdminLogEventListQuery {
  const page = query.page ?? 1;
  const limit = query.limit ?? ADMIN_LOG_LIST_LIMITS.default;
  const file_id = query.file_id?.trim() || 'app.log';

  if (!Number.isSafeInteger(page) || page < 1) {
    throw new Error('Admin log event page must be an integer greater than 0.');
  }
  if (
    !Number.isSafeInteger(limit) ||
    limit < ADMIN_LOG_LIST_LIMITS.min ||
    limit > ADMIN_LOG_LIST_LIMITS.max
  ) {
    throw new Error('Admin log event limit must be an integer from 1 to 100.');
  }
  if (query.level !== undefined && !LOG_LEVELS.has(query.level)) {
    throw new Error('Admin log event level filter is invalid.');
  }
  const component = query.component?.trim();
  const q = query.q?.trim();

  if (q !== undefined && (q.length < 1 || q.length > 200)) {
    throw new Error('Admin log event query must contain 1 to 200 characters.');
  }
  if (component !== undefined && component.length > 100) {
    throw new Error('Admin log event component must contain at most 100 characters.');
  }

  return {
    file_id,
    page,
    limit,
    ...(query.level ? { level: query.level } : {}),
    ...(component ? { component } : {}),
    ...(q ? { q } : {}),
  };
}

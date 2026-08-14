/**
 * Admin structured file log API contract (Frontend 08 / FE8-00).
 *
 * W4-G0 proposal aligned with Integration 09 AO2·AO3.
 * Safe fields only — no stack trace, credentials, SQL parameters, or server paths.
 *
 * @see docs/development/develop_plan/integration/09_admin_data_log_console.md
 */

export const ADMIN_LOG_FILES_PATH = '/api/v1/admin/log-files';
export const ADMIN_LOG_ROTATE_CURRENT_PATH = '/api/v1/admin/log-files/rotate-current';

export const ADMIN_LOG_ENDPOINTS = {
  fileList: {
    method: 'GET' as const,
    path: ADMIN_LOG_FILES_PATH,
  },
  fileDetail: {
    method: 'GET' as const,
    pathPrefix: `${ADMIN_LOG_FILES_PATH}/`,
  },
  eventList: {
    method: 'GET' as const,
    pathSuffix: '/events',
  },
  archiveDelete: {
    method: 'DELETE' as const,
    pathPrefix: `${ADMIN_LOG_FILES_PATH}/`,
  },
  rotateCurrent: {
    method: 'POST' as const,
    path: ADMIN_LOG_ROTATE_CURRENT_PATH,
  },
} as const;

export type AdminLogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';

export type AdminLogFileStatus = 'active' | 'archive';

export interface AdminLogFileListItemDto {
  /** Server-issued opaque id; not a filesystem path. */
  file_id: string;
  /** Basename only (no directory segments). */
  filename: string;
  status: AdminLogFileStatus;
  size_bytes: number;
  created_at: string;
  rotated_at: string | null;
}

export interface AdminLogFileListQuery {
  page?: number;
  size?: number;
  status?: AdminLogFileStatus;
}

export interface AdminLogFileListResponse {
  items: AdminLogFileListItemDto[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AdminLogEventListItemDto {
  event_id: string;
  file_id: string;
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

export interface AdminLogEventDetailDto extends AdminLogEventListItemDto {
  message: string | null;
}

export interface AdminLogEventListQuery {
  page?: number;
  size?: number;
  file_id?: string;
  level?: AdminLogLevel;
  component?: string;
  collection_run_id?: string;
  request_id?: string;
  source_id?: string;
  start_time?: string;
  end_time?: string;
  search?: string;
}

export interface AdminLogEventListResponse {
  items: AdminLogEventListItemDto[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AdminLogDeleteResultDto {
  file_id: string;
  deleted: boolean;
  message: string;
}

export interface AdminLogRotateResultDto {
  rotated_file_id: string;
  previous_active_file_id: string;
  deleted_archive_file_id: string | null;
  message: string;
}

/** Protected admin observability routes use FastAPI `detail` errors. */
export interface AdminObservabilityErrorBody {
  detail: string;
}

export const ADMIN_LOG_LEVELS: readonly AdminLogLevel[] = [
  'DEBUG',
  'INFO',
  'WARNING',
  'ERROR',
] as const;

export const ADMIN_LOG_LIST_SIZE_LIMITS = {
  min: 1,
  max: 100,
  default: 20,
} as const;

export interface ResolvedAdminLogFileListQuery {
  page: number;
  size: number;
  status?: AdminLogFileStatus;
}

export interface ResolvedAdminLogEventListQuery {
  page: number;
  size: number;
  file_id?: string;
  level?: AdminLogLevel;
  component?: string;
  collection_run_id?: string;
  request_id?: string;
  source_id?: string;
  start_time?: string;
  end_time?: string;
  search?: string;
}

const LOG_LEVELS = new Set<AdminLogLevel>(ADMIN_LOG_LEVELS);
const LOG_FILE_STATUSES = new Set<AdminLogFileStatus>(['active', 'archive']);

export function buildAdminLogFileDetailPath(fileId: string): string {
  const trimmed = fileId.trim();
  if (trimmed.length === 0) {
    throw new Error('Admin log file id must not be empty.');
  }

  return `${ADMIN_LOG_ENDPOINTS.fileDetail.pathPrefix}${encodeURIComponent(trimmed)}`;
}

export function buildAdminLogEventListPath(fileId: string): string {
  return `${buildAdminLogFileDetailPath(fileId)}${ADMIN_LOG_ENDPOINTS.eventList.pathSuffix}`;
}

export function buildAdminLogArchiveDeletePath(fileId: string): string {
  return buildAdminLogFileDetailPath(fileId);
}

export function resolveAdminLogFileListQuery(
  query: AdminLogFileListQuery = {},
): ResolvedAdminLogFileListQuery {
  const page = query.page ?? 1;
  const size = query.size ?? ADMIN_LOG_LIST_SIZE_LIMITS.default;

  if (!Number.isSafeInteger(page) || page < 1) {
    throw new Error('Admin log file list page must be an integer greater than 0.');
  }

  if (
    !Number.isSafeInteger(size) ||
    size < ADMIN_LOG_LIST_SIZE_LIMITS.min ||
    size > ADMIN_LOG_LIST_SIZE_LIMITS.max
  ) {
    throw new Error(
      `Admin log file list size must be an integer from ${ADMIN_LOG_LIST_SIZE_LIMITS.min} to ${ADMIN_LOG_LIST_SIZE_LIMITS.max}.`,
    );
  }

  if (query.status !== undefined && !LOG_FILE_STATUSES.has(query.status)) {
    throw new Error('Admin log file list status filter is invalid.');
  }

  return {
    page,
    size,
    ...(query.status ? { status: query.status } : {}),
  };
}

export function resolveAdminLogEventListQuery(
  query: AdminLogEventListQuery = {},
): ResolvedAdminLogEventListQuery {
  const page = query.page ?? 1;
  const size = query.size ?? ADMIN_LOG_LIST_SIZE_LIMITS.default;

  if (!Number.isSafeInteger(page) || page < 1) {
    throw new Error('Admin log event list page must be an integer greater than 0.');
  }

  if (
    !Number.isSafeInteger(size) ||
    size < ADMIN_LOG_LIST_SIZE_LIMITS.min ||
    size > ADMIN_LOG_LIST_SIZE_LIMITS.max
  ) {
    throw new Error(
      `Admin log event list size must be an integer from ${ADMIN_LOG_LIST_SIZE_LIMITS.min} to ${ADMIN_LOG_LIST_SIZE_LIMITS.max}.`,
    );
  }

  if (query.level !== undefined && !LOG_LEVELS.has(query.level)) {
    throw new Error('Admin log event list level filter is invalid.');
  }

  if (
    query.search !== undefined &&
    (query.search.length < 1 || query.search.length > 200)
  ) {
    throw new Error('Admin log event search must contain 1 to 200 characters.');
  }

  return {
    page,
    size,
    ...(query.file_id ? { file_id: query.file_id } : {}),
    ...(query.level ? { level: query.level } : {}),
    ...(query.component ? { component: query.component } : {}),
    ...(query.collection_run_id ? { collection_run_id: query.collection_run_id } : {}),
    ...(query.request_id ? { request_id: query.request_id } : {}),
    ...(query.source_id ? { source_id: query.source_id } : {}),
    ...(query.start_time ? { start_time: query.start_time } : {}),
    ...(query.end_time ? { end_time: query.end_time } : {}),
    ...(query.search ? { search: query.search } : {}),
  };
}

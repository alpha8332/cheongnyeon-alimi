import type { PolicyDto } from '../types/policy.js';
import type {
  AdminPolicyDetailDto,
  AdminPolicyListResponse,
  ResolvedAdminPolicyListQuery,
} from '../types/adminPolicyData.js';
import { toAdminPolicyListItem } from '../types/adminPolicyData.js';
import type {
  AdminLogDeleteResultDto,
  AdminLogEventListItemDto,
  AdminLogEventListResponse,
  AdminLogFileListResponse,
  AdminLogRotateResultDto,
  AdminObservabilityErrorBody,
  ResolvedAdminLogEventListQuery,
} from '../types/adminLog.js';
import {
  findMockAdminLogFileById,
  MOCK_ACTIVE_LOG_FILE_ID,
  MOCK_ADMIN_LOG_EVENTS,
  MOCK_ADMIN_LOG_FILES,
  MOCK_ARCHIVE_DELETE_409_FILE_ID,
} from './adminObservabilityFixtures.js';

function comparePolicyField(
  left: PolicyDto,
  right: PolicyDto,
  field: ResolvedAdminPolicyListQuery['sort_by'],
): number {
  switch (field) {
    case 'id':
      return left.id - right.id;
    case 'created_at':
      return left.created_at.localeCompare(right.created_at);
    case 'title':
      return left.title.localeCompare(right.title, 'ko');
    case 'collected_at':
      return left.collected_at.localeCompare(right.collected_at);
    case 'updated_at':
      return left.updated_at.localeCompare(right.updated_at);
    default:
      return 0;
  }
}

function matchesAdminPolicyQuery(
  policy: PolicyDto,
  query: ResolvedAdminPolicyListQuery,
): boolean {
  const regionMatches =
    query.region === undefined ||
    policy.regions.length === 0 ||
    policy.regions.includes('전국') ||
    policy.regions.includes(query.region);

  return (
    (query.source_id === undefined || policy.source_id === query.source_id) &&
    (query.category === undefined || policy.categories.includes(query.category)) &&
    regionMatches &&
    (query.status === undefined || policy.application_status === query.status) &&
    (query.data_quality_status === undefined ||
      policy.data_quality_status === query.data_quality_status)
  );
}

function paginate<T>(items: readonly T[], page: number, limit: number): T[] {
  const start = (page - 1) * limit;
  return items.slice(start, start + limit);
}

export function createMockAdminPolicyListResponse(
  policies: readonly PolicyDto[],
  query: ResolvedAdminPolicyListQuery,
): AdminPolicyListResponse {
  const filtered = [...policies]
    .filter((policy) => matchesAdminPolicyQuery(policy, query))
    .sort((left, right) => {
      const direction = query.order === 'asc' ? 1 : -1;
      return direction * comparePolicyField(left, right, query.sort_by);
    });

  return {
    items: paginate(filtered, query.page, query.limit).map(toAdminPolicyListItem),
    page: query.page,
    limit: query.limit,
    total: filtered.length,
  };
}

export type AdminPolicyDetailMockResult =
  | { status: 200; body: AdminPolicyDetailDto }
  | { status: 404; body: AdminObservabilityErrorBody };

export function handleAdminPolicyListMock(
  policies: readonly PolicyDto[],
  query: ResolvedAdminPolicyListQuery,
): AdminPolicyListResponse {
  return createMockAdminPolicyListResponse(policies, query);
}

export function handleAdminPolicyDetailMock(
  policies: readonly PolicyDto[],
  policyId: number,
): AdminPolicyDetailMockResult {
  const policy = policies.find((candidate) => candidate.id === policyId);
  if (policy === undefined) {
    return { status: 404, body: { detail: 'Policy not found.' } };
  }

  const {
    schema_version,
    application_period_text,
    application_schedule,
    ...detail
  } = policy;
  void schema_version;
  void application_period_text;
  void application_schedule;
  return { status: 200, body: detail };
}

export function handleAdminLogFileListMock(): AdminLogFileListResponse {
  return { files: [...MOCK_ADMIN_LOG_FILES] };
}

function matchesLogEventQuery(
  event: (typeof MOCK_ADMIN_LOG_EVENTS)[number],
  query: ResolvedAdminLogEventListQuery,
): boolean {
  if (event.file_id !== query.file_id) return false;
  if (query.level !== undefined && event.level !== query.level) return false;
  if (query.component !== undefined && event.component !== query.component) return false;
  if (query.q !== undefined) {
    const haystack = event.event.toLowerCase();
    if (!haystack.includes(query.q.toLowerCase())) return false;
  }
  return true;
}

function toPublicLogEvent(
  event: (typeof MOCK_ADMIN_LOG_EVENTS)[number],
): AdminLogEventListItemDto {
  return {
    timestamp: event.timestamp,
    level: event.level,
    component: event.component,
    event: event.event,
    request_id: event.request_id,
    collection_run_id: event.collection_run_id,
    source_id: event.source_id,
    duration_ms: event.duration_ms,
    error_type: event.error_type,
  };
}

export function handleAdminLogEventListMock(
  query: ResolvedAdminLogEventListQuery,
): AdminLogEventListResponse {
  const filtered = [...MOCK_ADMIN_LOG_EVENTS]
    .filter((event) => matchesLogEventQuery(event, query))
    .sort((left, right) => right.timestamp.localeCompare(left.timestamp));

  return {
    events: paginate(filtered, query.page, query.limit).map(toPublicLogEvent),
    page: query.page,
    limit: query.limit,
    total: filtered.length,
  };
}

export type AdminLogArchiveDeleteMockResult =
  | { status: 200; body: AdminLogDeleteResultDto }
  | { status: 400 | 404 | 409; body: AdminObservabilityErrorBody };

export function handleAdminLogArchiveDeleteMock(
  fileId: string,
): AdminLogArchiveDeleteMockResult {
  const file = findMockAdminLogFileById(fileId);
  if (file === undefined) {
    return { status: 404, body: { detail: 'Log file not found.' } };
  }
  if (file.is_active) {
    return {
      status: 400,
      body: { detail: "Active log file 'app.log' cannot be directly deleted" },
    };
  }
  if (fileId === MOCK_ARCHIVE_DELETE_409_FILE_ID) {
    return {
      status: 409,
      body: { detail: 'Archive delete conflict for admin observability audit test.' },
    };
  }
  return {
    status: 200,
    body: {
      file_id: file.file_id,
      deleted: true,
      audit_id: 'audit-mock-delete',
      message: `Log archive file '${file.file_id}' deleted successfully.`,
    },
  };
}

export function handleAdminLogRotateCurrentMock(): AdminLogRotateResultDto {
  return {
    rotated_file_id: MOCK_ACTIVE_LOG_FILE_ID,
    deleted_archive_file_id: 'app.log.rotated-mock',
    audit_id: 'audit-mock-rotate',
    message: 'Current log rotated and its generated archive deleted successfully.',
  };
}

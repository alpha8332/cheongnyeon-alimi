import type { PolicyDto } from '../types/policy.js';
import type {
  AdminPolicyDetailDto,
  AdminPolicyListResponse,
  ResolvedAdminPolicyListQuery,
} from '../types/adminPolicyData.js';
import {
  toAdminPolicyListItem,
} from '../types/adminPolicyData.js';
import type {
  AdminLogDeleteResultDto,
  AdminLogEventDetailDto,
  AdminLogEventListResponse,
  AdminLogFileListItemDto,
  AdminLogFileListResponse,
  AdminLogRotateResultDto,
  AdminObservabilityErrorBody,
  ResolvedAdminLogEventListQuery,
  ResolvedAdminLogFileListQuery,
} from '../types/adminLog.js';
import {
  findMockAdminLogEventById,
  findMockAdminLogFileById,
  MOCK_ACTIVE_LOG_FILE_ID,
  MOCK_ADMIN_LOG_EVENTS,
  MOCK_ADMIN_LOG_FILES,
  MOCK_ARCHIVE_LOG_FILE_ID,
} from './adminObservabilityFixtures.js';

function comparePolicyField(
  left: PolicyDto,
  right: PolicyDto,
  field: ResolvedAdminPolicyListQuery['sort_by'],
): number {
  switch (field) {
    case 'id':
      return left.id - right.id;
    case 'title':
      return left.title.localeCompare(right.title, 'ko');
    case 'collected_at':
      return left.collected_at.localeCompare(right.collected_at);
    case 'updated_at':
      return left.updated_at.localeCompare(right.updated_at);
    case 'application_start': {
      const leftValue = left.application_start ?? '';
      const rightValue = right.application_start ?? '';
      return leftValue.localeCompare(rightValue);
    }
    case 'application_end': {
      const leftValue = left.application_end ?? '';
      const rightValue = right.application_end ?? '';
      return leftValue.localeCompare(rightValue);
    }
    default:
      return 0;
  }
}

function matchesAdminPolicyQuery(
  policy: PolicyDto,
  query: ResolvedAdminPolicyListQuery,
): boolean {
  if (query.source_id !== undefined && policy.source_id !== query.source_id) {
    return false;
  }

  if (query.category !== undefined && !policy.categories.includes(query.category)) {
    return false;
  }

  if (query.region !== undefined && !policy.regions.includes(query.region)) {
    return false;
  }

  if (query.status !== undefined && policy.application_status !== query.status) {
    return false;
  }

  if (
    query.data_quality_status !== undefined &&
    policy.data_quality_status !== query.data_quality_status
  ) {
    return false;
  }

  return true;
}

function paginate<T>(
  items: readonly T[],
  page: number,
  size: number,
): { pageItems: T[]; pages: number } {
  const start = (page - 1) * size;
  const pageItems = items.slice(start, start + size);
  const pages = Math.max(1, Math.ceil(items.length / size));

  return { pageItems, pages };
}

export function createMockAdminPolicyListResponse(
  policies: readonly PolicyDto[],
  query: ResolvedAdminPolicyListQuery,
): AdminPolicyListResponse {
  const filtered = [...policies]
    .filter((policy) => matchesAdminPolicyQuery(policy, query))
    .sort((left, right) => {
      const direction = query.sort_order === 'asc' ? 1 : -1;
      return direction * comparePolicyField(left, right, query.sort_by);
    });

  const { pageItems, pages } = paginate(filtered, query.page, query.size);

  return {
    items: pageItems.map(toAdminPolicyListItem),
    page: query.page,
    size: query.size,
    total: filtered.length,
    pages,
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
    return {
      status: 404,
      body: { detail: 'Policy not found.' },
    };
  }

  return {
    status: 200,
    body: policy,
  };
}

function matchesLogFileQuery(
  file: AdminLogFileListItemDto,
  query: ResolvedAdminLogFileListQuery,
): boolean {
  return query.status === undefined || file.status === query.status;
}

export function handleAdminLogFileListMock(
  query: ResolvedAdminLogFileListQuery,
): AdminLogFileListResponse {
  const filtered = MOCK_ADMIN_LOG_FILES.filter((file) =>
    matchesLogFileQuery(file, query),
  );
  const { pageItems, pages } = paginate(filtered, query.page, query.size);

  return {
    items: pageItems,
    page: query.page,
    size: query.size,
    total: filtered.length,
    pages,
  };
}

export type AdminLogFileDetailMockResult =
  | { status: 200; body: AdminLogFileListItemDto }
  | { status: 404; body: AdminObservabilityErrorBody };

export function handleAdminLogFileDetailMock(
  fileId: string,
): AdminLogFileDetailMockResult {
  const file = findMockAdminLogFileById(fileId);

  if (file === undefined) {
    return {
      status: 404,
      body: { detail: 'Log file not found.' },
    };
  }

  return {
    status: 200,
    body: file,
  };
}

function matchesLogEventQuery(
  event: AdminLogEventDetailDto,
  query: ResolvedAdminLogEventListQuery,
): boolean {
  if (query.file_id !== undefined && event.file_id !== query.file_id) {
    return false;
  }

  if (query.level !== undefined && event.level !== query.level) {
    return false;
  }

  if (query.component !== undefined && event.component !== query.component) {
    return false;
  }

  if (
    query.collection_run_id !== undefined &&
    event.collection_run_id !== query.collection_run_id
  ) {
    return false;
  }

  if (query.request_id !== undefined && event.request_id !== query.request_id) {
    return false;
  }

  if (query.source_id !== undefined && event.source_id !== query.source_id) {
    return false;
  }

  if (query.start_time !== undefined && event.timestamp < query.start_time) {
    return false;
  }

  if (query.end_time !== undefined && event.timestamp > query.end_time) {
    return false;
  }

  if (query.search !== undefined) {
    const haystack = [
      event.event,
      event.component,
      event.message ?? '',
      event.error_type ?? '',
    ]
      .join(' ')
      .toLowerCase();

    if (!haystack.includes(query.search.toLowerCase())) {
      return false;
    }
  }

  return true;
}

export function handleAdminLogEventListMock(
  query: ResolvedAdminLogEventListQuery,
): AdminLogEventListResponse {
  const filtered = [...MOCK_ADMIN_LOG_EVENTS]
    .filter((event) => matchesLogEventQuery(event, query))
    .sort((left, right) => right.timestamp.localeCompare(left.timestamp));

  const { pageItems, pages } = paginate(filtered, query.page, query.size);

  return {
    items: pageItems.map((event) => ({
      event_id: event.event_id,
      file_id: event.file_id,
      timestamp: event.timestamp,
      level: event.level,
      component: event.component,
      event: event.event,
      request_id: event.request_id,
      collection_run_id: event.collection_run_id,
      source_id: event.source_id,
      duration_ms: event.duration_ms,
      error_type: event.error_type,
    })),
    page: query.page,
    size: query.size,
    total: filtered.length,
    pages,
  };
}

export type AdminLogEventDetailMockResult =
  | { status: 200; body: AdminLogEventDetailDto }
  | { status: 404; body: AdminObservabilityErrorBody };

export function handleAdminLogEventDetailMock(
  eventId: string,
): AdminLogEventDetailMockResult {
  const event = findMockAdminLogEventById(eventId);

  if (event === undefined) {
    return {
      status: 404,
      body: { detail: 'Log event not found.' },
    };
  }

  return {
    status: 200,
    body: event,
  };
}

export type AdminLogArchiveDeleteMockResult =
  | { status: 200; body: AdminLogDeleteResultDto }
  | { status: 404; body: AdminObservabilityErrorBody }
  | { status: 409; body: AdminObservabilityErrorBody };

export function handleAdminLogArchiveDeleteMock(
  fileId: string,
): AdminLogArchiveDeleteMockResult {
  const file = findMockAdminLogFileById(fileId);

  if (file === undefined) {
    return {
      status: 404,
      body: { detail: 'Log file not found.' },
    };
  }

  if (file.status === 'active') {
    return {
      status: 409,
      body: {
        detail: 'Active log file cannot be deleted. Rotate the current log first.',
      },
    };
  }

  return {
    status: 200,
    body: {
      file_id: file.file_id,
      deleted: true,
      message: 'Archive log file deleted successfully.',
    },
  };
}

export function handleAdminLogRotateCurrentMock(): AdminLogRotateResultDto {
  return {
    rotated_file_id: 'log-file-active-002',
    previous_active_file_id: MOCK_ACTIVE_LOG_FILE_ID,
    deleted_archive_file_id: MOCK_ARCHIVE_LOG_FILE_ID,
    message: 'Current log rotated and previous archive deleted.',
  };
}

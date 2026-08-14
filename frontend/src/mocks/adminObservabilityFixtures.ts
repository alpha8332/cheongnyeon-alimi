import type {
  AdminLogEventDetailDto,
  AdminLogFileListItemDto,
} from '../types/adminLog.js';

export const MOCK_ACTIVE_LOG_FILE_ID = 'log-file-active-001';
export const MOCK_ARCHIVE_LOG_FILE_ID = 'log-file-archive-20260810';

export const MOCK_ARCHIVE_DELETE_409_FILE_ID = 'log-file-archive-mock409';

export const MOCK_ADMIN_LOG_FILES: readonly AdminLogFileListItemDto[] = [
  {
    file_id: MOCK_ACTIVE_LOG_FILE_ID,
    filename: 'app.log',
    status: 'active',
    size_bytes: 245_760,
    created_at: '2026-08-11T00:00:00.000Z',
    rotated_at: null,
  },
  {
    file_id: MOCK_ARCHIVE_LOG_FILE_ID,
    filename: 'app.log.2026-08-10',
    status: 'archive',
    size_bytes: 1_048_576,
    created_at: '2026-08-10T00:00:00.000Z',
    rotated_at: '2026-08-11T00:00:00.000Z',
  },
  {
    file_id: 'log-file-archive-20260809',
    filename: 'app.log.2026-08-09',
    status: 'archive',
    size_bytes: 892_416,
    created_at: '2026-08-09T00:00:00.000Z',
    rotated_at: '2026-08-10T00:00:00.000Z',
  },
  {
    file_id: MOCK_ARCHIVE_DELETE_409_FILE_ID,
    filename: 'app.log.mock409',
    status: 'archive',
    size_bytes: 512_000,
    created_at: '2026-08-08T00:00:00.000Z',
    rotated_at: '2026-08-09T00:00:00.000Z',
  },
];

export const MOCK_ADMIN_LOG_EVENTS: readonly AdminLogEventDetailDto[] = [
  {
    event_id: 'log-event-001',
    file_id: MOCK_ACTIVE_LOG_FILE_ID,
    timestamp: '2026-08-11T09:00:01.123Z',
    level: 'INFO',
    component: 'api',
    event: 'request_completed',
    request_id: 'req-7f3a2b1c',
    collection_run_id: null,
    source_id: null,
    duration_ms: 42,
    error_type: null,
    message: 'GET /api/v1/policies completed.',
  },
  {
    event_id: 'log-event-002',
    file_id: MOCK_ACTIVE_LOG_FILE_ID,
    timestamp: '2026-08-11T09:05:12.456Z',
    level: 'ERROR',
    component: 'collector',
    event: 'collection_step_failed',
    request_id: 'req-91ac0044',
    collection_run_id: '11111111-1111-4111-8111-111111111111',
    source_id: 'youthcenter',
    duration_ms: 1200,
    error_type: 'ValidationError',
    message: 'Extracted document failed validation.',
  },
  {
    event_id: 'log-event-003',
    file_id: MOCK_ARCHIVE_LOG_FILE_ID,
    timestamp: '2026-08-10T18:30:00.000Z',
    level: 'WARNING',
    component: 'persistence',
    event: 'partial_policy_persisted',
    request_id: null,
    collection_run_id: '22222222-2222-4222-8222-222222222222',
    source_id: 'bokjiro',
    duration_ms: 88,
    error_type: null,
    message: 'Policy persisted with partial data quality status.',
  },
  {
    event_id: 'log-event-004',
    file_id: MOCK_ARCHIVE_LOG_FILE_ID,
    timestamp: '2026-08-10T19:00:00.000Z',
    level: 'INFO',
    component: 'admin',
    event: 'archive_log_deleted',
    request_id: 'req-admin-delete-01',
    collection_run_id: null,
    source_id: null,
    duration_ms: 15,
    error_type: null,
    message: 'Rotated archive log file deleted after confirmation.',
  },
];

export function findMockAdminLogFileById(
  fileId: string,
): AdminLogFileListItemDto | undefined {
  return MOCK_ADMIN_LOG_FILES.find((file) => file.file_id === fileId);
}

export function findMockAdminLogEventById(
  eventId: string,
): AdminLogEventDetailDto | undefined {
  return MOCK_ADMIN_LOG_EVENTS.find((event) => event.event_id === eventId);
}

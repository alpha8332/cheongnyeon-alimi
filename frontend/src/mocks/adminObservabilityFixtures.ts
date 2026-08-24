import type {
  AdminLogEventListItemDto,
  AdminLogFileListItemDto,
} from '../types/adminLog.js';

export const MOCK_ACTIVE_LOG_FILE_ID = 'app.log';
export const MOCK_ARCHIVE_LOG_FILE_ID = 'app.log.1';
export const MOCK_ARCHIVE_DELETE_409_FILE_ID = 'app.log.mock409';

export const MOCK_ADMIN_LOG_FILES: readonly AdminLogFileListItemDto[] = [
  {
    file_id: MOCK_ACTIVE_LOG_FILE_ID,
    filename: MOCK_ACTIVE_LOG_FILE_ID,
    size_bytes: 245_760,
    is_active: true,
    modified_at: '2026-08-11T09:05:12.456Z',
  },
  {
    file_id: MOCK_ARCHIVE_LOG_FILE_ID,
    filename: MOCK_ARCHIVE_LOG_FILE_ID,
    size_bytes: 1_048_576,
    is_active: false,
    modified_at: '2026-08-11T00:00:00.000Z',
  },
  {
    file_id: 'app.log.2',
    filename: 'app.log.2',
    size_bytes: 892_416,
    is_active: false,
    modified_at: '2026-08-10T00:00:00.000Z',
  },
  {
    file_id: MOCK_ARCHIVE_DELETE_409_FILE_ID,
    filename: MOCK_ARCHIVE_DELETE_409_FILE_ID,
    size_bytes: 512_000,
    is_active: false,
    modified_at: '2026-08-09T00:00:00.000Z',
  },
];

export interface MockAdminLogEvent extends AdminLogEventListItemDto {
  file_id: string;
  message: string;
}

export const MOCK_ADMIN_LOG_EVENTS: readonly MockAdminLogEvent[] = [
  {
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
];

export function findMockAdminLogFileById(
  fileId: string,
): AdminLogFileListItemDto | undefined {
  return MOCK_ADMIN_LOG_FILES.find((file) => file.file_id === fileId);
}

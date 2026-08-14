import type { AdminPolicyListItemDto } from '../types/adminPolicyData.js';
import type {
  AdminLogEventListItemDto,
  AdminLogFileListItemDto,
} from '../types/adminLog.js';

const FORBIDDEN_POLICY_LIST_KEYS = [
  'provenance',
  'raw_document',
  'raw_payload',
  'password',
  'token',
  'pin',
  'sql',
  'stack_trace',
] as const;

const FORBIDDEN_LOG_EVENT_KEYS = [
  'stack_trace',
  'traceback',
  'parameters',
  'sql_parameters',
  'password',
  'token',
  'pin',
  'api_key',
  'request_body',
  'response_body',
  'file_path',
  'absolute_path',
] as const;

const FORBIDDEN_LOG_FILE_KEYS = [
  'path',
  'absolute_path',
  'directory',
  'file_path',
] as const;

function assertPlainObject(
  value: unknown,
  label: string,
): asserts value is Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be a plain object`);
  }
}

function assertNoForbiddenKeys(
  value: Record<string, unknown>,
  forbiddenKeys: readonly string[],
  label: string,
): void {
  for (const key of forbiddenKeys) {
    if (key in value) {
      throw new Error(`${label} must not expose ${key}`);
    }
  }
}

function assertString(value: unknown, label: string): asserts value is string {
  if (typeof value !== 'string') {
    throw new Error(`${label} must be a string`);
  }
}

function assertOptionalString(
  value: unknown,
  label: string,
): asserts value is string | null {
  if (value !== null && typeof value !== 'string') {
    throw new Error(`${label} must be string or null`);
  }
}

function assertNonNegativeInteger(value: unknown, label: string): void {
  if (!Number.isSafeInteger(value) || (value as number) < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
}

export function assertAdminPolicyListItemContract(
  item: unknown,
): asserts item is AdminPolicyListItemDto {
  assertPlainObject(item, 'admin policy list item');
  assertNoForbiddenKeys(item, FORBIDDEN_POLICY_LIST_KEYS, 'admin policy list item');

  assertNonNegativeInteger(item.id, 'admin policy list item.id');
  assertString(item.source_id, 'admin policy list item.source_id');
  assertString(item.source_name, 'admin policy list item.source_name');
  assertOptionalString(item.external_id, 'admin policy list item.external_id');
  assertString(item.title, 'admin policy list item.title');
  assertOptionalString(item.organization, 'admin policy list item.organization');

  if (!Array.isArray(item.categories)) {
    throw new Error('admin policy list item.categories must be an array');
  }

  if (!Array.isArray(item.regions)) {
    throw new Error('admin policy list item.regions must be an array');
  }

  assertString(item.collected_at, 'admin policy list item.collected_at');
  assertString(item.updated_at, 'admin policy list item.updated_at');
}

export function assertAdminLogFileListItemContract(
  item: unknown,
): asserts item is AdminLogFileListItemDto {
  assertPlainObject(item, 'admin log file list item');
  assertNoForbiddenKeys(item, FORBIDDEN_LOG_FILE_KEYS, 'admin log file list item');

  assertString(item.file_id, 'admin log file list item.file_id');
  assertString(item.filename, 'admin log file list item.filename');

  if (item.filename.includes('/') || item.filename.includes('\\')) {
    throw new Error('admin log file list item.filename must be basename only');
  }

  if (item.status !== 'active' && item.status !== 'archive') {
    throw new Error('admin log file list item.status must be active or archive');
  }

  assertNonNegativeInteger(item.size_bytes, 'admin log file list item.size_bytes');
  assertString(item.created_at, 'admin log file list item.created_at');
  assertOptionalString(item.rotated_at, 'admin log file list item.rotated_at');
}

export function assertAdminLogEventListItemContract(
  item: unknown,
): asserts item is AdminLogEventListItemDto {
  assertPlainObject(item, 'admin log event list item');
  assertNoForbiddenKeys(item, FORBIDDEN_LOG_EVENT_KEYS, 'admin log event list item');

  assertString(item.event_id, 'admin log event list item.event_id');
  assertString(item.file_id, 'admin log event list item.file_id');
  assertString(item.timestamp, 'admin log event list item.timestamp');
  assertString(item.level, 'admin log event list item.level');
  assertString(item.component, 'admin log event list item.component');
  assertString(item.event, 'admin log event list item.event');
  assertOptionalString(item.request_id, 'admin log event list item.request_id');
  assertOptionalString(
    item.collection_run_id,
    'admin log event list item.collection_run_id',
  );
  assertOptionalString(item.source_id, 'admin log event list item.source_id');

  if (item.duration_ms !== null) {
    assertNonNegativeInteger(item.duration_ms, 'admin log event list item.duration_ms');
  }

  assertOptionalString(item.error_type, 'admin log event list item.error_type');
}

export function assertPaginationEnvelope(
  envelope: unknown,
  label: string,
): void {
  assertPlainObject(envelope, label);

  if (!Array.isArray(envelope.items)) {
    throw new Error(`${label}.items must be an array`);
  }

  assertNonNegativeInteger(envelope.total, `${label}.total`);
  assertNonNegativeInteger(envelope.page, `${label}.page`);
  assertNonNegativeInteger(envelope.size, `${label}.size`);
  assertNonNegativeInteger(envelope.pages, `${label}.pages`);
}

export function assertAdminObservabilityErrorBody(
  body: unknown,
): asserts body is { detail: string } {
  assertPlainObject(body, 'admin observability error body');
  assertString(body.detail, 'admin observability error body.detail');
}

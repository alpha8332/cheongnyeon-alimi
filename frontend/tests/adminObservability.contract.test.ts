import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import test from 'node:test';
import {
  assertAdminLogEventListItemContract,
  assertAdminLogFileListItemContract,
  assertAdminObservabilityErrorBody,
  assertAdminPolicyListItemContract,
  assertPaginationEnvelope,
} from '../src/mocks/adminObservabilityContract.js';
import {
  handleAdminLogArchiveDeleteMock,
  handleAdminLogEventListMock,
  handleAdminLogFileListMock,
  handleAdminLogRotateCurrentMock,
  handleAdminPolicyDetailMock,
  handleAdminPolicyListMock,
} from '../src/mocks/adminObservabilityHandlers.js';
import {
  MOCK_ACTIVE_LOG_FILE_ID,
  MOCK_ARCHIVE_LOG_FILE_ID,
} from '../src/mocks/adminObservabilityFixtures.js';
import {
  createMockPolicies,
  type SeedPolicyProgram,
} from '../src/mocks/policyContract.js';
import {
  ADMIN_LOG_ENDPOINTS,
  ADMIN_LOG_FILES_PATH,
  ADMIN_LOG_ROTATE_CURRENT_PATH,
  buildAdminLogArchiveDeletePath,
  buildAdminLogEventListPath,
  buildAdminLogFileDetailPath,
  resolveAdminLogEventListQuery,
  resolveAdminLogFileListQuery,
} from '../src/types/adminLog.js';
import {
  ADMIN_POLICY_DATA_ENDPOINTS,
  ADMIN_POLICY_DATA_PATH,
  buildAdminPolicyDetailPath,
  resolveAdminPolicyListQuery,
} from '../src/types/adminPolicyData.js';

const seedPath = resolve(
  process.cwd(),
  '..',
  'data',
  'seeds',
  'initial_programs.json',
);
const seedPrograms = JSON.parse(
  readFileSync(seedPath, 'utf8'),
) as SeedPolicyProgram[];
const mockPolicies = createMockPolicies(seedPrograms);

test('Admin policy data endpoint 경로가 W4-G0 proposal과 일치한다', () => {
  assert.equal(ADMIN_POLICY_DATA_ENDPOINTS.list.path, ADMIN_POLICY_DATA_PATH);
  assert.equal(ADMIN_POLICY_DATA_ENDPOINTS.list.method, 'GET');
  assert.equal(
    buildAdminPolicyDetailPath(mockPolicies[0]?.id ?? 1),
    `${ADMIN_POLICY_DATA_ENDPOINTS.detail.pathPrefix}${mockPolicies[0]?.id ?? 1}`,
  );
});

test('Admin log endpoint 경로가 W4-G0 proposal과 일치한다', () => {
  assert.equal(ADMIN_LOG_ENDPOINTS.fileList.path, ADMIN_LOG_FILES_PATH);
  assert.equal(ADMIN_LOG_ENDPOINTS.rotateCurrent.path, ADMIN_LOG_ROTATE_CURRENT_PATH);
  assert.equal(
    buildAdminLogEventListPath(MOCK_ACTIVE_LOG_FILE_ID),
    `${ADMIN_LOG_FILES_PATH}/${MOCK_ACTIVE_LOG_FILE_ID}/events`,
  );
  assert.equal(
    buildAdminLogArchiveDeletePath(MOCK_ARCHIVE_LOG_FILE_ID),
    buildAdminLogFileDetailPath(MOCK_ARCHIVE_LOG_FILE_ID),
  );
});

test('handleAdminPolicyListMock는 page·size·pages envelope를 반환한다', () => {
  const response = handleAdminPolicyListMock(mockPolicies, {
    page: 1,
    size: 5,
    sort_by: 'id',
    sort_order: 'asc',
  });

  assertPaginationEnvelope(response, 'admin policy list response');
  assert.equal(response.page, 1);
  assert.equal(response.size, 5);
  assert.equal(response.total, mockPolicies.length);
  assert.ok(response.pages >= 1);
  assert.equal(response.items.length, Math.min(5, mockPolicies.length));

  for (const item of response.items) {
    assertAdminPolicyListItemContract(item);
    assert.equal('provenance' in item, false);
    assert.equal('eligibility_text' in item, false);
  }
});

test('handleAdminPolicyDetailMock는 404 safe error와 detail DTO를 반환한다', () => {
  const missing = handleAdminPolicyDetailMock(mockPolicies, 999_999);
  assert.equal(missing.status, 404);
  if (missing.status === 404) {
    assertAdminObservabilityErrorBody(missing.body);
  }

  const found = handleAdminPolicyDetailMock(mockPolicies, mockPolicies[0]?.id ?? 1);
  assert.equal(found.status, 200);
  if (found.status === 200) {
    assert.equal(found.body.id, mockPolicies[0]?.id);
    assert.equal('provenance' in found.body, false);
  }
});

test('resolveAdminPolicyListQuery는 page·size·sort allowlist를 검증한다', () => {
  assert.throws(() => resolveAdminPolicyListQuery({ page: 0 }));
  assert.throws(() => resolveAdminPolicyListQuery({ size: 101 }));
  assert.throws(() => resolveAdminPolicyListQuery({ sort_by: 'sql' as 'id' }));

  assert.deepEqual(
    resolveAdminPolicyListQuery({ page: 2, size: 10, sort_by: 'title' }),
    {
      page: 2,
      size: 10,
      sort_by: 'title',
      sort_order: 'asc',
    },
  );
});

test('handleAdminLogFileListMock는 pagination envelope와 basename filename을 반환한다', () => {
  const response = handleAdminLogFileListMock({ page: 1, size: 2 });

  assertPaginationEnvelope(response, 'admin log file list response');
  assert.equal(response.items.length, 2);

  for (const item of response.items) {
    assertAdminLogFileListItemContract(item);
    assert.equal(item.filename.includes('/'), false);
  }
});

test('handleAdminLogEventListMock는 safe event 필드만 list item에 노출한다', () => {
  const response = handleAdminLogEventListMock({
    page: 1,
    size: 10,
    file_id: MOCK_ACTIVE_LOG_FILE_ID,
  });

  assertPaginationEnvelope(response, 'admin log event list response');
  assert.ok(response.items.length >= 1);

  for (const item of response.items) {
    assertAdminLogEventListItemContract(item);
    assert.equal('message' in item, false);
    assert.equal('stack_trace' in item, false);
  }
});

test('handleAdminLogArchiveDeleteMock는 active file 409와 archive delete를 구분한다', () => {
  const active = handleAdminLogArchiveDeleteMock(MOCK_ACTIVE_LOG_FILE_ID);
  assert.equal(active.status, 409);
  if (active.status === 409) {
    assertAdminObservabilityErrorBody(active.body);
  }

  const archive = handleAdminLogArchiveDeleteMock(MOCK_ARCHIVE_LOG_FILE_ID);
  assert.equal(archive.status, 200);
  if (archive.status === 200) {
    assert.equal(archive.body.deleted, true);
    assert.equal(archive.body.file_id, MOCK_ARCHIVE_LOG_FILE_ID);
  }
});

test('handleAdminLogRotateCurrentMock는 rotate 결과 DTO를 반환한다', () => {
  const result = handleAdminLogRotateCurrentMock();
  assert.equal(result.previous_active_file_id, MOCK_ACTIVE_LOG_FILE_ID);
  assert.ok(result.rotated_file_id.length > 0);
  assert.ok(result.message.length > 0);
});

test('resolveAdminLogFileListQuery와 resolveAdminLogEventListQuery는 size 경계를 검증한다', () => {
  assert.throws(() => resolveAdminLogFileListQuery({ size: 0 }));
  assert.throws(() => resolveAdminLogEventListQuery({ size: 101 }));
  assert.throws(() => resolveAdminLogEventListQuery({ level: 'TRACE' as 'INFO' }));
});

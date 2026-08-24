import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import test from 'node:test';
import {
  assertAdminLogEventListResponseContract,
  assertAdminLogFileListResponseContract,
  assertAdminObservabilityErrorBody,
  assertAdminPolicyListItemContract,
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
import { createMockPolicies, type SeedPolicyProgram } from '../src/mocks/policyContract.js';
import {
  ADMIN_LOG_ENDPOINTS,
  ADMIN_LOG_EVENTS_PATH,
  ADMIN_LOG_FILES_PATH,
  ADMIN_LOG_ROTATE_CURRENT_PATH,
  buildAdminLogArchiveDeletePath,
  resolveAdminLogEventListQuery,
} from '../src/types/adminLog.js';
import {
  ADMIN_POLICY_DATA_ENDPOINTS,
  ADMIN_POLICY_DATA_PATH,
  buildAdminPolicyDetailPath,
  resolveAdminPolicyListQuery,
} from '../src/types/adminPolicyData.js';

const seedPath = resolve(process.cwd(), '..', 'data', 'seeds', 'initial_programs.json');
const seedPrograms = JSON.parse(readFileSync(seedPath, 'utf8')) as SeedPolicyProgram[];
const mockPolicies = createMockPolicies(seedPrograms);

test('관리자 정책 endpoint가 Backend 계약과 일치한다', () => {
  assert.equal(ADMIN_POLICY_DATA_ENDPOINTS.list.path, ADMIN_POLICY_DATA_PATH);
  assert.equal(ADMIN_POLICY_DATA_ENDPOINTS.list.method, 'GET');
  assert.equal(
    buildAdminPolicyDetailPath(mockPolicies[0]?.id ?? 1),
    `${ADMIN_POLICY_DATA_ENDPOINTS.detail.pathPrefix}${mockPolicies[0]?.id ?? 1}`,
  );
});

test('관리자 로그 endpoint가 Backend 계약과 일치한다', () => {
  assert.equal(ADMIN_LOG_ENDPOINTS.fileList.path, ADMIN_LOG_FILES_PATH);
  assert.equal(ADMIN_LOG_ENDPOINTS.eventList.path, ADMIN_LOG_EVENTS_PATH);
  assert.equal(ADMIN_LOG_ENDPOINTS.rotateCurrent.path, ADMIN_LOG_ROTATE_CURRENT_PATH);
  assert.equal(
    buildAdminLogArchiveDeletePath(MOCK_ARCHIVE_LOG_FILE_ID),
    `/api/v1/admin/logs/archives/${MOCK_ARCHIVE_LOG_FILE_ID}`,
  );
});

test('정책 목록 Mock이 Backend page·limit envelope와 공개 projection을 반환한다', () => {
  const response = handleAdminPolicyListMock(mockPolicies, {
    page: 1,
    limit: 5,
    sort_by: 'id',
    order: 'asc',
  });

  assert.equal(response.page, 1);
  assert.equal(response.limit, 5);
  assert.equal(response.total, mockPolicies.length);
  assert.equal(response.items.length, Math.min(5, mockPolicies.length));
  for (const item of response.items) {
    assertAdminPolicyListItemContract(item);
    assert.equal('provenance' in item, false);
    assert.equal('eligibility_text' in item, false);
    assert.equal('age_min' in item, false);
  }
});

test('policy region mock includes nationwide and empty-region policies like Backend', () => {
  const template = mockPolicies[0];
  assert.ok(template);
  if (!template) return;

  const response = handleAdminPolicyListMock(
    [
      { ...template, id: 10_001, regions: ['서울'] },
      { ...template, id: 10_002, regions: ['전국'] },
      { ...template, id: 10_003, regions: [] },
      { ...template, id: 10_004, regions: ['부산'] },
    ],
    {
      page: 1,
      limit: 10,
      region: '서울',
      sort_by: 'id',
      order: 'asc',
    },
  );

  assert.deepEqual(
    response.items.map((item) => item.id),
    [10_001, 10_002, 10_003],
  );
  assert.equal(response.total, 3);
});

test('정책 상세 Mock은 404 safe error와 Backend detail DTO를 반환한다', () => {
  const missing = handleAdminPolicyDetailMock(mockPolicies, 999_999);
  assert.equal(missing.status, 404);
  if (missing.status === 404) assertAdminObservabilityErrorBody(missing.body);

  const found = handleAdminPolicyDetailMock(mockPolicies, mockPolicies[0]?.id ?? 1);
  assert.equal(found.status, 200);
  if (found.status === 200) {
    assert.equal(found.body.id, mockPolicies[0]?.id);
    assert.equal('schema_version' in found.body, false);
    assert.equal('application_schedule' in found.body, false);
  }
});

test('정책 query resolver가 limit·sort allowlist를 검증한다', () => {
  assert.throws(() => resolveAdminPolicyListQuery({ page: 0 }));
  assert.throws(() => resolveAdminPolicyListQuery({ limit: 101 }));
  assert.throws(() => resolveAdminPolicyListQuery({ sort_by: 'sql' as 'id' }));
  assert.deepEqual(resolveAdminPolicyListQuery({ page: 2, limit: 10, sort_by: 'title' }), {
    page: 2,
    limit: 10,
    sort_by: 'title',
    order: 'desc',
  });
});

test('로그 파일 Mock은 Backend files envelope와 basename만 반환한다', () => {
  const response = handleAdminLogFileListMock();
  assertAdminLogFileListResponseContract(response);
  assert.ok(response.files.length >= 2);
  for (const item of response.files) {
    assert.equal(item.filename.includes('/'), false);
    assert.equal('path' in item, false);
  }
});

test('로그 이벤트 Mock은 Backend events envelope와 safe allowlist만 반환한다', () => {
  const response = handleAdminLogEventListMock({
    page: 1,
    limit: 10,
    file_id: MOCK_ACTIVE_LOG_FILE_ID,
  });
  assertAdminLogEventListResponseContract(response);
  assert.ok(response.events.length >= 1);
  for (const item of response.events) {
    assert.equal('message' in item, false);
    assert.equal('stack_trace' in item, false);
    assert.equal('raw' in item, false);
    assert.equal('sql_parameters' in item, false);
  }
});

test('archive 삭제 Mock은 active 400과 archive 감사 응답을 구분한다', () => {
  const active = handleAdminLogArchiveDeleteMock(MOCK_ACTIVE_LOG_FILE_ID);
  assert.equal(active.status, 400);
  assertAdminObservabilityErrorBody(active.body);

  const archive = handleAdminLogArchiveDeleteMock(MOCK_ARCHIVE_LOG_FILE_ID);
  assert.equal(archive.status, 200);
  if (archive.status === 200) {
    assert.equal(archive.body.deleted, true);
    assert.ok(archive.body.audit_id.length > 0);
  }
});

test('현재 로그 정리 Mock은 rotate·생성 archive 삭제·감사 의미를 반환한다', () => {
  const result = handleAdminLogRotateCurrentMock();
  assert.equal(result.rotated_file_id, MOCK_ACTIVE_LOG_FILE_ID);
  assert.ok(result.deleted_archive_file_id.startsWith('app.log.'));
  assert.ok(result.audit_id.length > 0);
});

test('로그 query resolver가 Backend limit·level 경계를 검증한다', () => {
  assert.throws(() => resolveAdminLogEventListQuery({ limit: 101 }));
  assert.throws(() => resolveAdminLogEventListQuery({ level: 'TRACE' as 'INFO' }));
  assert.deepEqual(resolveAdminLogEventListQuery({ file_id: ' app.log.1 ', q: ' fail ' }), {
    file_id: 'app.log.1',
    page: 1,
    limit: 20,
    q: 'fail',
  });
});

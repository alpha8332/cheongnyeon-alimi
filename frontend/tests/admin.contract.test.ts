import assert from 'node:assert/strict';
import test from 'node:test';
import {
  ADMIN_APP_ROUTES,
  ADMIN_SESSION_PATH,
  buildCollectionRunDetailPath,
  COLLECTION_RUNS_PATH,
  COLLECTION_RUN_TRIGGER_PATH,
  resolveCollectionRunListQuery,
} from '../src/api/adminRequest.js';
import { handleAdminSessionMock } from '../src/mocks/adminSessionHandlers.js';
import {
  handleCollectionRunDetailMock,
  handleCollectionRunListMock,
} from '../src/mocks/collectionRunHandlers.js';
import { MOCK_COLLECTION_RUN_DETAILS } from '../src/mocks/collectionRunFixtures.js';
import {
  ADMIN_SESSION_ENDPOINT,
  type AdminSessionResponse,
} from '../src/types/adminSession.js';
import {
  COLLECTION_RUN_ADMIN_ENDPOINTS,
  COLLECTION_RUN_ADMIN_PATH,
  type CollectionRunDetailDto,
} from '../src/types/collectionRun.js';

function assertDetailCountFieldsNonNegative(run: CollectionRunDetailDto): void {
  const countFields = [
    'requested_count',
    'raw_document_count',
    'extracted_count',
    'accepted_count',
    'partial_count',
    'invalid_count',
    'duplicate_count',
    'rejected_count',
    'inserted_count',
    'updated_count',
    'unchanged_count',
    'skipped_count',
    'failed_count',
  ] as const;

  for (const field of countFields) {
    assert.ok(run[field] >= 0, `${field} must be non-negative`);
  }
}

test('Admin session endpoint는 POST body 경로만 사용한다', () => {
  assert.equal(ADMIN_SESSION_ENDPOINT.method, 'POST');
  assert.equal(ADMIN_SESSION_PATH, ADMIN_SESSION_ENDPOINT.path);
  assert.equal(ADMIN_SESSION_PATH.includes('?'), false);
  assert.equal(ADMIN_SESSION_PATH.includes('pin='), false);
});

test('CollectionRun admin list·detail·trigger 경로가 Backend 05와 일치한다', () => {
  assert.equal(COLLECTION_RUNS_PATH, COLLECTION_RUN_ADMIN_PATH);
  assert.equal(COLLECTION_RUN_TRIGGER_PATH, COLLECTION_RUN_ADMIN_PATH);
  assert.equal(COLLECTION_RUN_ADMIN_ENDPOINTS.list.path, COLLECTION_RUN_ADMIN_PATH);
  assert.equal(
    buildCollectionRunDetailPath(MOCK_COLLECTION_RUN_DETAILS[0].run_id),
    `${COLLECTION_RUN_ADMIN_ENDPOINTS.detail.pathPrefix}${MOCK_COLLECTION_RUN_DETAILS[0].run_id}`,
  );
});

test('ADMIN_APP_ROUTES는 API 경로에 PIN·token query를 포함하지 않는다', () => {
  const paths = [
    ADMIN_APP_ROUTES.login,
    ADMIN_APP_ROUTES.dashboard,
    ADMIN_APP_ROUTES.collectors,
    ADMIN_APP_ROUTES.runs,
    ADMIN_APP_ROUTES.runDetail('test-run-id'),
    ADMIN_APP_ROUTES.quality,
    ADMIN_APP_ROUTES.policies,
    ADMIN_APP_ROUTES.policyDetail(1),
    ADMIN_APP_ROUTES.logs,
  ];

  for (const path of paths) {
    assert.equal(path.includes('pin='), false);
    assert.equal(path.includes('token='), false);
    assert.equal(path.includes('access_token='), false);
  }
});

test('handleAdminSessionMock는 development PIN 0000으로 session을 발급한다', () => {
  const result = handleAdminSessionMock({ pin: '0000' });
  assert.equal(result.status, 200);

  if (result.status === 200) {
    const body: AdminSessionResponse = result.body;
    assert.equal(body.token_type, 'bearer');
    assert.equal(body.role, 'admin');
    assert.ok(body.access_token.length > 0);
    assert.ok(body.expires_in > 0);
  }
});

test('handleAdminSessionMock는 잘못된 PIN·429·422를 구분한다', () => {
  assert.equal(handleAdminSessionMock({ pin: '1234' }).status, 401);
  assert.equal(handleAdminSessionMock({ pin: '4290' }).status, 429);
  assert.equal(handleAdminSessionMock({ pin: '12ab' }).status, 422);
});

test('handleCollectionRunListMock는 page·size·pages envelope를 반환한다', () => {
  const page1 = handleCollectionRunListMock({ page: 1, size: 2 });
  assert.equal(page1.page, 1);
  assert.equal(page1.size, 2);
  assert.equal(page1.total, MOCK_COLLECTION_RUN_DETAILS.length);
  assert.equal(page1.pages, 2);
  assert.equal(page1.items.length, 2);
  assert.equal('duplicate_count' in (page1.items[0] ?? {}), false);

  const filtered = handleCollectionRunListMock({
    status: 'running',
    page: 1,
    size: 10,
  });
  assert.equal(filtered.total, 1);
  assert.equal(filtered.items[0]?.status, 'running');
  assert.equal(filtered.items[0]?.is_stale, true);
  assert.equal('requested_count' in (filtered.items[0] ?? {}), false);
});

test('handleCollectionRunDetailMock는 404와 detail DTO를 반환한다', () => {
  const missing = handleCollectionRunDetailMock('not-a-run');
  assert.equal(missing.status, 404);

  const found = handleCollectionRunDetailMock(MOCK_COLLECTION_RUN_DETAILS[0].run_id);
  assert.equal(found.status, 200);
  if (found.status === 200) {
    assertDetailCountFieldsNonNegative(found.body);
    assert.equal(found.body.duplicate_count, 0);
    assert.equal(found.body.error_type, null);
  }
});

test('Mock CollectionRun detail은 terminal finished_at 규칙을 따른다', () => {
  for (const run of MOCK_COLLECTION_RUN_DETAILS) {
    assertDetailCountFieldsNonNegative(run);

    if (run.status === 'running') {
      assert.equal(run.finished_at, null);
    } else {
      assert.notEqual(run.finished_at, null);
    }
  }
});

test('resolveCollectionRunListQuery는 page·size 경계를 검증한다', () => {
  assert.throws(() => resolveCollectionRunListQuery({ page: 0 }));
  assert.throws(() => resolveCollectionRunListQuery({ size: 101 }));
  assert.deepEqual(resolveCollectionRunListQuery({ page: 2, size: 5 }), {
    page: 2,
    size: 5,
  });
  assert.equal(
    resolveCollectionRunListQuery({ status: 'queued' }).status,
    'queued',
  );
});

import assert from 'node:assert/strict';
import test from 'node:test';
import { ADMIN_APP_ROUTES } from '../src/api/adminRequest.js';
import {
  buildAdminLogsDrillDownUrl,
  buildCollectionRunDetailDrillDownUrl,
  formatAdminMetricCount,
  getAdminMetricCardVariant,
  shouldLinkMetricDrillDown,
  shouldShowLogsDrillDown,
} from '../src/utils/adminDashboard.js';
import type { CollectionRunDetailDto } from '../src/types/collectionRun.js';

const SAMPLE_RUN: CollectionRunDetailDto = {
  run_id: '11111111-1111-4111-8111-111111111111',
  source_id: 'youthcenter',
  run_type: 'collection',
  trigger_type: 'admin',
  started_at: '2026-08-10T09:00:00.000Z',
  finished_at: '2026-08-10T09:12:34.000Z',
  status: 'partial_failure',
  is_stale: false,
  requested_count: 10,
  raw_document_count: 10,
  extracted_count: 10,
  accepted_count: 8,
  partial_count: 1,
  invalid_count: 2,
  duplicate_count: 1,
  rejected_count: 0,
  inserted_count: 3,
  updated_count: 4,
  unchanged_count: 1,
  skipped_count: 0,
  failed_count: 5,
  error_type: null,
};

test('formatAdminMetricCount는 ko-KR locale 숫자를 반환한다', () => {
  assert.equal(formatAdminMetricCount(1234), '1,234');
});

test('getAdminMetricCardVariant는 실패·무효·중복 count에 variant를 부여한다', () => {
  assert.equal(getAdminMetricCardVariant('failed_count', 0), 'default');
  assert.equal(getAdminMetricCardVariant('failed_count', 1), 'danger');
  assert.equal(getAdminMetricCardVariant('invalid_count', 2), 'warning');
  assert.equal(getAdminMetricCardVariant('duplicate_count', 1), 'warning');
  assert.equal(getAdminMetricCardVariant('inserted_count', 9), 'default');
});

test('shouldLinkMetricDrillDown은 품질 이슈 metric만 drill-down 링크를 허용한다', () => {
  assert.equal(shouldLinkMetricDrillDown('failed_count', 1), true);
  assert.equal(shouldLinkMetricDrillDown('invalid_count', 1), true);
  assert.equal(shouldLinkMetricDrillDown('duplicate_count', 1), true);
  assert.equal(shouldLinkMetricDrillDown('inserted_count', 10), false);
  assert.equal(shouldLinkMetricDrillDown('failed_count', 0), false);
});

test('buildCollectionRunDetailDrillDownUrl은 admin run detail route를 반환한다', () => {
  assert.equal(
    buildCollectionRunDetailDrillDownUrl(SAMPLE_RUN.run_id),
    ADMIN_APP_ROUTES.runDetail(SAMPLE_RUN.run_id),
  );
});

test('buildAdminLogsDrillDownUrl은 admin logs route를 반환한다', () => {
  assert.equal(buildAdminLogsDrillDownUrl(), ADMIN_APP_ROUTES.logs);
});

test('shouldShowLogsDrillDown은 failed_count·terminal failure 상태에서 Log 링크를 노출한다', () => {
  assert.equal(shouldShowLogsDrillDown(SAMPLE_RUN), true);
  assert.equal(
    shouldShowLogsDrillDown({ ...SAMPLE_RUN, failed_count: 0, status: 'succeeded' }),
    false,
  );
  assert.equal(
    shouldShowLogsDrillDown({ ...SAMPLE_RUN, failed_count: 0, status: 'failed' }),
    true,
  );
});

import assert from 'node:assert/strict';
import test from 'node:test';
import { handleAdminCollectorStatusMock } from '../src/mocks/adminCollectorHandlers.js';
import { ADMIN_COLLECTORS_PATH } from '../src/types/adminCollector.js';

const EXPECTED_SOURCE_IDS = [
  'bokjiro-central-welfare-api',
  'cheonan-youthcenter-web',
  'data-go-kr-incheon-youth-programs',
  'kinfa-financial-product-web',
  'kosaf-scholarship-web',
  'kpass-transit-refund-web',
  'lh-housing-announcement-web',
  'regional-busan-youth-platform',
  'regional-gyeongbuk-youth-platform',
  'work24-policy-web',
  'youthcenter-api',
];

test('collector admin endpoint is stable', () => {
  assert.equal(ADMIN_COLLECTORS_PATH, '/api/v1/admin/collectors');
});

test('collector status fixture covers the registered source contract', () => {
  const payload = handleAdminCollectorStatusMock();

  assert.deepEqual(
    payload.collectors.map((collector) => collector.source_id),
    EXPECTED_SOURCE_IDS,
  );
  assert.equal(
    payload.collectors.reduce(
      (total, collector) => total + collector.public_policy_count,
      0,
    ),
    2052,
  );
});

test('collector status never exposes credential values or secret field names', () => {
  const serialized = JSON.stringify(handleAdminCollectorStatusMock()).toLowerCase();

  for (const forbidden of ['api_key', 'secret', 'password', 'pin', 'token']) {
    assert.equal(serialized.includes(forbidden), false, forbidden);
  }
});


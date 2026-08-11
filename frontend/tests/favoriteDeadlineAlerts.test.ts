import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto } from '../src/types/policy.js';
import { buildFavoriteDeadlineAlerts } from '../src/utils/favoriteDeadlineAlerts.js';

function createPolicy(id: number, applicationEnd: string | null): PolicyDto {
  return {
    schema_version: '1.1.0',
    source_id: 'test',
    source_name: 'Test',
    external_id: null,
    title: `Policy ${id}`,
    organization: null,
    summary: null,
    category_text: null,
    categories: ['other'],
    application_period_text: null,
    application_start: null,
    application_end: applicationEnd,
    application_schedule: 'fixed_period',
    application_status: 'open',
    region_text: null,
    regions: ['전국'],
    age_min: null,
    age_max: null,
    age_condition_text: null,
    eligibility_text: null,
    support_content: null,
    application_method: null,
    education_statuses: [],
    employment_statuses: [],
    required_conditions: [],
    preferred_conditions: [],
    excluded_conditions: [],
    source_url: 'https://example.gov/policy',
    collected_at: '2026-08-11T00:00:00.000Z',
    data_quality_status: 'valid',
    id,
    created_at: '2026-08-11T00:00:00.000Z',
    updated_at: '2026-08-11T00:00:00.000Z',
  };
}

test('buildFavoriteDeadlineAlerts는 북마크∩D-7 이내 정책만 반환한다', () => {
  const reference = new Date('2026-08-11T05:00:00.000Z');
  const policies = [
    createPolicy(1, '2026-08-15'),
    createPolicy(2, '2026-09-01'),
    createPolicy(3, null),
    createPolicy(4, '2026-08-12'),
  ];

  const alerts = buildFavoriteDeadlineAlerts(
    policies,
    [1, 2, 3, 4],
    reference,
    7,
  );

  assert.equal(alerts.length, 2);
  assert.deepEqual(
    alerts.map((alert) => alert.policyId),
    [4, 1],
  );
});

test('buildFavoriteDeadlineAlerts는 비즐겨찾기 정책을 제외한다', () => {
  const reference = new Date('2026-08-11T05:00:00.000Z');
  const policies = [createPolicy(10, '2026-08-13')];

  const alerts = buildFavoriteDeadlineAlerts(policies, [], reference, 7);
  assert.equal(alerts.length, 0);
});

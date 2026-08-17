import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto } from '../src/types/policy.js';
import {
  getPolicyCardDDayBadgeLabel,
  getPolicyDeadlineInfo,
} from '../src/utils/policyDeadline.js';

function createPolicy(overrides: Partial<PolicyDto> = {}): PolicyDto {
  return {
    schema_version: '1.2.0',
    source_id: 'seed',
    source_name: 'seed',
    external_id: 'ext-1',
    title: '테스트 정책',
    organization: '기관',
    summary: null,
    category_text: null,
    categories: ['housing'],
    application_period_text: null,
    application_start: '2026-08-01',
    application_end: '2026-08-31',
    application_schedule: 'fixed_period',
    application_status: 'open',
    region_text: null,
    regions: ['서울특별시'],
    age_min: 19,
    age_max: 34,
    age_condition_text: null,
    eligibility_text: null,
    support_content: null,
    application_method: null,
    education_statuses: [],
    employment_statuses: [],
    required_conditions: [],
    preferred_conditions: [],
    excluded_conditions: [],
    source_url: 'https://example.com',
    collected_at: '2026-08-01T00:00:00.000Z',
    data_quality_status: 'valid',
    id: 1,
    created_at: '2026-08-01T00:00:00.000Z',
    updated_at: '2026-08-01T00:00:00.000Z',
    ...overrides,
  };
}

test('getPolicyCardDDayBadgeLabel은 upcoming·today만 D-nn/D-Day를 반환한다', () => {
  const referenceDate = new Date('2026-08-13T12:00:00.000Z');

  assert.equal(getPolicyCardDDayBadgeLabel(createPolicy(), referenceDate), 'D-18');
  assert.equal(
    getPolicyCardDDayBadgeLabel(
      createPolicy({ application_end: '2026-08-13' }),
      referenceDate,
    ),
    'D-Day',
  );
  assert.equal(
    getPolicyCardDDayBadgeLabel(
      createPolicy({
        application_schedule: 'always',
        application_end: null,
        application_status: 'open',
      }),
      referenceDate,
    ),
    null,
  );
  assert.equal(
    getPolicyCardDDayBadgeLabel(
      createPolicy({ application_status: 'closed' }),
      referenceDate,
    ),
    null,
  );
});

test('getPolicyCardDDayBadgeLabel은 마감 지난 정책에 null을 반환한다', () => {
  const referenceDate = new Date('2026-09-01T12:00:00.000Z');
  assert.equal(getPolicyCardDDayBadgeLabel(createPolicy(), referenceDate), null);
  assert.equal(getPolicyDeadlineInfo(createPolicy(), referenceDate).kind, 'past');
});

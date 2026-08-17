import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto } from '../src/types/policy.js';
import { getPolicyDisplayTitle } from '../src/utils/policyDisplay.js';
import { normalizePolicyYmd } from '../src/utils/policyDeadline.js';
import { policyMatchesCategoryFilters } from '../src/utils/calendarCategoryTheme.js';

function createPolicy(overrides: Partial<PolicyDto> = {}): PolicyDto {
  return {
    schema_version: '1.1.0',
    source_id: 'test',
    source_name: 'Test Source',
    external_id: null,
    title: '',
    organization: null,
    summary: null,
    category_text: null,
    categories: ['other'],
    application_period_text: null,
    application_start: null,
    application_end: null,
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
    id: 1,
    created_at: '2026-08-11T00:00:00.000Z',
    updated_at: '2026-08-11T00:00:00.000Z',
    ...overrides,
  };
}

test('normalizePolicyYmd는 ISO datetime을 YYYY-MM-DD로 정규화한다', () => {
  assert.equal(normalizePolicyYmd('2026-08-20'), '2026-08-20');
  assert.equal(normalizePolicyYmd('2026-08-20T00:00:00Z'), '2026-08-20');
  assert.equal(normalizePolicyYmd(' 2026-08-20T15:00:00+09:00 '), '2026-08-20');
  assert.equal(normalizePolicyYmd(null), null);
  assert.equal(normalizePolicyYmd('invalid'), null);
});

test('getPolicyDisplayTitle은 title·legacy 필드·HTML 폴백을 처리한다', () => {
  assert.equal(
    getPolicyDisplayTitle(createPolicy({ title: '  주거 지원  ' })),
    '주거 지원',
  );
  assert.equal(
    getPolicyDisplayTitle({
      ...createPolicy({ title: '' }),
      plcyNm: '<b>합성 청년 주거 지원</b>',
    } as PolicyDto),
    '합성 청년 주거 지원',
  );
  assert.equal(
    getPolicyDisplayTitle({
      ...createPolicy({ title: '' }),
      policy_name: '청년 일자리',
    } as PolicyDto),
    '청년 일자리',
  );
  assert.equal(getPolicyDisplayTitle(createPolicy({ title: '', category_text: '복지' })), '복지');
  assert.equal(getPolicyDisplayTitle(createPolicy({ title: '' })), '정책');
});

test('policyMatchesCategoryFilters는 unknown category를 other로 매칭한다', () => {
  const enabled = new Set(['other'] as const);
  assert.equal(
    policyMatchesCategoryFilters(
      createPolicy({ categories: ['unknown-category' as PolicyDto['categories'][number]] }),
      enabled,
    ),
    true,
  );
});

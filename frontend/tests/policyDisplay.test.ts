import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto } from '../src/types/policy.js';
import {
  formatApplicationPeriodCard,
  formatApplicationPeriodDisplay,
  formatAge,
  formatCollectedAt,
  formatPolicyDateDot,
  POLICY_ELIGIBILITY_NOTICE,
} from '../src/utils/policyDisplay.js';

function createPolicy(overrides: Partial<PolicyDto> = {}): PolicyDto {
  return {
    schema_version: '1.2.0',
    source_id: 'test',
    source_name: 'Test Source',
    external_id: null,
    title: 'Test Policy',
    organization: 'Test Org',
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
    source_url: 'https://example.gov/policy',
    collected_at: '2026-08-11T00:00:00.000Z',
    data_quality_status: 'valid',
    id: 1,
    created_at: '2026-08-11T00:00:00.000Z',
    updated_at: '2026-08-11T00:00:00.000Z',
    ...overrides,
  };
}

test('검색 결과는 실제 자격 확정이 아님을 명시한다', () => {
  assert.match(POLICY_ELIGIBILITY_NOTICE, /자격 충족을 확정하지 않습니다/);
  assert.match(POLICY_ELIGIBILITY_NOTICE, /원문과 세부 요건/);
});

test('collected_at을 한국 표준시로 표시한다', () => {
  assert.equal(
    formatCollectedAt('2026-08-06T00:30:00Z'),
    '2026-08-06 09:30 KST',
  );
});

test('잘못된 collected_at은 미확인으로 표시한다', () => {
  assert.equal(formatCollectedAt('not-a-date'), '수집 시각 미확인');
});

test('0세~0세 sentinel은 실제 연령 조건처럼 표시하지 않는다', () => {
  assert.equal(formatAge(createPolicy({ age_min: 0, age_max: 0 })), '연령 정보 없음');
  assert.equal(
    formatAge(
      createPolicy({
        age_min: null,
        age_max: null,
        age_condition_text: '0세 ~ 0세',
      }),
    ),
    '연령 정보 없음',
  );
  assert.equal(
    formatAge(
      createPolicy({
        age_min: 0,
        age_max: 0,
        age_condition_text: '공식 공고 확인',
      }),
    ),
    '연령 정보 없음',
  );
});

test('formatPolicyDateDot은 ISO·YMD를 YYYY.MM.DD로 변환한다', () => {
  assert.equal(formatPolicyDateDot('2026-08-01'), '2026.08.01');
  assert.equal(formatPolicyDateDot('2026-08-01T15:00:00.000Z'), '2026.08.01');
  assert.equal(formatPolicyDateDot(null), null);
  assert.equal(formatPolicyDateDot('invalid'), null);
});

test('formatApplicationPeriodCard는 목록 카드용 기간을 정규화한다', () => {
  assert.equal(
    formatApplicationPeriodCard(createPolicy()),
    '2026.08.01 ~ 2026.08.31',
  );
  assert.equal(
    formatApplicationPeriodCard(
      createPolicy({ application_start: null, application_end: '2026-08-31' }),
    ),
    '2026.08.31 마감',
  );
  assert.equal(
    formatApplicationPeriodCard(
      createPolicy({
        application_start: '2026-08-01',
        application_end: null,
        application_schedule: 'fixed_period',
      }),
    ),
    '2026.08.01 시작',
  );
  assert.equal(
    formatApplicationPeriodCard(
      createPolicy({
        application_start: null,
        application_end: null,
        application_schedule: 'always',
      }),
    ),
    '상시',
  );
});

test('formatApplicationPeriodDisplay는 상세용 기간과 텍스트 날짜를 정규화한다', () => {
  assert.equal(
    formatApplicationPeriodDisplay(createPolicy()),
    '2026.08.01 ~ 2026.08.31',
  );
  assert.equal(
    formatApplicationPeriodDisplay(
      createPolicy({
        application_start: null,
        application_end: null,
        application_period_text: '2026-08-01 ~ 2026-08-31',
      }),
    ),
    '2026.08.01 ~ 2026.08.31',
  );
  assert.equal(
    formatApplicationPeriodDisplay(
      createPolicy({
        application_start: null,
        application_end: null,
        application_period_text: '20260330 ~ 20260529',
      }),
    ),
    '2026.03.30 ~ 2026.05.29',
  );
});

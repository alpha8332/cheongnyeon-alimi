import assert from 'node:assert/strict';
import test from 'node:test';
import { ELIGIBILITY_SUMMARY_FIXTURES } from '../src/mocks/policyDetailFixtures.js';
import type { PolicyDto } from '../src/types/policy.js';
import type { UserSavedConditions } from '../src/types/userLocalStorage.js';
import {
  compareEligibilityCondition,
  compareSavedPolicyCategory,
  ELIGIBILITY_COMPARISON_LABELS,
  hasSavedConditionsForComparison,
} from '../src/utils/eligibilityComparison.js';
import {
  getEligibilityCategoryLabel,
  shouldExpandEligibilityText,
  truncateEligibilityText,
} from '../src/utils/eligibilitySummaryDisplay.js';

const POLICY: PolicyDto = {
  schema_version: '1.1.0',
  source_id: 'mock',
  source_name: 'Mock',
  external_id: 'ext-1',
  title: 'Test Policy',
  organization: 'Org',
  summary: null,
  category_text: null,
  categories: ['housing', 'welfare'],
  application_period_text: null,
  application_start: null,
  application_end: null,
  application_schedule: 'always',
  application_status: 'open',
  region_text: null,
  regions: ['서울', '경기'],
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
};

test('ELIGIBILITY_COMPARISON_LABELS는 W4-G0 copy를 사용한다', () => {
  assert.equal(ELIGIBILITY_COMPARISON_LABELS.match, '조건상 일치');
  assert.equal(ELIGIBILITY_COMPARISON_LABELS.mismatch, '조건상 불일치');
  assert.equal(ELIGIBILITY_COMPARISON_LABELS.needs_review, '추가 확인 필요');
});

test('hasSavedConditionsForComparison은 저장 조건 존재 여부를 판별한다', () => {
  assert.equal(hasSavedConditionsForComparison(null), false);
  assert.equal(
    hasSavedConditionsForComparison({ region: null, age: null, category: null }),
    false,
  );
  assert.equal(
    hasSavedConditionsForComparison({ region: '서울', age: null, category: null }),
    true,
  );
});

test('compareEligibilityCondition은 age·region saved conditions를 비교한다', () => {
  const complete = ELIGIBILITY_SUMMARY_FIXTURES.complete;
  const ageItem = complete.requirements.find((item) => item.category === 'age');
  const regionItem = complete.requirements.find((item) => item.category === 'region');

  assert.ok(ageItem);
  assert.ok(regionItem);

  const conditions: UserSavedConditions = {
    region: '서울',
    age: 25,
    category: null,
  };

  assert.equal(
    compareEligibilityCondition(ageItem, POLICY, conditions),
    'match',
  );
  assert.equal(
    compareEligibilityCondition(regionItem, POLICY, conditions),
    'match',
  );

  assert.equal(
    compareEligibilityCondition(ageItem, POLICY, {
      ...conditions,
      age: 40,
    }),
    'mismatch',
  );
});

test('compareEligibilityCondition은 evidence 없는 항목을 추가 확인 필요로 표시한다', () => {
  const partial = ELIGIBILITY_SUMMARY_FIXTURES.partial;
  const item = partial.requirements.find((entry) => entry.evidence === null);

  assert.ok(item);

  assert.equal(
    compareEligibilityCondition(item, POLICY, {
      region: '서울',
      age: 25,
      category: null,
    }),
    'needs_review',
  );
});

test('compareSavedPolicyCategory는 policy categories와 saved category를 비교한다', () => {
  assert.equal(
    compareSavedPolicyCategory(POLICY, {
      region: null,
      age: null,
      category: 'housing',
    }),
    'match',
  );
  assert.equal(
    compareSavedPolicyCategory(POLICY, {
      region: null,
      age: null,
      category: 'finance',
    }),
    'mismatch',
  );
});

test('getEligibilityCategoryLabel은 W4-G0 category label을 반환한다', () => {
  assert.equal(getEligibilityCategoryLabel('age'), '연령');
  assert.equal(getEligibilityCategoryLabel('custom'), 'custom');
});

test('truncateEligibilityText는 긴 문장을 잘라낸다', () => {
  const longText = '가'.repeat(150);
  const truncated = truncateEligibilityText(longText, 120);

  assert.equal(truncated.endsWith('…'), true);
  assert.equal(shouldExpandEligibilityText(longText, 120), true);
});

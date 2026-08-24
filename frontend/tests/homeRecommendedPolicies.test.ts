import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto } from '../src/types/policy.js';
import type { RecommendationItemDto } from '../src/types/recommendation.js';
import {
  buildHomeRecommendationRequest,
  hasHomeSavedConditions,
  mapHomeRecommendationItemsToPolicies,
  pickHomeFallbackPolicies,
} from '../src/utils/homeRecommendedPolicies.js';

function createPolicy(overrides: Partial<PolicyDto> = {}): PolicyDto {
  return {
    schema_version: '1.2.0',
    source_id: 'seed',
    source_name: 'seed',
    external_id: 'ext-1',
    title: '테스트 정책',
    organization: null,
    summary: null,
    category_text: null,
    categories: ['welfare'],
    application_period_text: null,
    application_start: '2026-01-01',
    application_end: '2026-12-31',
    application_schedule: 'fixed_period',
    application_status: 'open',
    region_text: null,
    regions: ['서울'],
    age_min: 19,
    age_max: 39,
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
    collected_at: '2026-01-01T00:00:00.000Z',
    data_quality_status: 'valid',
    id: 1,
    created_at: '2026-01-01T00:00:00.000Z',
    updated_at: '2026-01-01T00:00:00.000Z',
    ...overrides,
  };
}

function createRecommendationItem(
  overrides: Partial<RecommendationItemDto> = {},
): RecommendationItemDto {
  return {
    id: 1,
    source_id: 'seed',
    external_id: 'ext-1',
    title: '추천 정책',
    lead: null,
    category: 'welfare',
    regions: ['서울'],
    min_age: 19,
    max_age: 39,
    application_start: '2026-01-01',
    application_end: '2026-12-31',
    application_status: 'open',
    data_quality_status: 'valid',
    score: 10,
    reasons: [],
    unknown_conditions: [],
    disclaimer: 'disclaimer',
    ...overrides,
  };
}

test('hasHomeSavedConditions는 region·age·category 중 하나라도 있으면 true', () => {
  assert.equal(hasHomeSavedConditions(null), false);
  assert.equal(
    hasHomeSavedConditions({ region: null, age: null, category: null }),
    false,
  );
  assert.equal(
    hasHomeSavedConditions({ region: '서울', age: null, category: null }),
    true,
  );
});

test('buildHomeRecommendationRequest는 공식 프로필 필드만 사용한다', () => {
  const request = buildHomeRecommendationRequest({
    region: '서울',
    age: 25,
    category: 'housing',
  });

  assert.deepEqual(request, {
    region: '서울',
    age: 25,
    category: 'housing',
    include_partial: false,
    limit: 12,
  });
});

test('pickHomeFallbackPolicies는 closed·scheduled·지난 마감을 제외한다', () => {
  const referenceDate = new Date('2026-08-01T00:00:00+09:00');
  const policies = [
    createPolicy({ id: 1, application_status: 'closed' }),
    createPolicy({
      id: 2,
      application_status: 'open',
      application_schedule: 'always',
    }),
    createPolicy({ id: 3, application_status: 'scheduled' }),
    createPolicy({
      id: 4,
      application_status: 'open',
      application_end: '2026-07-01',
    }),
    createPolicy({ id: 5, application_status: 'open' }),
  ];

  const picked = pickHomeFallbackPolicies(policies, 3, referenceDate);

  assert.deepEqual(
    picked.map((policy) => policy.id),
    [2, 5],
  );
});

test('mapHomeRecommendationItemsToPolicies는 closed 항목을 제외한다', () => {
  const items = [
    createRecommendationItem({ id: 1, application_status: 'closed' }),
    createRecommendationItem({ id: 2, application_status: 'open' }),
    createRecommendationItem({
      id: 3,
      application_status: 'open',
      application_end: '2026-12-31',
    }),
  ];

  const mapped = mapHomeRecommendationItemsToPolicies(
    items,
    3,
    new Date('2026-08-01T00:00:00+09:00'),
  );

  assert.deepEqual(
    mapped.map((policy) => policy.id),
    [2, 3],
  );
});

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import test from 'node:test';
import { handleRecommendationMock } from '../src/mocks/recommendationHandlers.js';
import {
  MOCK_RECOMMENDATION_EMPTY_REGION,
  MOCK_RECOMMENDATION_EVALUATED_AT,
} from '../src/mocks/recommendationFixtures.js';
import {
  createMockPolicies,
  type SeedPolicyProgram,
} from '../src/mocks/policyContract.js';
import {
  RECOMMENDATION_APP_ROUTE,
  RECOMMENDATION_DEFAULT_DISCLAIMER,
  RECOMMENDATION_ENDPOINTS,
  resolveRecommendationRequest,
} from '../src/types/recommendation.js';

const seedPath = resolve(
  process.cwd(),
  '..',
  'data',
  'seeds',
  'initial_programs.json',
);
const seedPrograms = JSON.parse(
  readFileSync(seedPath, 'utf8'),
) as SeedPolicyProgram[];
const mockPolicies = createMockPolicies(seedPrograms);

test('Recommendation API endpoint는 Backend draft POST·GET 경로와 일치한다', () => {
  assert.equal(RECOMMENDATION_ENDPOINTS.post.path, '/api/v1/recommendations');
  assert.equal(
    RECOMMENDATION_ENDPOINTS.get.path,
    '/api/v1/policies/recommendations',
  );
  assert.equal(RECOMMENDATION_APP_ROUTE, '/recommendations');
  assert.notEqual(RECOMMENDATION_APP_ROUTE, '/search');
});

test('handleRecommendationMock는 200 응답 envelope와 disclaimer를 반환한다', () => {
  const result = handleRecommendationMock(
    { age: 25, region: '서울특별시', limit: 5 },
    mockPolicies,
  );

  assert.equal(result.status, 200);
  if (result.status === 200) {
    assert.ok(Array.isArray(result.body.items));
    assert.equal(typeof result.body.total, 'number');
    assert.equal(result.body.evaluated_at, MOCK_RECOMMENDATION_EVALUATED_AT);
    assert.ok(result.body.items.length <= 5);

    for (const item of result.body.items) {
      assert.equal(typeof item.id, 'number');
      assert.equal(typeof item.score, 'number');
      assert.ok(Array.isArray(item.reasons));
      assert.ok(Array.isArray(item.unknown_conditions));
      assert.equal(item.disclaimer, RECOMMENDATION_DEFAULT_DISCLAIMER);
      assert.ok(item.disclaimer.includes('자격을 확정하지 않으며'));
    }
  }
});

test('handleRecommendationMock는 MOCK_EMPTY region으로 empty 200을 반환한다', () => {
  const result = handleRecommendationMock(
    { region: MOCK_RECOMMENDATION_EMPTY_REGION },
    mockPolicies,
  );

  assert.equal(result.status, 200);
  if (result.status === 200) {
    assert.equal(result.body.total, 0);
    assert.deepEqual(result.body.items, []);
  }
});

test('handleRecommendationMock는 age·limit 경계 위반 시 422를 반환한다', () => {
  const ageResult = handleRecommendationMock({ age: 121 }, mockPolicies);
  assert.equal(ageResult.status, 422);
  if (ageResult.status === 422) {
    assert.equal(typeof ageResult.body.detail, 'string');
  }

  const limitResult = handleRecommendationMock({ limit: 51 }, mockPolicies);
  assert.equal(limitResult.status, 422);
});

test('resolveRecommendationRequest는 기본 include_partial=false·limit=10을 적용한다', () => {
  assert.deepEqual(resolveRecommendationRequest({}), {
    include_partial: false,
    limit: 10,
  });
});

test('Mock 추천 정렬은 score DESC, id ASC를 따른다', () => {
  const result = handleRecommendationMock({ limit: 50 }, mockPolicies);
  assert.equal(result.status, 200);

  if (result.status === 200 && result.body.items.length >= 2) {
    for (let index = 0; index < result.body.items.length - 1; index += 1) {
      const left = result.body.items[index];
      const right = result.body.items[index + 1];

      assert.ok(
        left.score > right.score ||
          (left.score === right.score && left.id <= right.id),
      );
    }
  }
});

test('Recommendation item DTO는 PolicySearch hit nested shape와 분리된다', () => {
  const result = handleRecommendationMock({ limit: 1 }, mockPolicies);
  assert.equal(result.status, 200);

  if (result.status === 200 && result.body.items[0]) {
    const item = result.body.items[0];
    assert.equal('policy' in item, false);
    assert.equal('verdicts' in item, false);
    assert.equal('reason_codes' in item, false);
    assert.equal(typeof item.category, 'string');
    assert.equal(typeof item.lead, 'string');
  }
});

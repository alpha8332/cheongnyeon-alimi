import assert from 'node:assert/strict';
import test from 'node:test';
import type { RecommendationItemDto } from '../src/types/recommendation.js';
import {
  normalizeRecommendationCategory,
  recommendationItemToPolicyDto,
} from '../src/utils/recommendationPolicyMapping.js';

function createRecommendationItem(
  overrides: Partial<RecommendationItemDto> = {},
): RecommendationItemDto {
  return {
    id: 1,
    source_id: 'public-bootstrap',
    external_id: 'external-1',
    title: '테스트 정책',
    lead: null,
    category: '기타',
    regions: ['전국'],
    min_age: null,
    max_age: null,
    application_start: null,
    application_end: null,
    application_status: 'unknown',
    data_quality_status: 'partial',
    score: 0,
    reasons: [],
    unknown_conditions: [],
    disclaimer: '공식 원문을 확인하세요.',
    ...overrides,
  };
}

test('알 수 없는 추천 category는 other UI theme으로 정규화한다', () => {
  assert.equal(normalizeRecommendationCategory('기타'), 'other');
  assert.equal(normalizeRecommendationCategory('housing'), 'housing');
});

test('공개 bootstrap의 unknown 상태를 안전한 PolicyDto로 변환한다', () => {
  const policy = recommendationItemToPolicyDto(createRecommendationItem());

  assert.deepEqual(policy.categories, ['other']);
  assert.equal(policy.application_status, null);
  assert.equal(policy.application_schedule, null);
  assert.equal(policy.data_quality_status, 'partial');
});

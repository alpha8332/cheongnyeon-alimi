import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildProgramDetailRoutePath,
  buildRecommendationItemDetailPath,
} from '../src/utils/policyDetailNavigation.js';
import type { RecommendationItemDto } from '../src/types/recommendation.js';

test('buildRecommendationItemDetailPath는 partial item에 include_partial query를 붙인다', () => {
  const item = {
    id: 42,
    data_quality_status: 'partial',
  } as RecommendationItemDto;

  assert.equal(
    buildRecommendationItemDetailPath(item),
    '/programs/42?include_partial=true',
  );
});

test('buildRecommendationItemDetailPath와 buildProgramDetailRoutePath는 동일 id를 공유한다', () => {
  const item = {
    id: 7,
    data_quality_status: 'complete',
  } as RecommendationItemDto;

  assert.equal(
    buildRecommendationItemDetailPath(item),
    buildProgramDetailRoutePath(7),
  );
});

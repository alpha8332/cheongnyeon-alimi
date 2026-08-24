import assert from 'node:assert/strict';
import test from 'node:test';
import { RecommendationApiError } from '../src/api/recommendationApiError.js';
import {
  isRecommendationEmptyResults,
  mapRecommendationEmptyResults,
  mapRecommendationError,
} from '../src/utils/recommendationErrors.js';

test('mapRecommendationError는 422 validation presentation을 반환한다', () => {
  const presentation = mapRecommendationError(
    new RecommendationApiError(422, 'age must be between 0 and 120'),
  );

  assert.equal(presentation.kind, 'validation');
  assert.equal(presentation.retryable, false);
  assert.match(presentation.message, /age must be between 0 and 120/);
});

test('mapRecommendationError는 5xx server presentation과 retryable을 반환한다', () => {
  const presentation = mapRecommendationError(
    new RecommendationApiError(503, 'service unavailable'),
  );

  assert.equal(presentation.kind, 'server');
  assert.equal(presentation.retryable, true);
});

test('mapRecommendationEmptyResults는 empty_results kind를 반환한다', () => {
  const presentation = mapRecommendationEmptyResults();

  assert.equal(presentation.kind, 'empty_results');
  assert.equal(presentation.retryable, false);
  assert.match(presentation.message, /자격 충족/);
});

test('isRecommendationEmptyResults는 total 0과 빈 items를 감지한다', () => {
  assert.equal(
    isRecommendationEmptyResults({ items: [], total: 0, evaluated_at: '2026-01-01' }),
    true,
  );
  assert.equal(
    isRecommendationEmptyResults({
      items: [{ id: 1 } as never],
      total: 1,
      evaluated_at: '2026-01-01',
    }),
    false,
  );
});

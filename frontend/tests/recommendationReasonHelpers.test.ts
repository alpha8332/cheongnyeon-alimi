import assert from 'node:assert/strict';
import test from 'node:test';
import type { RecommendationItemDto, RecommendationResponse } from '../src/types/recommendation.js';
import {
  buildRecommendationQueryWarningMessage,
  countRecommendationUnconfirmedRegionItems,
  countRecommendationUnknownItems,
  formatRecommendationAge,
  formatRecommendationReasonSummary,
  hasQueryLevelRecommendationWarnings,
  hasRecommendationUnknownConditions,
  hasRecommendationUnconfirmedRegion,
} from '../src/utils/recommendationReasonHelpers.js';

function createItem(
  overrides: Partial<RecommendationItemDto> = {},
): RecommendationItemDto {
  return {
    id: 1,
    source_id: 'seed',
    external_id: 'ext-1',
    title: '테스트 정책',
    lead: null,
    category: 'finance',
    regions: ['서울특별시'],
    min_age: 19,
    max_age: 39,
    application_start: null,
    application_end: '2026-12-31',
    application_status: 'open',
    data_quality_status: 'complete',
    score: 10,
    reasons: [{ code: 'MATCHED_REGION', label: '지역 조건이 일치합니다.' }],
    unknown_conditions: [],
    disclaimer: 'disclaimer',
    ...overrides,
  };
}

test('formatRecommendationReasonSummary는 reason label을 연결한다', () => {
  const summary = formatRecommendationReasonSummary(createItem());

  assert.match(summary, /지역 조건/);
});

test('formatRecommendationAge는 제한 없음과 0 sentinel을 구분한다', () => {
  assert.equal(
    formatRecommendationAge(
      createItem({
        min_age: null,
        max_age: null,
        reasons: [{ code: 'AGE_UNRESTRICTED', label: '연령 제한 없음' }],
      }),
    ),
    '연령 제한 없음',
  );
  assert.equal(
    formatRecommendationAge(createItem({ min_age: 0, max_age: 0 })),
    '연령 정보 없음',
  );
});

test('hasRecommendationUnknownConditions는 unknown_conditions 유무를 판별한다', () => {
  assert.equal(hasRecommendationUnknownConditions(createItem()), false);
  assert.equal(
    hasRecommendationUnknownConditions(
      createItem({ unknown_conditions: ['원문 확인 필요'] }),
    ),
    true,
  );
});

test('hasQueryLevelRecommendationWarnings는 response item 중 unknown을 감지한다', () => {
  const response: RecommendationResponse = {
    items: [createItem({ unknown_conditions: ['partial'] })],
    total: 1,
    evaluated_at: '2026-01-01',
  };

  assert.equal(hasQueryLevelRecommendationWarnings(response), true);
  assert.equal(countRecommendationUnknownItems(response), 1);
  assert.match(buildRecommendationQueryWarningMessage(response), /1건/);
});

test('지역 미확정 추천은 지역 정책으로 단정하지 않는 안내를 만든다', () => {
  const item = createItem({
    regions: [],
    reasons: [{ code: 'REGION_UNCONFIRMED', label: '거주지 일치 미확인' }],
    unknown_conditions: ['지역 제한 근거가 없습니다.'],
  });
  const response: RecommendationResponse = {
    items: [item],
    total: 1,
    evaluated_at: '2026-01-01',
  };

  assert.equal(hasRecommendationUnconfirmedRegion(item), true);
  assert.equal(countRecommendationUnconfirmedRegionItems(response), 1);
  assert.match(formatRecommendationReasonSummary(item), /거주지 일치 미확인/);
  assert.match(buildRecommendationQueryWarningMessage(response), /해당 지역 정책으로 확인된 결과가 아닙니다/);
});

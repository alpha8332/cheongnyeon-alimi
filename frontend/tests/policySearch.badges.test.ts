import assert from 'node:assert/strict';
import test from 'node:test';
import {
  MATCH_VERDICT_LABELS,
  PARTIAL_QUALITY_BADGE_LABEL,
  UNKNOWN_ELIGIBILITY_BADGE_LABEL,
  formatUnconfirmedConditionsTooltip,
  hasUnconfirmedConditions,
  hasUnknownVerdicts,
} from '../src/constants/policySearchDisplayHelpers.js';

test('partial 품질 배지와 unknown 판정 배지 라벨은 구분된다', () => {
  assert.notEqual(PARTIAL_QUALITY_BADGE_LABEL, MATCH_VERDICT_LABELS.unknown);
  assert.equal(PARTIAL_QUALITY_BADGE_LABEL, '정보 일부 누락');
  assert.equal(MATCH_VERDICT_LABELS.unknown, '정보 미확인');
});

test('hasUnknownVerdicts는 unknown_count > 0일 때 true', () => {
  assert.equal(hasUnknownVerdicts({ unknown_count: 0 }), false);
  assert.equal(hasUnknownVerdicts({ unknown_count: 2 }), true);
});

test('hasUnconfirmedConditions는 unconfirmed_conditions 존재 여부를 반환한다', () => {
  assert.equal(
    hasUnconfirmedConditions({ unconfirmed_conditions: [] }),
    false,
  );
  assert.equal(
    hasUnconfirmedConditions({
      unconfirmed_conditions: [
        {
          field: 'region',
          reason_code: 'DATA_MISSING_REGION',
          message: '지역 정보가 없습니다.',
        },
      ],
    }),
    true,
  );
});

test('formatUnconfirmedConditionsTooltip은 row alert tooltip copy를 조합한다', () => {
  const tooltip = formatUnconfirmedConditionsTooltip([
    {
      field: 'region',
      reason_code: 'DATA_MISSING_REGION',
      message: '지역 정보가 없습니다.',
    },
    {
      field: 'age',
      reason_code: 'DATA_MISSING_AGE',
      message: '연령 정보가 없습니다.',
    },
  ]);

  assert.match(tooltip, /지역 정보가 없습니다/);
  assert.match(tooltip, /연령 정보가 없습니다/);
  assert.equal(UNKNOWN_ELIGIBILITY_BADGE_LABEL, '자격요건 직접 확인 필요');
});

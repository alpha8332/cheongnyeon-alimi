import assert from 'node:assert/strict';
import test from 'node:test';
import { buildSavedConditionSearchPreferences } from '../src/utils/policySearchSavedConditions.js';

test('저장 조건은 검색 필터가 아닌 복수 분야 선호도로 변환된다', () => {
  assert.deepEqual(
    buildSavedConditionSearchPreferences({
      region: '천안시',
      age: 24,
      category: 'housing',
      categories: ['housing', 'finance'],
    }),
    {
      region: '천안시',
      age: 24,
      categories: ['housing', 'finance'],
    },
  );
});

test('예시 검색은 저장된 프로필 선호도를 적용하지 않는다', () => {
  assert.equal(
    buildSavedConditionSearchPreferences(
      {
      region: '경상남도',
      age: 25,
      category: 'housing',
      categories: ['housing'],
      },
      false,
    ),
    null,
  );
});

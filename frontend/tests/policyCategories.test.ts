import assert from 'node:assert/strict';
import test from 'node:test';
import { getPolicyCategoryDisplayOrder } from '../src/utils/policyDisplay.js';

test('복수 분야 정책은 모든 분야를 원래 순서대로 표시한다', () => {
  assert.deepEqual(
    getPolicyCategoryDisplayOrder({
      categories: ['welfare', 'housing', 'finance'],
    }),
    ['welfare', 'housing', 'finance'],
  );
});

test('필터 분야가 복수 categories에 있으면 첫 배지로 표시한다', () => {
  assert.deepEqual(
    getPolicyCategoryDisplayOrder(
      { categories: ['welfare', 'housing', 'finance'] },
      'housing',
    ),
    ['housing', 'welfare', 'finance'],
  );
});

test('categories가 비어 있으면 기타 배지를 표시한다', () => {
  assert.deepEqual(getPolicyCategoryDisplayOrder({ categories: [] }), ['other']);
});

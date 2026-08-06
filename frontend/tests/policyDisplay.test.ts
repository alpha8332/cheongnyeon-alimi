import assert from 'node:assert/strict';
import test from 'node:test';
import { formatCollectedAt } from '../src/utils/policyDisplay.js';

test('collected_at을 한국 표준시로 표시한다', () => {
  assert.equal(
    formatCollectedAt('2026-08-06T00:30:00Z'),
    '2026-08-06 09:30 KST',
  );
});

test('잘못된 collected_at은 미확인으로 표시한다', () => {
  assert.equal(formatCollectedAt('not-a-date'), '수집 시각 미확인');
});

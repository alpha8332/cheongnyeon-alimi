import assert from 'node:assert/strict';
import test from 'node:test';
import {
  formatCollectionRunCounts,
  getCollectionRunStatusLabel,
  isTerminalCollectionRunStatus,
} from '../src/utils/collectionRunDisplay.js';

test('getCollectionRunStatusLabel은 Backend status enum label을 반환한다', () => {
  assert.equal(getCollectionRunStatusLabel('running'), '실행 중');
  assert.equal(getCollectionRunStatusLabel('partial_failure'), '부분 실패');
});

test('isTerminalCollectionRunStatus는 running만 non-terminal이다', () => {
  assert.equal(isTerminalCollectionRunStatus('running'), false);
  assert.equal(isTerminalCollectionRunStatus('failed'), true);
});

test('formatCollectionRunCounts는 list subset counts를 포맷한다', () => {
  assert.equal(formatCollectionRunCounts(1, 2, 3), '삽입 1 · 갱신 2 · 실패 3');
});

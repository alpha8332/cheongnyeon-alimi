import assert from 'node:assert/strict';
import test from 'node:test';
import { EMPTY_PROGRAM_FILTERS } from '../src/utils/policyFilters.js';

test('정책 목록은 공개 bootstrap의 partial 정책을 기본 포함한다', () => {
  assert.equal(EMPTY_PROGRAM_FILTERS.includePartial, true);
});

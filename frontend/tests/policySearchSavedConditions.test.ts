import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicySearchUrlQueryState } from '../src/types/policySearchUrlState.js';
import { mergeSavedConditionsIntoSearchState } from '../src/utils/policySearchSavedConditions.js';

const BASE_STATE = {
  q: '청년 정책',
  include_partial: true,
  page: 1,
  limit: 20,
} satisfies PolicySearchUrlQueryState;

test('mergeSavedConditionsIntoSearchState는 q가 없으면 URL state를 그대로 둔다', () => {
  const emptyQ = { ...BASE_STATE, q: '' };
  const saved = { region: '천안시', age: 24, category: null };

  assert.deepEqual(
    mergeSavedConditionsIntoSearchState(emptyQ, saved),
    emptyQ,
  );
});

test('mergeSavedConditionsIntoSearchState는 URL에 없는 flat filter를 프로필에서 채운다', () => {
  const saved = {
    region: '천안시',
    age: 24,
    category: 'housing' as const,
  };

  const merged = mergeSavedConditionsIntoSearchState(BASE_STATE, saved);

  assert.equal(merged.region, '천안시');
  assert.equal(merged.age, 24);
  assert.equal(merged.category, 'housing');
});

test('mergeSavedConditionsIntoSearchState는 URL explicit filter를 덮어쓰지 않는다', () => {
  const saved = {
    region: '천안시',
    age: 24,
    category: 'housing' as const,
  };
  const withUrlFilters = {
    ...BASE_STATE,
    region: '서울특별시',
    age: 30,
    category: 'finance' as const,
  } satisfies PolicySearchUrlQueryState;

  const merged = mergeSavedConditionsIntoSearchState(withUrlFilters, saved);

  assert.equal(merged.region, '서울특별시');
  assert.equal(merged.age, 30);
  assert.equal(merged.category, 'finance');
});

test('검색어에 분야가 명시되면 저장된 분야보다 검색 의도를 우선한다', () => {
  const merged = mergeSavedConditionsIntoSearchState(
    { ...BASE_STATE, q: '천안 취업' },
    { region: null, age: 24, category: 'housing' },
  );

  assert.equal(merged.category, null);
  assert.equal(merged.age, 24);
});

test('예시 검색은 저장된 프로필 조건을 강제 필터로 합치지 않는다', () => {
  const exampleState = {
    ...BASE_STATE,
    q: '천안 취업',
    use_saved_conditions: false,
  } satisfies PolicySearchUrlQueryState;

  assert.deepEqual(
    mergeSavedConditionsIntoSearchState(exampleState, {
      region: '경상남도',
      age: 25,
      category: 'housing',
    }),
    exampleState,
  );
});

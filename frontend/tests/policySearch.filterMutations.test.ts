import assert from 'node:assert/strict';
import test from 'node:test';
import {
  hasPolicySearchFilterParam,
  removePolicySearchFilter,
  updatePolicySearchFilter,
} from '../src/utils/policySearchFilterMutations.js';

const baseState = {
  q: '서울 주거',
  keyword: '주거',
  region: '서울특별시',
  age: 25,
  category: 'housing' as const,
  status: 'open' as const,
  include_partial: true,
  page: 3,
  limit: 20,
  sort: 'default' as const,
};

test('hasPolicySearchFilterParam은 URL flat filter 존재 여부를 판별한다', () => {
  assert.equal(hasPolicySearchFilterParam(baseState, 'region'), true);
  assert.equal(hasPolicySearchFilterParam(baseState, 'include_partial'), false);
  assert.equal(
    hasPolicySearchFilterParam(
      { ...baseState, include_partial: false },
      'include_partial',
    ),
    true,
  );
});

test('removePolicySearchFilter는 flat param 제거와 page=1 reset을 함께 적용한다', () => {
  const next = removePolicySearchFilter(baseState, 'region');

  assert.equal(next.region, null);
  assert.equal(next.page, 1);
  assert.equal(next.q, '서울 주거');
});

test('updatePolicySearchFilter는 flat param 갱신과 page=1 reset을 함께 적용한다', () => {
  const next = updatePolicySearchFilter(baseState, 'age', 29);

  assert.equal(next.age, 29);
  assert.equal(next.page, 1);
  assert.equal(next.region, '서울특별시');
});

test('removePolicySearchFilter include_partial는 기본값 true로 복원한다', () => {
  const next = removePolicySearchFilter(
    { ...baseState, include_partial: false },
    'include_partial',
  );

  assert.equal(next.include_partial, true);
  assert.equal(next.page, 1);
});

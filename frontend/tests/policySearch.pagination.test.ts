import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildPolicySearchPageNumbers,
  getPolicySearchTotalPages,
  isPolicySearchResponseCurrent,
  withPolicySearchPage,
} from '../src/utils/policySearchPagination.js';

test('getPolicySearchTotalPages는 total/limit envelope로 총 페이지 수를 계산한다', () => {
  assert.equal(getPolicySearchTotalPages(0, 20), 1);
  assert.equal(getPolicySearchTotalPages(20, 20), 1);
  assert.equal(getPolicySearchTotalPages(21, 20), 2);
  assert.equal(getPolicySearchTotalPages(45, 20), 3);
});

test('withPolicySearchPage는 page를 1 이상으로 유지한다', () => {
  const base = {
    q: '청년',
    include_partial: true,
    page: 1,
    limit: 20,
  };

  assert.deepEqual(withPolicySearchPage(base, 3), { ...base, page: 3 });
  assert.deepEqual(withPolicySearchPage(base, 0), { ...base, page: 1 });
  assert.deepEqual(withPolicySearchPage(base, -1), { ...base, page: 1 });
});

test('isPolicySearchResponseCurrent는 page/limit 불일치 stale 응답을 감지한다', () => {
  assert.equal(
    isPolicySearchResponseCurrent(
      { page: 2, limit: 20 },
      { page: 2, limit: 20 },
    ),
    true,
  );
  assert.equal(
    isPolicySearchResponseCurrent(
      { page: 1, limit: 20 },
      { page: 2, limit: 20 },
    ),
    false,
  );
  assert.equal(
    isPolicySearchResponseCurrent(
      { page: 2, limit: 10 },
      { page: 2, limit: 20 },
    ),
    false,
  );
});

test('buildPolicySearchPageNumbers는 7페이지 이하에서 전체 범위를 반환한다', () => {
  assert.deepEqual(buildPolicySearchPageNumbers(1, 5), [1, 2, 3, 4, 5]);
});

test('buildPolicySearchPageNumbers는 긴 범위에서 현재 페이지 주변을 포함한다', () => {
  assert.deepEqual(buildPolicySearchPageNumbers(5, 10), [1, 4, 5, 6, 10]);
  assert.deepEqual(buildPolicySearchPageNumbers(1, 10), [1, 2, 3, 10]);
  assert.deepEqual(buildPolicySearchPageNumbers(10, 10), [1, 8, 9, 10]);
});

test('withPolicySearchPage는 검색어 변경 시 page=1 재설정 패턴을 지원한다', () => {
  const paged = {
    q: '전국 청년',
    region: '서울특별시',
    include_partial: true,
    page: 3,
    limit: 20,
  };
  const afterNewSearch = withPolicySearchPage(
    {
      ...paged,
      q: '25세 일자리',
    },
    1,
  );

  assert.equal(afterNewSearch.q, '25세 일자리');
  assert.equal(afterNewSearch.region, '서울특별시');
  assert.equal(afterNewSearch.page, 1);
});

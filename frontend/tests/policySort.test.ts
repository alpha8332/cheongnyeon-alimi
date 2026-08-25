import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto, PolicySort } from '../src/types/policy.js';
import { sortByPolicy } from '../src/utils/policySort.js';

function policy(
  id: number,
  title: string,
  applicationEnd: string | null,
  collectedAt: string,
): PolicyDto {
  return {
    id,
    title,
    application_end: applicationEnd,
    collected_at: collectedAt,
  } as PolicyDto;
}

const policies = [
  policy(1, '나 정책', '2026-09-02', '2026-08-20T00:00:00Z'),
  policy(2, '가 정책', null, '2026-08-22T00:00:00Z'),
  policy(3, '다 정책', '2026-08-30', '2026-08-21T00:00:00Z'),
];

function ids(sort: PolicySort): number[] {
  return sortByPolicy(policies, (item) => item, sort).map((item) => item.id);
}

test('정책 정렬은 가나다·마감·수집 순서를 결정적으로 적용한다', () => {
  assert.deepEqual(ids('title_asc'), [2, 1, 3]);
  assert.deepEqual(ids('title_desc'), [3, 1, 2]);
  assert.deepEqual(ids('deadline_asc'), [3, 1, 2]);
  assert.deepEqual(ids('deadline_desc'), [1, 3, 2]);
  assert.deepEqual(ids('collected_desc'), [2, 3, 1]);
  assert.deepEqual(ids('collected_asc'), [1, 3, 2]);
});

test('마감일 미확정 정책은 마감 양방향 정렬에서 항상 뒤에 둔다', () => {
  assert.equal(ids('deadline_asc').at(-1), 2);
  assert.equal(ids('deadline_desc').at(-1), 2);
});

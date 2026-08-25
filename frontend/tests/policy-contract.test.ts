import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import test from 'node:test';
import {
  buildPolicyDetailPath,
  POLICY_COLLECTION_PATH,
  resolvePolicyListQuery,
} from '../src/api/policyRequest.js';
import {
  createMockPolicies,
  createMockPolicyDetails,
  createMockPolicyListResponse,
  findMockPolicyById,
  type SeedPolicyProgram,
} from '../src/mocks/policyContract.js';
import { parsePolicyId } from '../src/utils/policyId.js';

const seedPath = resolve(
  process.cwd(),
  '..',
  'data',
  'seeds',
  'initial_programs.json',
);
const seedPrograms = JSON.parse(
  readFileSync(seedPath, 'utf8'),
) as SeedPolicyProgram[];
const policies = createMockPolicies(seedPrograms);
const policyDetails = createMockPolicyDetails(seedPrograms);

test('canonical Seed를 provenance 없는 공개 PolicyDto로 변환한다', () => {
  assert.equal(policies.length, 4);
  assert.deepEqual(
    policies.map((policy) => policy.id),
    [1, 2, 3, 4],
  );

  for (const policy of policies) {
    assert.equal('provenance' in policy, false);
    assert.equal('keywords' in policy, false);
    assert.equal('life_stages' in policy, false);
    assert.equal('target_groups' in policy, false);
    assert.equal('coverage_scope' in policy, false);
    assert.equal('region_rules' in policy, false);
    assert.equal('eligibility_summary' in policy, false);
    assert.notEqual(policy.data_quality_status, 'invalid');
    assert.match(policy.created_at, /Z$/);
    assert.match(policy.updated_at, /Z$/);
  }
});

test('기본 목록은 valid만 pagination envelope로 반환한다', () => {
  const query = resolvePolicyListQuery();
  const response = createMockPolicyListResponse(policies, query);

  assert.deepEqual(
    {
      total: response.total,
      page: response.page,
      limit: response.limit,
      itemCount: response.items.length,
    },
    {
      total: 2,
      page: 1,
      limit: 10,
      itemCount: 2,
    },
  );
  assert.ok(
    response.items.every(
      (policy) => policy.data_quality_status === 'valid',
    ),
  );
});

test('partial opt-in과 필터·pagination을 Mock에서도 API와 동일하게 적용한다', () => {
  const allResponse = createMockPolicyListResponse(
    policies,
    resolvePolicyListQuery({
      page: 1,
      limit: 100,
      include_partial: true,
    }),
  );
  assert.equal(allResponse.total, 4);

  const filteredResponse = createMockPolicyListResponse(
    policies,
    resolvePolicyListQuery({
      page: 1,
      limit: 1,
      category: 'welfare',
      include_partial: true,
    }),
  );
  assert.equal(filteredResponse.total, 1);
  assert.equal(filteredResponse.items.length, 1);
  assert.ok(filteredResponse.items[0]?.categories.includes('welfare'));
  assert.equal(filteredResponse.items[0]?.external_id, 'SYN-YOUTH-002');

  const emptyPage = createMockPolicyListResponse(
    policies,
    resolvePolicyListQuery({
      page: 2,
      limit: 10,
    }),
  );
  assert.equal(emptyPage.total, 2);
  assert.deepEqual(emptyPage.items, []);
});

test('상세 조회는 숫자 id와 partial opt-in 경계를 사용한다', () => {
  const partialPolicy = policyDetails.find(
    (policy) => policy.data_quality_status === 'partial',
  );
  assert.ok(partialPolicy);

  assert.equal(findMockPolicyById(policyDetails, partialPolicy.id), null);
  assert.equal(
    findMockPolicyById(policyDetails, partialPolicy.id, true)?.id,
    partialPolicy.id,
  );
  assert.deepEqual(
    findMockPolicyById(policyDetails, partialPolicy.id, true)
      ?.eligibility_summary,
    seedPrograms[partialPolicy.id - 1]?.eligibility_summary,
  );
  assert.equal(findMockPolicyById(policyDetails, 999_999, true), null);
});

test('API endpoint와 route id는 Policy API 숫자 계약을 따른다', () => {
  assert.equal(POLICY_COLLECTION_PATH, '/api/v1/policies');
  assert.equal(buildPolicyDetailPath(42), '/api/v1/policies/42');
  assert.throws(() => buildPolicyDetailPath(0));

  assert.equal(parsePolicyId('42'), 42);
  assert.equal(parsePolicyId('source--external'), null);
  assert.equal(parsePolicyId('0'), null);
});

test('Mock과 실제 Client가 같은 query 범위를 사용한다', () => {
  assert.throws(() => resolvePolicyListQuery({ page: 0 }));
  assert.throws(() => resolvePolicyListQuery({ limit: 101 }));
  assert.throws(() => resolvePolicyListQuery({ region: '' }));

  assert.deepEqual(
    resolvePolicyListQuery({
      category: 'housing',
      region: '서울특별시',
      status: 'open',
      include_partial: true,
    }),
    {
      page: 1,
      limit: 10,
      category: 'housing',
      region: '서울특별시',
      status: 'open',
      include_partial: true,
      sort: 'default',
    },
  );

  assert.equal(
    resolvePolicyListQuery({ sort: 'deadline_asc' }).sort,
    'deadline_asc',
  );
  assert.throws(() =>
    resolvePolicyListQuery({ sort: 'raw_sql' as 'default' }),
  );
});

test('timezone offset이 달라도 collected_at을 같은 instant로 해석한다', () => {
  assert.equal(
    Date.parse('2026-07-30T09:00:00+09:00'),
    Date.parse('2026-07-30T00:00:00Z'),
  );
});

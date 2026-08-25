import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import test from 'node:test';
import {
  createMockPolicies,
  type SeedPolicyProgram,
} from '../src/mocks/policyContract.js';
import {
  countUnknownVerdicts,
  POLICY_SEARCH_SCENARIO_FIXTURES,
  type PolicySearchHitFixture,
  type PolicySearchScenarioFixture,
} from '../src/mocks/policySearchFixtures.js';
import { handlePolicySearchMock } from '../src/mocks/policySearchHandlers.js';
import { resolvePolicySearchQuery } from '../src/mocks/policySearchRequest.js';
import {
  POLICY_SEARCH_DEFAULTS,
  POLICY_SEARCH_ENDPOINT,
  POLICY_SEARCH_QUERY_LIMITS,
  type PolicySearchHit,
  type PolicySearchResponse,
} from '../src/types/policySearch.js';

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
const mockPolicies = createMockPolicies(seedPrograms);

function searchMock(
  input: Parameters<typeof handlePolicySearchMock>[0],
): ReturnType<typeof handlePolicySearchMock> {
  return handlePolicySearchMock(input, mockPolicies);
}

const fixturesDir = resolve(
  process.cwd(),
  'src/mocks/fixtures/policySearch',
);

interface ManifestScenario {
  id: string;
  fixture: string;
  query: string;
}

interface ManifestFile {
  endpoint: string;
  defaults: {
    include_partial: boolean;
    page: number;
    limit: number;
  };
  scenarios: ManifestScenario[];
}

interface ValidationFixtureFile {
  scenario: 'M5';
  description: string;
  expect: {
    status: 422;
    detail: string;
  };
}

const manifest = JSON.parse(
  readFileSync(resolve(fixturesDir, 'manifest.json'), 'utf8'),
) as ManifestFile;

const SCENARIO_QUERIES = {
  M1: { q: '서울 주거', region: '서울특별시' },
  M2: { q: '전국 청년' },
  M3: { q: '25세 일자리', age: 25 },
  M4: { q: '복지로 생활' },
  M5: { q: '   ' },
  M6: { q: '지원금', keyword: '지원금' },
} as const;

function loadScenarioFixture(
  filename: string,
): PolicySearchScenarioFixture | ValidationFixtureFile {
  return JSON.parse(
    readFileSync(resolve(fixturesDir, filename), 'utf8'),
  ) as PolicySearchScenarioFixture | ValidationFixtureFile;
}

function assertNestedHitContract(hit: PolicySearchHit): void {
  assert.equal(typeof hit.policy.id, 'number');
  assert.equal(typeof hit.score, 'number');
  assert.equal(typeof hit.message, 'string');
  assert.equal(typeof hit.unknown_count, 'number');
  assert.ok(Array.isArray(hit.reason_codes));
  assert.ok(Array.isArray(hit.unconfirmed_conditions));

  for (const unconfirmed of hit.unconfirmed_conditions) {
    assert.equal(typeof unconfirmed.field, 'string');
    assert.equal(typeof unconfirmed.reason_code, 'string');
    assert.equal(typeof unconfirmed.message, 'string');
  }

  assert.equal('provenance' in hit.policy, false);
  assert.equal('keywords' in hit.policy, false);
  assert.equal(hit.unknown_count, countUnknownVerdicts(hit.verdicts));
}

function assertSuccessEnvelope(body: PolicySearchResponse): void {
  assert.equal(typeof body.total, 'number');
  assert.equal(typeof body.page, 'number');
  assert.equal(typeof body.limit, 'number');
  assert.ok(Array.isArray(body.items));
  assert.equal(typeof body.interpreted_conditions.q_raw, 'string');
  assert.equal(typeof body.interpreted_conditions.q_clean, 'string');
  assert.ok(Array.isArray(body.interpreted_conditions.conditions));
  assert.ok(Array.isArray(body.interpreted_conditions.override_fields));
  assert.ok(Array.isArray(body.interpreted_conditions.uninterpreted_terms));

  for (const hit of body.items) {
    assertNestedHitContract(hit);
  }
}

function assertFixtureParity(
  tsFixture: PolicySearchScenarioFixture,
  jsonFixture: PolicySearchScenarioFixture,
): void {
  assert.equal(tsFixture.scenario, jsonFixture.scenario);
  assert.equal(tsFixture.total, jsonFixture.total);
  assert.deepEqual(
    tsFixture.interpreted_conditions,
    jsonFixture.interpreted_conditions,
  );
  assert.deepEqual(
    tsFixture.items.map(stripHitFixture),
    jsonFixture.items.map(stripHitFixture),
  );
}

function stripHitFixture(item: PolicySearchHitFixture): PolicySearchHitFixture {
  return {
    policy_id: item.policy_id,
    score: item.score,
    verdicts: item.verdicts,
    reason_codes: [...item.reason_codes],
    message: item.message,
    unconfirmed_conditions: item.unconfirmed_conditions.map((entry) => ({
      ...entry,
    })),
  };
}

test('Policy Search endpoint와 G1 default query 계약을 고정한다', () => {
  assert.equal(POLICY_SEARCH_ENDPOINT.method, 'GET');
  assert.equal(POLICY_SEARCH_ENDPOINT.preferenceMethod, 'POST');
  assert.equal(POLICY_SEARCH_ENDPOINT.path, '/api/v1/policies/search');

  assert.deepEqual(POLICY_SEARCH_DEFAULTS, {
    include_partial: true,
    page: 1,
    limit: 20,
    sort: 'default',
  });

  assert.deepEqual(manifest.defaults, POLICY_SEARCH_DEFAULTS);

  assert.deepEqual(resolvePolicySearchQuery({ q: '청년' }), {
    q: '청년',
    include_partial: true,
    page: 1,
    limit: 20,
    sort: 'default',
  });
});

test('flat query parameter resolve와 URLSearchParams 직렬화를 검증한다', () => {
  const params = new URLSearchParams({
    q: '서울 주거',
    region: '서울특별시',
    age: '25',
    category: 'housing',
    status: 'open',
    include_partial: 'false',
    page: '2',
    limit: '5',
  });

  assert.deepEqual(resolvePolicySearchQuery(params), {
    q: '서울 주거',
    region: '서울특별시',
    age: 25,
    category: 'housing',
    status: 'open',
    include_partial: false,
    page: 2,
    limit: 5,
    sort: 'default',
  });

  assert.deepEqual(resolvePolicySearchQuery({ q: '', category: 'housing' }), {
    q: '',
    category: 'housing',
    include_partial: true,
    page: 1,
    limit: 20,
    sort: 'default',
  });

  assert.throws(() => resolvePolicySearchQuery({ q: '   ' }));
  assert.throws(() => resolvePolicySearchQuery({ q: 'x', page: 0 }));
  assert.throws(() => resolvePolicySearchQuery({ q: 'x', limit: 101 }));
  assert.throws(() =>
    resolvePolicySearchQuery({ q: 'x', sort: 'raw_sql' as 'default' }),
  );
  assert.throws(() =>
    resolvePolicySearchQuery({ q: 'x'.repeat(POLICY_SEARCH_QUERY_LIMITS.q + 1) }),
  );
});

test('TS scenario registry와 JSON fixture가 M1~M4·M6에서 drift 없이 일치한다', () => {
  for (const entry of manifest.scenarios) {
    if (entry.id === 'M5') {
      continue;
    }

    const jsonFixture = loadScenarioFixture(entry.fixture);

    assert.notEqual('expect' in jsonFixture, true);
    const tsFixture = POLICY_SEARCH_SCENARIO_FIXTURES[entry.id as keyof typeof POLICY_SEARCH_SCENARIO_FIXTURES];
    assertFixtureParity(tsFixture, jsonFixture as PolicySearchScenarioFixture);
  }
});

test('handlePolicySearchMock M1~M4·M6가 nested PolicySearchResponse 계약을 만족한다', () => {
  for (const scenarioId of ['M1', 'M2', 'M3', 'M4', 'M6'] as const) {
    const result = searchMock(SCENARIO_QUERIES[scenarioId]);

    assert.equal(result.status, 200, `${scenarioId} should return 200`);
    assertSuccessEnvelope(result.body);

    const fixture = POLICY_SEARCH_SCENARIO_FIXTURES[scenarioId];
    assert.equal(result.body.total, fixture.total);
    assert.equal(result.body.page, POLICY_SEARCH_DEFAULTS.page);
    assert.equal(result.body.limit, POLICY_SEARCH_DEFAULTS.limit);
    assert.equal(result.body.items.length, fixture.items.length);
  }
});

test('M1 region match baseline과 M2 unknown mixed 시나리오를 검증한다', () => {
  const m1 = searchMock(SCENARIO_QUERIES.M1);
  assert.equal(m1.status, 200);
  assert.equal(m1.body.items[0]?.policy.external_id, 'SYN-YOUTH-001');
  assert.equal(m1.body.items[0]?.verdicts.region, 'match');
  assert.deepEqual(m1.body.interpreted_conditions.override_fields, ['region']);

  const m2 = searchMock(SCENARIO_QUERIES.M2);
  assert.equal(m2.status, 200);
  assert.equal(m2.body.total, 2);
  assert.ok(
    m2.body.items.some((hit: PolicySearchHit) => hit.verdicts.region === 'unknown'),
  );
  assert.ok(
    m2.body.items.some((hit: PolicySearchHit) => hit.unconfirmed_conditions.length > 0),
  );
});

test('M3 age match와 M4 partial-only multi-unknown 시나리오를 검증한다', () => {
  const m3 = searchMock(SCENARIO_QUERIES.M3);
  assert.equal(m3.status, 200);
  assert.equal(m3.body.items[0]?.verdicts.age, 'match');
  assert.equal(m3.body.interpreted_conditions.override_fields[0], 'age');

  const m4 = searchMock(SCENARIO_QUERIES.M4);
  assert.equal(m4.status, 200);
  assert.ok(
    m4.body.items.every(
      (hit: PolicySearchHit) => hit.policy.data_quality_status === 'partial',
    ),
  );
  assert.ok(
    m4.body.items.every((hit: PolicySearchHit) => hit.verdicts.region === 'unknown'),
  );
  assert.deepEqual(m4.body.interpreted_conditions.uninterpreted_terms, ['복지로']);
});

test('M5 empty q와 명시 조건 없음은 422 validation을 반환한다', () => {
  const m5Fixture = loadScenarioFixture('m5-empty-q.validation.json') as ValidationFixtureFile;
  const result = searchMock(SCENARIO_QUERIES.M5);

  assert.equal(result.status, 422);
  assert.equal(result.body.detail, m5Fixture.expect.detail);
});

test('M6 q+keyword explicit 시나리오와 pagination·include_partial 경계를 검증한다', () => {
  const m6 = searchMock(SCENARIO_QUERIES.M6);
  assert.equal(m6.status, 200);
  assert.deepEqual(m6.body.interpreted_conditions.override_fields, ['keyword']);
  assert.equal(m6.body.items[0]?.policy.data_quality_status, 'partial');

  const paged = searchMock({
    ...SCENARIO_QUERIES.M2,
    page: 1,
    limit: 1,
  });
  assert.equal(paged.status, 200);
  assert.equal(paged.body.total, 2);
  assert.equal(paged.body.limit, 1);
  assert.equal(paged.body.items.length, 1);

  const excludePartial = searchMock({
    ...SCENARIO_QUERIES.M4,
    include_partial: false,
  });
  assert.equal(excludePartial.status, 200);
  assert.equal(excludePartial.body.total, 0);
  assert.deepEqual(excludePartial.body.items, []);
});

test('등록되지 않은 query는 200 total=0 empty envelope를 반환한다', () => {
  const result = searchMock({ q: '존재하지 않는 검색어' });

  assert.equal(result.status, 200);
  assert.equal(result.body.total, 0);
  assert.deepEqual(result.body.items, []);
  assert.equal(result.body.limit, POLICY_SEARCH_DEFAULTS.limit);
});

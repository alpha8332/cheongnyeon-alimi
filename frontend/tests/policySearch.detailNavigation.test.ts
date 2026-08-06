import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildPolicySearchHitDetailPath,
  buildProgramDetailRoutePath,
  shouldPassIncludePartialOnDetail,
} from '../src/utils/policyDetailNavigation.js';
import type { PolicySearchHit } from '../src/types/policySearch.js';

function createHit(
  overrides: { id?: number; data_quality_status?: 'valid' | 'partial' } = {},
): PolicySearchHit {
  return {
    policy: {
      id: overrides.id ?? 42,
      data_quality_status: overrides.data_quality_status ?? 'valid',
    },
    score: 1,
    verdicts: {
      region: null,
      age: null,
      status: null,
      category: null,
    },
    unknown_count: 0,
    unconfirmed_conditions: [],
    reason_codes: [],
    message: '',
  } as unknown as PolicySearchHit;
}

test('buildProgramDetailRoutePath는 include_partial opt-in 쿼리를 붙인다', () => {
  assert.equal(buildProgramDetailRoutePath(7), '/programs/7');
  assert.equal(
    buildProgramDetailRoutePath(7, { includePartial: true }),
    '/programs/7?include_partial=true',
  );
});

test('shouldPassIncludePartialOnDetail은 partial hit 또는 search opt-in을 반영한다', () => {
  const validHit = createHit({ data_quality_status: 'valid' });
  const partialHit = createHit({ data_quality_status: 'partial' });

  assert.equal(shouldPassIncludePartialOnDetail(validHit, false), false);
  assert.equal(shouldPassIncludePartialOnDetail(validHit, true), true);
  assert.equal(shouldPassIncludePartialOnDetail(partialHit, false), true);
  assert.equal(shouldPassIncludePartialOnDetail(partialHit, true), true);
});

test('buildPolicySearchHitDetailPath는 hit id와 include_partial 조건을 조합한다', () => {
  const partialHit = createHit({ id: 99, data_quality_status: 'partial' });
  const validHit = createHit({ id: 100, data_quality_status: 'valid' });

  assert.equal(
    buildPolicySearchHitDetailPath(partialHit, false),
    '/programs/99?include_partial=true',
  );
  assert.equal(
    buildPolicySearchHitDetailPath(validHit, true),
    '/programs/100?include_partial=true',
  );
  assert.equal(
    buildPolicySearchHitDetailPath(validHit, false),
    '/programs/100',
  );
});

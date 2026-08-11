import assert from 'node:assert/strict';
import test from 'node:test';
import {
  assertEligibilitySummaryContract,
  isKnownEligibilityCategory,
} from '../src/mocks/eligibilitySummaryContract.js';
import {
  ELIGIBILITY_SUMMARY_FIXTURES,
  getEligibilitySummaryFixture,
  getMockPolicyDetailById,
  MOCK_ELIGIBILITY_POLICY_IDS,
  MOCK_POLICY_DETAIL_FIXTURES,
} from '../src/mocks/policyDetailFixtures.js';
import { ELIGIBILITY_SUMMARY_STATUSES } from '../src/types/eligibilitySummary.js';
import type { EligibilitySummaryDto } from '../src/types/eligibilitySummary.js';

test('ELIGIBILITY_SUMMARY_STATUSES는 Integration 08 W4-G0 후보와 일치한다', () => {
  assert.deepEqual([...ELIGIBILITY_SUMMARY_STATUSES], [
    'complete',
    'partial',
    'unknown',
  ]);
});

test('complete·partial·unknown eligibility summary fixture가 계약 검증을 통과한다', () => {
  for (const status of ELIGIBILITY_SUMMARY_STATUSES) {
    const fixture = getEligibilitySummaryFixture(status);
    assert.equal(fixture.status, status);
    assertEligibilitySummaryContract(fixture);
  }
});

test('MOCK_POLICY_DETAIL_FIXTURES는 status별 detail envelope 3건을 제공한다', () => {
  assert.equal(MOCK_POLICY_DETAIL_FIXTURES.length, 3);

  const statuses = new Set<EligibilitySummaryDto['status']>();

  for (const policy of MOCK_POLICY_DETAIL_FIXTURES) {
    assert.ok(policy.eligibility_summary);
    assertEligibilitySummaryContract(policy.eligibility_summary);
    statuses.add(policy.eligibility_summary.status);
  }

  assert.deepEqual([...statuses].sort(), ['complete', 'partial', 'unknown']);

  assert.equal(
    getMockPolicyDetailById(MOCK_ELIGIBILITY_POLICY_IDS.complete)?.eligibility_summary
      ?.status,
    'complete',
  );
  assert.equal(
    getMockPolicyDetailById(MOCK_ELIGIBILITY_POLICY_IDS.partial)?.eligibility_summary
      ?.status,
    'partial',
  );
  assert.equal(
    getMockPolicyDetailById(MOCK_ELIGIBILITY_POLICY_IDS.unknown)?.eligibility_summary
      ?.status,
    'unknown',
  );
});

test('complete fixture는 evidence가 있는 requirements와 documents를 포함한다', () => {
  const complete = ELIGIBILITY_SUMMARY_FIXTURES.complete;

  assert.ok(complete.requirements.length >= 1);
  assert.ok(complete.requirements.every((item) => item.evidence !== null));
  assert.ok(complete.required_documents.length >= 1);
  assert.equal(complete.unknown_conditions.length, 0);
});

test('partial fixture는 unknown_conditions와 evidence 없는 항목을 포함한다', () => {
  const partial = ELIGIBILITY_SUMMARY_FIXTURES.partial;

  assert.equal(partial.status, 'partial');
  assert.ok(partial.unknown_conditions.length >= 1);
  assert.ok(partial.requirements.some((item) => item.evidence === null));
});

test('unknown fixture는 구조화 배열이 비어 있고 unknown_conditions만 제공한다', () => {
  const unknown = ELIGIBILITY_SUMMARY_FIXTURES.unknown;

  assert.equal(unknown.status, 'unknown');
  assert.equal(unknown.requirements.length, 0);
  assert.equal(unknown.exclusions.length, 0);
  assert.equal(unknown.preferences.length, 0);
  assert.equal(unknown.required_documents.length, 0);
  assert.ok(unknown.unknown_conditions.length >= 1);
});

test('fixture category는 W4-G0 분류 집합 또는 other fallback을 사용한다', () => {
  for (const policy of MOCK_POLICY_DETAIL_FIXTURES) {
    const summary = policy.eligibility_summary;
    assert.ok(summary);

    for (const section of [
      summary.requirements,
      summary.exclusions,
      summary.preferences,
    ]) {
      for (const item of section) {
        assert.ok(
          isKnownEligibilityCategory(item.category) || item.category.length > 0,
          `category must be known or non-empty: ${item.category}`,
        );
      }
    }
  }
});

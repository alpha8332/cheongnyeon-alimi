import assert from 'node:assert/strict';
import test from 'node:test';
import { findMockPolicyById } from '../src/mocks/policyContract.js';
import {
  MOCK_ELIGIBILITY_POLICY_IDS,
  getMockPolicyDetailById,
} from '../src/mocks/policyDetailFixtures.js';

test('findMockPolicyById는 eligibility detail fixture id를 반환한다', () => {
  const complete = findMockPolicyById(
    [],
    MOCK_ELIGIBILITY_POLICY_IDS.complete,
  );

  assert.ok(complete);
  assert.equal(complete?.eligibility_summary?.status, 'complete');
  assert.equal(
    getMockPolicyDetailById(MOCK_ELIGIBILITY_POLICY_IDS.complete)?.id,
    complete?.id,
  );
});

test('findMockPolicyById는 unknown eligibility fixture를 반환한다', () => {
  const unknown = findMockPolicyById([], MOCK_ELIGIBILITY_POLICY_IDS.unknown);

  assert.ok(unknown);
  assert.equal(unknown?.eligibility_summary?.status, 'unknown');
});

import assert from 'node:assert/strict';
import test from 'node:test';
import { findMockPolicyById } from '../src/mocks/policyContract.js';
import type { PolicyDetailDto } from '../src/types/policy.js';

const mockPolicyDetails = [
  {
    id: 1,
    data_quality_status: 'valid',
    eligibility_summary: { coverage: 'complete' },
  },
  {
    id: 2,
    data_quality_status: 'partial',
    eligibility_summary: { coverage: 'partial' },
  },
] as unknown as PolicyDetailDto[];

test('findMockPolicyById는 1.2.0 eligibility detail을 반환한다', () => {
  const expected = mockPolicyDetails[0];
  assert.ok(expected);

  const detail = findMockPolicyById(
    mockPolicyDetails,
    expected.id,
    true,
  );

  assert.ok(detail);
  assert.equal(detail.id, expected.id);
  assert.equal(detail.eligibility_summary.coverage, expected.eligibility_summary.coverage);
});

test('findMockPolicyById는 partial 정책의 공개 여부를 지킨다', () => {
  const partial = mockPolicyDetails.find(
    (policy) => policy.data_quality_status === 'partial',
  );
  assert.ok(partial);

  assert.equal(findMockPolicyById(mockPolicyDetails, partial.id), null);
  assert.equal(
    findMockPolicyById(mockPolicyDetails, partial.id, true)?.id,
    partial.id,
  );
});

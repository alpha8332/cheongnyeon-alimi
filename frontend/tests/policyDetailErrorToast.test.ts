import assert from 'node:assert/strict';
import test from 'node:test';
import { PolicyDetailApiError } from '../src/api/policyDetailApiError.js';
import {
  buildPolicyDetailErrorToastDedupeKey,
  isPolicyDetailApiError,
  mapPolicyDetailErrorToToast,
} from '../src/utils/policyDetailErrorToast.js';

test('buildPolicyDetailErrorToastDedupeKey는 status·detail prefix를 사용한다', () => {
  assert.equal(
    buildPolicyDetailErrorToastDedupeKey(503, 'Service unavailable'),
    'policy-detail-503-Service unavailable',
  );
});

test('mapPolicyDetailErrorToToast는 5xx retryable Toast를 반환한다', () => {
  const toast = mapPolicyDetailErrorToToast(
    new PolicyDetailApiError(503, 'Service unavailable'),
  );

  assert.equal(toast.kind, 'error');
  assert.equal(toast.retryable, true);
});

test('mapPolicyDetailErrorToToast는 422 validation Toast를 반환한다', () => {
  const toast = mapPolicyDetailErrorToToast(
    new PolicyDetailApiError(422, 'include_partial is invalid'),
  );

  assert.equal(toast.kind, 'warning');
  assert.equal(toast.retryable, false);
});

test('isPolicyDetailApiError는 PolicyDetailApiError만 true를 반환한다', () => {
  assert.equal(
    isPolicyDetailApiError(new PolicyDetailApiError(503, 'fail')),
    true,
  );
  assert.equal(isPolicyDetailApiError(new Error('fail')), false);
});

import assert from 'node:assert/strict';
import test from 'node:test';
import { AdminApiError } from '../src/api/adminApiError.js';
import {
  buildAdminApiErrorToastDedupeKey,
  mapAdminApiErrorToToast,
} from '../src/utils/adminApiErrorToast.js';

test('buildAdminApiErrorToastDedupeKey는 status·detail prefix를 사용한다', () => {
  assert.equal(
    buildAdminApiErrorToastDedupeKey(503, 'Service unavailable'),
    'admin-api-503-Service unavailable',
  );
});

test('mapAdminApiErrorToToast는 401 세션 만료 copy를 반환한다', () => {
  const toast = mapAdminApiErrorToToast(new AdminApiError(401, 'Unauthorized'));

  assert.equal(toast.retryable, false);
  assert.match(toast.message, /세션이 만료/);
});

test('mapAdminApiErrorToToast는 429 cooldown Toast presentation을 반환한다', () => {
  const toast = mapAdminApiErrorToToast(
    new AdminApiError(429, 'Too many attempts'),
  );

  assert.equal(toast.kind, 'warning');
  assert.equal(toast.retryable, false);
});

test('mapAdminApiErrorToToast는 5xx retryable Toast를 반환한다', () => {
  const toast = mapAdminApiErrorToToast(
    new AdminApiError(503, 'Service unavailable'),
  );

  assert.equal(toast.kind, 'error');
  assert.equal(toast.retryable, true);
});

test('mapAdminApiErrorToToast는 422 validation Toast를 반환한다', () => {
  const toast = mapAdminApiErrorToToast(
    new AdminApiError(422, 'Invalid filter parameter'),
  );

  assert.equal(toast.kind, 'warning');
  assert.equal(toast.retryable, false);
});

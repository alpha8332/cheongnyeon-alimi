import assert from 'node:assert/strict';
import test from 'node:test';
import { AdminApiError } from '../src/api/adminApiError.js';
import {
  ADMIN_LOGIN_COOLDOWN_MS,
  isValidAdminPinInput,
  mapAdminLoginError,
} from '../src/utils/adminLoginPresentation.js';

test('isValidAdminPinInput는 숫자 4자리만 허용한다', () => {
  assert.equal(isValidAdminPinInput('0000'), true);
  assert.equal(isValidAdminPinInput('123'), false);
  assert.equal(isValidAdminPinInput('abcd'), false);
});

test('mapAdminLoginError는 429 cooldown presentation을 반환한다', () => {
  const presentation = mapAdminLoginError(
    new AdminApiError(429, 'Too many attempts'),
  );

  assert.equal(presentation.kind, 'cooldown');
  assert.equal(presentation.cooldownMs, ADMIN_LOGIN_COOLDOWN_MS);
});

test('mapAdminLoginError는 401 unauthorized presentation을 반환한다', () => {
  const presentation = mapAdminLoginError(
    new AdminApiError(401, 'Invalid PIN'),
  );

  assert.equal(presentation.kind, 'unauthorized');
});

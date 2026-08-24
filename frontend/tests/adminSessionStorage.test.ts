import assert from 'node:assert/strict';
import test from 'node:test';
import {
  getMockAdminAccessToken,
  handleAdminSessionMock,
} from '../src/mocks/adminSessionHandlers.js';
import type { AdminSessionResponse } from '../src/types/adminSession.js';
import {
  clearAdminSession,
  getAdminSessionSnapshot,
  isAdminAuthenticated,
  resetAdminSessionForTests,
  setAdminSession,
} from '../src/utils/adminSessionStorage.js';

function createSessionResponse(
  overrides: Partial<AdminSessionResponse> = {},
): AdminSessionResponse {
  return {
    access_token: getMockAdminAccessToken(),
    token_type: 'bearer',
    expires_in: 900,
    role: 'admin',
    ...overrides,
  };
}

test('setAdminSession은 in-memory snapshot을 저장하고 token을 반환한다', () => {
  resetAdminSessionForTests();

  try {
    const response = createSessionResponse();
    setAdminSession(response);

    const snapshot = getAdminSessionSnapshot();
    assert.ok(snapshot);
    assert.equal(snapshot?.accessToken, response.access_token);
    assert.equal(isAdminAuthenticated(), true);
  } finally {
    resetAdminSessionForTests();
  }
});

test('clearAdminSession은 snapshot을 제거한다', () => {
  resetAdminSessionForTests();

  try {
    setAdminSession(createSessionResponse());
    clearAdminSession();
    assert.equal(getAdminSessionSnapshot(), null);
    assert.equal(isAdminAuthenticated(), false);
  } finally {
    resetAdminSessionForTests();
  }
});

test('getAdminSessionSnapshot은 expires_in 경과 후 null을 반환한다', () => {
  resetAdminSessionForTests();

  try {
    setAdminSession(createSessionResponse({ expires_in: 1 }));
    assert.equal(isAdminAuthenticated(), true);

    const originalNow = Date.now;
    Date.now = () => originalNow() + 2_000;

    assert.equal(getAdminSessionSnapshot(), null);
    Date.now = originalNow;
  } finally {
    resetAdminSessionForTests();
  }
});

test('handleAdminSessionMock PIN 0000은 setAdminSession 입력으로 사용 가능하다', () => {
  resetAdminSessionForTests();

  try {
    const result = handleAdminSessionMock({ pin: '0000' });
    assert.equal(result.status, 200);
    if (result.status === 200) {
      setAdminSession(result.body);
      assert.equal(getAdminSessionSnapshot()?.accessToken, result.body.access_token);
    }
  } finally {
    resetAdminSessionForTests();
  }
});

import assert from 'node:assert/strict';
import test from 'node:test';
import { parseAdminApiErrorDetail } from '../src/utils/adminApiErrors.js';

test('parseAdminApiErrorDetail는 FastAPI detail 문자열을 파싱한다', () => {
  assert.equal(
    parseAdminApiErrorDetail({ detail: 'Invalid or expired admin session token.' }),
    'Invalid or expired admin session token.',
  );
});

test('parseAdminApiErrorDetail는 nested error.message를 파싱한다', () => {
  assert.equal(
    parseAdminApiErrorDetail({
      error: {
        message: 'Invalid admin PIN or authentication disabled.',
        details: {},
      },
    }),
    'Invalid admin PIN or authentication disabled.',
  );
});

test('parseAdminApiErrorDetail는 알 수 없는 body에 fallback을 반환한다', () => {
  assert.equal(parseAdminApiErrorDetail(null), 'Admin API request failed.');
  assert.equal(parseAdminApiErrorDetail({}, 'fallback'), 'fallback');
});

import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildUserLocalStorageRecoveryMessage,
  dismissUserLocalStorageRecoveryNotice,
  peekUserLocalStorageRecoveryNotice,
  recordUserLocalStorageRecoveryNotice,
  USER_LOCAL_RECOVERY_NOTICE_SESSION_KEY,
} from '../src/utils/userLocalStorageRecoveryNotice.js';

import { MemoryStorage } from './helpers/memoryStorage.js';

test('recordUserLocalStorageRecoveryNotice와 peek/dismiss round-trip', () => {
  const session = new MemoryStorage();

  assert.equal(peekUserLocalStorageRecoveryNotice(session), null);

  recordUserLocalStorageRecoveryNotice('corrupt', session);
  assert.equal(peekUserLocalStorageRecoveryNotice(session), 'corrupt');
  assert.equal(
    session.getItem(USER_LOCAL_RECOVERY_NOTICE_SESSION_KEY),
    'corrupt',
  );

  dismissUserLocalStorageRecoveryNotice(session);
  assert.equal(peekUserLocalStorageRecoveryNotice(session), null);
});

test('buildUserLocalStorageRecoveryMessage는 reason별 안내 문구를 반환한다', () => {
  assert.match(
    buildUserLocalStorageRecoveryMessage('corrupt'),
    /손상/,
  );
  assert.match(
    buildUserLocalStorageRecoveryMessage('unsupported_version'),
    /저장 형식/,
  );
  assert.match(
    buildUserLocalStorageRecoveryMessage('invalid_shape'),
    /형식/,
  );
});

test('peekUserLocalStorageRecoveryNotice는 unknown value를 무시한다', () => {
  const session = new MemoryStorage();
  session.setItem(USER_LOCAL_RECOVERY_NOTICE_SESSION_KEY, 'unknown');

  assert.equal(peekUserLocalStorageRecoveryNotice(session), null);
});

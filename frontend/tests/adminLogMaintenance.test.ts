import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildArchiveDeleteConfirmLabel,
  isArchiveDeleteConfirmValid,
} from '../src/utils/adminLogMaintenance.js';

test('isArchiveDeleteConfirmValid는 file_id 일치 여부를 검사한다', () => {
  assert.equal(isArchiveDeleteConfirmValid('log-archive-001', 'log-archive-001'), true);
  assert.equal(isArchiveDeleteConfirmValid('log-archive-001', ' log-archive-001 '), true);
  assert.equal(isArchiveDeleteConfirmValid('log-archive-001', 'wrong-id'), false);
  assert.equal(isArchiveDeleteConfirmValid('', ''), false);
});

test('buildArchiveDeleteConfirmLabel은 typed confirm 안내 문구를 만든다', () => {
  assert.equal(
    buildArchiveDeleteConfirmLabel('log-archive-001'),
    '삭제하려면 file_id "log-archive-001"를 입력하세요',
  );
});

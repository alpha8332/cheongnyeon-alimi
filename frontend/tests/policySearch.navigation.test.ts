import assert from 'node:assert/strict';
import test from 'node:test';
import {
  HOME_RECOMMENDED_SEARCHES,
  buildPolicySearchEntryPath,
} from '../src/utils/policySearchNavigation.js';

test('buildPolicySearchEntryPath는 trim된 q로 홈 검색 URL을 만든다', () => {
  assert.equal(
    buildPolicySearchEntryPath('  천안시 24세 청년 지원금  '),
    '/?q=%EC%B2%9C%EC%95%88%EC%8B%9C+24%EC%84%B8+%EC%B2%AD%EB%85%84+%EC%A7%80%EC%9B%90%EA%B8%88',
  );
});

test('buildPolicySearchEntryPath는 빈 q에 null을 반환한다', () => {
  assert.equal(buildPolicySearchEntryPath(''), null);
  assert.equal(buildPolicySearchEntryPath('   '), null);
});

test('HOME_RECOMMENDED_SEARCHES는 golden flow 칩 후보를 제공한다', () => {
  assert.ok(HOME_RECOMMENDED_SEARCHES.length >= 2);
  assert.ok(HOME_RECOMMENDED_SEARCHES.includes('서울 주거'));
});

import assert from 'node:assert/strict';
import test from 'node:test';
import {
  HOME_RECOMMENDED_SEARCHES,
  buildPolicySearchEntryPath,
  getRelatedPolicySearches,
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
  assert.ok(HOME_RECOMMENDED_SEARCHES.includes('천안 취업'));
  assert.ok(HOME_RECOMMENDED_SEARCHES.includes('서울 주거'));
  assert.ok(HOME_RECOMMENDED_SEARCHES.includes('청년 금융'));
  assert.equal(
    HOME_RECOMMENDED_SEARCHES.join('|').includes('청년도약계좌'),
    false,
  );
});

test('예시 검색 URL은 저장 프로필 강제 필터를 끌 수 있다', () => {
  assert.equal(
    buildPolicySearchEntryPath('천안 취업', { useSavedConditions: false }),
    '/?q=%EC%B2%9C%EC%95%88+%EC%B7%A8%EC%97%85&use_saved_conditions=false',
  );
});

test('대학생 검색은 자격을 추정하지 않고 선택 가능한 관련 검색어를 제공한다', () => {
  assert.deepEqual(getRelatedPolicySearches('대학생 지원'), [
    '청년',
    '장학금',
    '학자금',
  ]);
});

test('관련 검색어는 현재 검색어와 중복된 항목을 제외한다', () => {
  assert.deepEqual(getRelatedPolicySearches('서울 주거'), [
    '월세',
    '전세',
    '청년주택',
  ]);
  assert.deepEqual(getRelatedPolicySearches('관련 없는 표현'), []);
});

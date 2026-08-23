import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildUserPolicyDetailPath,
  isSamePolicyId,
  isUserCrossRoutePath,
  normalizeFavoritePolicyId,
  USER_CROSS_ROUTE_PATHS,
} from '../src/utils/userRouteIdentity.js';

test('USER_CROSS_ROUTE_PATHS는 search·recommendations·calendar·profile을 포함한다', () => {
  assert.equal(USER_CROSS_ROUTE_PATHS.search, '/');
  assert.equal(USER_CROSS_ROUTE_PATHS.legacySearch, '/search');
  assert.equal(USER_CROSS_ROUTE_PATHS.recommendations, '/recommendations');
  assert.equal(USER_CROSS_ROUTE_PATHS.calendar, '/calendar');
  assert.equal(USER_CROSS_ROUTE_PATHS.profile, '/profile');
});

test('buildUserPolicyDetailPath는 card·calendar와 동일한 detail route를 생성한다', () => {
  assert.equal(buildUserPolicyDetailPath(12), '/programs/12');
  assert.equal(
    buildUserPolicyDetailPath(12, { includePartial: true }),
    '/programs/12?include_partial=true',
  );
});

test('isSamePolicyId와 normalizeFavoritePolicyId는 numeric identity를 정규화한다', () => {
  assert.equal(isSamePolicyId(3, 3), true);
  assert.equal(isSamePolicyId(3, 4), false);
  assert.equal(normalizeFavoritePolicyId('15'), 15);
  assert.equal(normalizeFavoritePolicyId('abc'), null);
});

test('isUserCrossRoutePath는 user-facing route prefix를 인식한다', () => {
  assert.equal(isUserCrossRoutePath('/recommendations'), true);
  assert.equal(isUserCrossRoutePath('/programs/9'), true);
  assert.equal(isUserCrossRoutePath('/profile'), true);
  assert.equal(isUserCrossRoutePath('/admin'), false);
});

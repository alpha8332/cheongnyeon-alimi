/**
 * Cross-route policy identity helpers (Frontend 05 FE5-06).
 *
 * Ensures search·recommend·detail·favorites·calendar routes resolve the same
 * numeric policy id and detail path conventions.
 */

import { RECOMMENDATION_APP_ROUTE } from '../types/recommendation.js';
import { buildProgramDetailRoutePath } from './policyDetailNavigation.js';

export const USER_CROSS_ROUTE_PATHS = {
  home: '/',
  search: '/search',
  recommendations: RECOMMENDATION_APP_ROUTE,
  favorites: '/favorites',
  calendar: '/calendar',
  notifications: '/notifications',
  programs: '/programs',
  profile: '/profile',
} as const;

export type UserCrossRouteKey = keyof typeof USER_CROSS_ROUTE_PATHS;

/** Canonical detail path shared by card·calendar·recommendation result links. */
export function buildUserPolicyDetailPath(
  policyId: number,
  options?: { includePartial?: boolean },
): string {
  return buildProgramDetailRoutePath(policyId, options);
}

export function isSamePolicyId(
  left: number | null | undefined,
  right: number | null | undefined,
): boolean {
  return (
    typeof left === 'number' &&
    typeof right === 'number' &&
    Number.isInteger(left) &&
    Number.isInteger(right) &&
    left === right
  );
}

export function normalizeFavoritePolicyId(
  policyId: number | string | null | undefined,
): number | null {
  if (typeof policyId === 'number' && Number.isInteger(policyId) && policyId > 0) {
    return policyId;
  }

  if (typeof policyId === 'string' && policyId.trim().length > 0) {
    const parsed = Number(policyId);
    if (Number.isInteger(parsed) && parsed > 0) {
      return parsed;
    }
  }

  return null;
}

export function isUserCrossRoutePath(pathname: string): boolean {
  return (
    pathname === USER_CROSS_ROUTE_PATHS.home ||
    pathname.startsWith(USER_CROSS_ROUTE_PATHS.search) ||
    pathname.startsWith(USER_CROSS_ROUTE_PATHS.recommendations) ||
    pathname.startsWith(USER_CROSS_ROUTE_PATHS.favorites) ||
    pathname.startsWith(USER_CROSS_ROUTE_PATHS.calendar) ||
    pathname.startsWith(USER_CROSS_ROUTE_PATHS.notifications) ||
    pathname.startsWith(USER_CROSS_ROUTE_PATHS.programs) ||
    pathname.startsWith(USER_CROSS_ROUTE_PATHS.profile)
  );
}

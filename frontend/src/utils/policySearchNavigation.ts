import { POLICY_SEARCH_QUERY_LIMITS } from '../types/policySearch.js';

/** Home route — NL search state lives in `/?q=…` query params. */
export const POLICY_SEARCH_ROUTE = '/';

/** @deprecated Legacy path; `/search` redirects to home with the same query string. */
export const LEGACY_POLICY_SEARCH_ROUTE = '/search';

/** Golden-flow entry paths from Home hero or recommended chips (FE4-20). */
export const HOME_RECOMMENDED_SEARCHES = [
  '천안시 24세 청년 지원금',
  '청년도약계좌',
  '서울 주거',
  '전국 청년',
] as const;

/**
 * Build `/?q=…` path for non-empty trimmed query.
 * Returns null when q is empty or exceeds URL limit.
 */
export function buildPolicySearchEntryPath(q: string): string | null {
  const trimmed = q.trim();

  if (!trimmed || trimmed.length > POLICY_SEARCH_QUERY_LIMITS.q) {
    return null;
  }

  const params = new URLSearchParams();
  params.set('q', trimmed);
  const query = params.toString();
  return query ? `${POLICY_SEARCH_ROUTE}?${query}` : POLICY_SEARCH_ROUTE;
}

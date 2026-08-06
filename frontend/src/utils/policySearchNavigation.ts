import { POLICY_SEARCH_QUERY_LIMITS } from '../types/policySearch.js';

const POLICY_SEARCH_ROUTE = '/search';

/** Golden-flow entry paths from Home hero or recommended chips (FE4-20). */
export const HOME_RECOMMENDED_SEARCHES = [
  '천안시 24세 청년 지원금',
  '청년도약계좌',
  '서울 주거',
  '전국 청년',
] as const;

/**
 * Build `/search?q=…` path for non-empty trimmed query.
 * Returns null when q is empty or exceeds URL limit.
 */
export function buildPolicySearchEntryPath(q: string): string | null {
  const trimmed = q.trim();

  if (!trimmed || trimmed.length > POLICY_SEARCH_QUERY_LIMITS.q) {
    return null;
  }

  const params = new URLSearchParams();
  params.set('q', trimmed);
  return `${POLICY_SEARCH_ROUTE}?${params.toString()}`;
}

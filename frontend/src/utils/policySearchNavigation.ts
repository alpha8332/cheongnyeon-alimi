import { POLICY_SEARCH_QUERY_LIMITS } from '../types/policySearch.js';

/** Home route — NL search state lives in `/?q=…` query params. */
export const POLICY_SEARCH_ROUTE = '/';

/** @deprecated Legacy path; `/search` redirects to home with the same query string. */
export const LEGACY_POLICY_SEARCH_ROUTE = '/search';

/** Golden-flow entry paths from Home hero or recommended chips (FE4-20). */
export const HOME_RECOMMENDED_SEARCHES = [
  '천안 취업',
  '청년 금융',
  '서울 주거',
  '전국 청년',
] as const;

const RELATED_POLICY_SEARCH_GROUPS = [
  {
    triggers: ['대학생', '대학 재학생'],
    suggestions: ['청년', '장학금', '학자금'],
  },
  {
    triggers: ['청년도약계좌', '도약계좌'],
    suggestions: ['청년 금융', '청년 적금', '청년 자산'],
  },
  {
    triggers: ['취업', '구직', '일자리'],
    suggestions: ['취업', '구직', '일자리'],
  },
  {
    triggers: ['주거', '월세', '전세', '청년주택'],
    suggestions: ['주거', '월세', '전세', '청년주택'],
  },
] as const;

export interface PolicySearchEntryOptions {
  useSavedConditions?: boolean;
}

/**
 * Build `/?q=…` path for non-empty trimmed query.
 * Returns null when q is empty or exceeds URL limit.
 */
export function buildPolicySearchEntryPath(
  q: string,
  options: PolicySearchEntryOptions = {},
): string | null {
  const trimmed = q.trim();

  if (!trimmed || trimmed.length > POLICY_SEARCH_QUERY_LIMITS.q) {
    return null;
  }

  const params = new URLSearchParams();
  params.set('q', trimmed);
  if (options.useSavedConditions === false) {
    params.set('use_saved_conditions', 'false');
  }
  const query = params.toString();
  return query ? `${POLICY_SEARCH_ROUTE}?${query}` : POLICY_SEARCH_ROUTE;
}

/** Return explicit user-selectable alternatives without silently widening results. */
export function getRelatedPolicySearches(q: string): string[] {
  const normalized = q.trim();
  if (!normalized) {
    return [];
  }

  const suggestions: string[] = [];
  const seen = new Set<string>();
  for (const group of RELATED_POLICY_SEARCH_GROUPS) {
    if (!group.triggers.some((trigger) => normalized.includes(trigger))) {
      continue;
    }
    for (const suggestion of group.suggestions) {
      if (normalized.includes(suggestion) || seen.has(suggestion)) {
        continue;
      }
      seen.add(suggestion);
      suggestions.push(suggestion);
    }
  }
  return suggestions;
}

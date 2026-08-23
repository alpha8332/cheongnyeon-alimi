import type { PolicyCategory } from '../types/policy.js';
import type { PolicySearchUrlQueryState } from '../types/policySearchUrlState.js';
import type { UserSavedConditions } from '../types/userLocalStorage.js';
import { SAVED_CONDITIONS_CATEGORY_OPTIONS } from './savedConditionsForm.js';

const QUERY_CATEGORY_KEYWORDS = [
  '단기숙소', '주거', '월세', '전세', '주택', '보증금',
  '금융', '대출', '적금', '자산', '통장', '금리', '목돈', '저축',
  '복지', '의료', '건강', '수당', '지원금', '생계비',
  '취업', '일자리', '구직', '인턴', '채용',
  '창업', '스타트업', '사업자',
  '교육', '장학금', '등록금', '학비', '역량강화',
] as const;

function hasActiveSearchQuery(state: Pick<PolicySearchUrlQueryState, 'q'>): boolean {
  return state.q.trim().length > 0;
}

function resolveSavedCategory(
  category: string | null | undefined,
): PolicyCategory | null {
  if (!category) {
    return null;
  }

  return SAVED_CONDITIONS_CATEGORY_OPTIONS.find((option) => option === category) ?? null;
}

function queryContainsCategory(q: string): boolean {
  return QUERY_CATEGORY_KEYWORDS.some((keyword) => q.includes(keyword));
}

/**
 * Fill explicit flat filters from profile saved conditions when URL omits them.
 * Applied only when a non-empty `q` is present (active search).
 */
export function mergeSavedConditionsIntoSearchState(
  state: PolicySearchUrlQueryState,
  saved: UserSavedConditions | null,
): PolicySearchUrlQueryState {
  if (!saved || !hasActiveSearchQuery(state)) {
    return state;
  }

  const regionFromUrl = state.region?.trim();
  const categoryFromUrl = state.category;

  return {
    ...state,
    region: regionFromUrl ? state.region : saved.region,
    age: state.age ?? saved.age,
    category:
      categoryFromUrl ??
      (queryContainsCategory(state.q) ? null : resolveSavedCategory(saved.category)),
  };
}

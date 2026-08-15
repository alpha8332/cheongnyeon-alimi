import type { PolicyCategory } from '../types/policy.js';
import type { PolicySearchUrlQueryState } from '../types/policySearchUrlState.js';
import type { UserSavedConditions } from '../types/userLocalStorage.js';
import { SAVED_CONDITIONS_CATEGORY_OPTIONS } from './savedConditionsForm.js';

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
    category: categoryFromUrl ?? resolveSavedCategory(saved.category),
  };
}

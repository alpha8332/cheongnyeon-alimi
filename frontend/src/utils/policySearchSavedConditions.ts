import type { PolicySearchPreferences } from '../types/policySearch.js';
import type { UserSavedConditions } from '../types/userLocalStorage.js';
import {
  getSavedConditionCategories,
  isSavedConditionsEmpty,
} from './savedConditionsForm.js';

/**
 * Convert browser-only saved conditions into soft ranking preferences.
 * These values must be sent in a POST body and never serialized into the URL.
 */
export function buildSavedConditionSearchPreferences(
  saved: UserSavedConditions | null,
  enabled = true,
): PolicySearchPreferences | null {
  if (!enabled || isSavedConditionsEmpty(saved) || saved === null) {
    return null;
  }

  return {
    region: saved.region,
    age: saved.age,
    categories: getSavedConditionCategories(saved),
  };
}

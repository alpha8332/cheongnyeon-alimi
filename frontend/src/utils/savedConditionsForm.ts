import type { PolicyCategory } from '../types/policy.js';
import type { UserSavedConditions } from '../types/userLocalStorage.js';
import type { RecommendationRequest } from '../types/recommendation.js';
import { getCategoryLabel } from './policyDisplay.js';

export const SAVED_CONDITIONS_CATEGORY_OPTIONS: PolicyCategory[] = [
  'housing',
  'finance',
  'welfare',
  'employment',
  'startup',
  'education',
  'other',
];

export const SAVED_CONDITIONS_MIN_AGE = 1;
export const SAVED_CONDITIONS_MAX_AGE = 120;

export function toSavedConditionsDraft(
  conditions: UserSavedConditions | null,
): UserSavedConditions {
  return {
    region: conditions?.region ?? null,
    age: conditions?.age ?? null,
    category: conditions?.category ?? null,
  };
}

export function parseSavedConditionsDraft(
  draft: UserSavedConditions,
): UserSavedConditions {
  const region = draft.region?.trim() ?? '';
  const category = draft.category?.trim() ?? '';

  let age: number | null = draft.age;
  if (
    age !== null &&
    (!Number.isInteger(age) ||
      age < SAVED_CONDITIONS_MIN_AGE ||
      age > SAVED_CONDITIONS_MAX_AGE)
  ) {
    age = null;
  }

  return {
    region: region.length > 0 ? region : null,
    age,
    category: category.length > 0 ? category : null,
  };
}

export function formatSavedConditionsSummary(
  conditions: UserSavedConditions | null,
): string | null {
  if (conditions === null) {
    return null;
  }

  const parts: string[] = [];

  if (conditions.region) {
    parts.push(conditions.region);
  }

  if (conditions.age !== null) {
    parts.push(`${conditions.age}세`);
  }

  if (conditions.category) {
    const knownCategory = SAVED_CONDITIONS_CATEGORY_OPTIONS.find(
      (option) => option === conditions.category,
    );
    parts.push(
      knownCategory
        ? getCategoryLabel(knownCategory)
        : conditions.category,
    );
  }

  return parts.length > 0 ? parts.join(' · ') : null;
}

export function buildSavedConditionsKey(
  conditions: UserSavedConditions | null,
): string {
  if (conditions === null) {
    return 'empty';
  }

  return `${conditions.region ?? ''}|${conditions.age ?? ''}|${conditions.category ?? ''}`;
}

export function toRecommendationRequestFromConditions(
  conditions: UserSavedConditions,
): RecommendationRequest {
  return {
    region: conditions.region,
    age: conditions.age,
    category: conditions.category,
  };
}

export function isSavedConditionsEmpty(
  conditions: UserSavedConditions | null,
): boolean {
  return formatSavedConditionsSummary(conditions) === null;
}

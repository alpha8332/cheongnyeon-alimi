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

export function getSavedConditionCategories(
  conditions: UserSavedConditions | null,
): PolicyCategory[] {
  const raw = conditions?.categories?.length
    ? conditions.categories
    : conditions?.category
      ? [conditions.category]
      : [];
  const known = new Set<PolicyCategory>(SAVED_CONDITIONS_CATEGORY_OPTIONS);
  return Array.from(
    new Set(
      raw.filter((category): category is PolicyCategory =>
        known.has(category as PolicyCategory),
      ),
    ),
  );
}

export function toSavedConditionsDraft(
  conditions: UserSavedConditions | null,
): UserSavedConditions {
  return {
    region: conditions?.region ?? null,
    age: conditions?.age ?? null,
    category: getSavedConditionCategories(conditions)[0] ?? null,
    categories: getSavedConditionCategories(conditions),
  };
}

export function parseSavedConditionsDraft(
  draft: UserSavedConditions,
): UserSavedConditions {
  const region = draft.region?.trim() ?? '';
  const draftCategories = draft.categories?.length
    ? draft.categories
    : draft.category
      ? [draft.category]
      : [];
  const categories = getSavedConditionCategories({
    region: null,
    age: null,
    category: draftCategories[0]?.trim() || null,
    categories: draftCategories.map((category) => category.trim()),
  });

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
    category: categories[0] ?? null,
    categories,
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

  const categories = getSavedConditionCategories(conditions);
  if (categories.length > 0) {
    parts.push(categories.map(getCategoryLabel).join(', '));
  }

  return parts.length > 0 ? parts.join(' · ') : null;
}

export function buildSavedConditionsKey(
  conditions: UserSavedConditions | null,
): string {
  if (conditions === null) {
    return 'empty';
  }

  return `${conditions.region ?? ''}|${conditions.age ?? ''}|${getSavedConditionCategories(conditions).join(',')}`;
}

export function toRecommendationRequestFromConditions(
  conditions: UserSavedConditions,
): RecommendationRequest {
  return {
    region: conditions.region,
    age: conditions.age,
    category: conditions.category,
    categories: getSavedConditionCategories(conditions),
    include_partial: true,
  };
}

export function isSavedConditionsEmpty(
  conditions: UserSavedConditions | null,
): boolean {
  return formatSavedConditionsSummary(conditions) === null;
}

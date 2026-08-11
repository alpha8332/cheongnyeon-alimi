import type { ItemConditionDto } from '../types/eligibilitySummary.js';
import type { PolicyCategory, PolicyDto } from '../types/policy.js';
import type { UserSavedConditions } from '../types/userLocalStorage.js';

export type EligibilityComparisonStatus = 'match' | 'mismatch' | 'needs_review';

export const ELIGIBILITY_COMPARISON_LABELS: Record<
  EligibilityComparisonStatus,
  string
> = {
  match: '조건상 일치',
  mismatch: '조건상 불일치',
  needs_review: '추가 확인 필요',
};

export function hasSavedConditionsForComparison(
  conditions: UserSavedConditions | null,
): boolean {
  if (conditions === null) {
    return false;
  }

  return (
    conditions.region !== null ||
    conditions.age !== null ||
    conditions.category !== null
  );
}

export function compareSavedPolicyCategory(
  policy: PolicyDto,
  conditions: UserSavedConditions,
): EligibilityComparisonStatus | null {
  if (!conditions.category) {
    return null;
  }

  const savedCategory = conditions.category as PolicyCategory;

  if (policy.categories.includes(savedCategory)) {
    return 'match';
  }

  return 'mismatch';
}

export function compareEligibilityCondition(
  item: ItemConditionDto,
  policy: PolicyDto,
  conditions: UserSavedConditions,
): EligibilityComparisonStatus | null {
  if (item.evidence === null) {
    return 'needs_review';
  }

  switch (item.category) {
    case 'age': {
      if (conditions.age === null) {
        return null;
      }

      const { age_min: min, age_max: max } = policy;

      if (min === null && max === null) {
        return 'needs_review';
      }

      if (min !== null && conditions.age < min) {
        return 'mismatch';
      }

      if (max !== null && conditions.age > max) {
        return 'mismatch';
      }

      return 'match';
    }
    case 'region': {
      if (!conditions.region) {
        return null;
      }

      const savedRegion = conditions.region.trim();

      if (savedRegion.length === 0) {
        return null;
      }

      if (policy.regions.includes('전국')) {
        return 'match';
      }

      const matched = policy.regions.some(
        (region) =>
          region.includes(savedRegion) || savedRegion.includes(region),
      );

      return matched ? 'match' : 'mismatch';
    }
    default:
      return null;
  }
}

import type { PolicyDto } from '../types/policy.js';
import type {
  RecommendationItemDto,
  RecommendationRequest,
} from '../types/recommendation.js';
import type { UserSavedConditions } from '../types/userLocalStorage.js';
import { isHomeFeaturedPolicy } from './policyDeadline.js';
import { recommendationItemToPolicyDto } from './recommendationPolicyMapping.js';
import {
  isSavedConditionsEmpty,
  toRecommendationRequestFromConditions,
} from './savedConditionsForm.js';

export const HOME_RECOMMENDED_POLICY_LIMIT = 3;

export const HOME_SAVED_CONDITIONS_RECOMMENDATION_CAPTION =
  '저장된 조건으로 추천된 정책입니다.';

/** Recommendation API fetch size before client-side open·always filter. */
export const HOME_RECOMMENDATION_FETCH_LIMIT = 12;

export function hasHomeSavedConditions(
  conditions: UserSavedConditions | null,
): boolean {
  return !isSavedConditionsEmpty(conditions);
}

export function buildHomeRecommendationRequest(
  conditions: UserSavedConditions,
): RecommendationRequest {
  return {
    ...toRecommendationRequestFromConditions(conditions),
    include_partial: false,
    limit: HOME_RECOMMENDATION_FETCH_LIMIT,
  };
}

export function isHomeRecommendablePolicy(
  policy: PolicyDto,
  referenceDate: Date = new Date(),
): boolean {
  if (policy.application_status === 'closed') {
    return false;
  }

  return isHomeFeaturedPolicy(policy, referenceDate);
}

export function pickHomeFallbackPolicies(
  policies: readonly PolicyDto[],
  limit = HOME_RECOMMENDED_POLICY_LIMIT,
  referenceDate: Date = new Date(),
): PolicyDto[] {
  return policies
    .filter((policy) => isHomeRecommendablePolicy(policy, referenceDate))
    .slice(0, limit);
}

export function mapHomeRecommendationItemsToPolicies(
  items: readonly RecommendationItemDto[],
  limit = HOME_RECOMMENDED_POLICY_LIMIT,
  referenceDate: Date = new Date(),
): PolicyDto[] {
  return items
    .map(recommendationItemToPolicyDto)
    .filter((policy) => isHomeRecommendablePolicy(policy, referenceDate))
    .slice(0, limit);
}

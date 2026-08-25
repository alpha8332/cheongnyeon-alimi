import type { PolicyDto } from '../types/policy.js';
import type {
  RecommendationItemDto,
  RecommendationReasonDto,
  RecommendationRequest,
  RecommendationResponse,
  ResolvedRecommendationRequest,
} from '../types/recommendation.js';
import {
  RECOMMENDATION_DEFAULT_DISCLAIMER,
} from '../types/recommendation.js';

/** Mock-only trigger: returns HTTP 200 with zero items (FE6-00 contract). */
export const MOCK_RECOMMENDATION_EMPTY_REGION = 'MOCK_EMPTY';

export const MOCK_RECOMMENDATION_EVALUATED_AT = '2026-08-11T12:00:00.000Z';

function selectedCategories(
  request: ResolvedRecommendationRequest,
): string[] {
  return Array.from(
    new Set(
      [request.category, ...(request.categories ?? [])].filter(
        (category): category is string => Boolean(category),
      ),
    ),
  );
}

function mapApplicationStatusForFilter(
  status: string | undefined,
): string | undefined {
  if (status === 'upcoming') {
    return 'scheduled';
  }

  return status;
}

function buildReasons(
  policy: PolicyDto,
  request: ResolvedRecommendationRequest,
): RecommendationReasonDto[] {
  const reasons: RecommendationReasonDto[] = [];

  if (selectedCategories(request).some((category) =>
    policy.categories.includes(category as PolicyDto['categories'][number]))) {
    reasons.push({
      code: 'MATCHED_CATEGORY',
      label: '관심 분야와 일치하는 정책입니다.',
    });
  }

  if (request.region && policy.regions.includes(request.region)) {
    reasons.push({
      code: 'MATCHED_REGION',
      label: '입력한 거주지와 일치하는 지역 조건이 있습니다.',
    });
  }

  if (
    request.age !== undefined &&
    (policy.age_min === null || request.age >= policy.age_min) &&
    (policy.age_max === null || request.age <= policy.age_max)
  ) {
    reasons.push({
      code: 'MATCHED_AGE',
      label: '입력한 연령대와 일치하는 조건이 있습니다.',
    });
  }

  if (
    request.status &&
    policy.application_status === mapApplicationStatusForFilter(request.status)
  ) {
    reasons.push({
      code: 'MATCHED_STATUS',
      label: '선택한 신청 상태와 일치합니다.',
    });
  }

  if (reasons.length === 0) {
    reasons.push({
      code: 'GENERAL_FIT',
      label: '입력 조건과 관련된 정책 후보입니다.',
    });
  }

  return reasons;
}

function computeScore(
  policy: PolicyDto,
  request: ResolvedRecommendationRequest,
): number {
  let score = 0;

  if (selectedCategories(request).some((category) =>
    policy.categories.includes(category as PolicyDto['categories'][number]))) {
    score += 30;
  }

  if (request.region && policy.regions.includes(request.region)) {
    score += 30;
  }

  if (
    request.age !== undefined &&
    (policy.age_min === null || request.age >= policy.age_min) &&
    (policy.age_max === null || request.age <= policy.age_max)
  ) {
    score += 25;
  }

  if (
    request.status &&
    policy.application_status === mapApplicationStatusForFilter(request.status)
  ) {
    score += 15;
  }

  return score > 0 ? score : 10;
}

export function toRecommendationItem(
  policy: PolicyDto,
  request: ResolvedRecommendationRequest,
): RecommendationItemDto {
  const unknown_conditions =
    policy.data_quality_status === 'partial'
      ? ['정책 데이터가 partial 상태입니다. 공식 원문 확인이 필요합니다.']
      : [];

  return {
    id: policy.id,
    source_id: policy.source_id,
    external_id: policy.external_id ?? '',
    title: policy.title,
    lead: policy.summary,
    category: policy.categories[0] ?? 'other',
    categories: [...policy.categories],
    regions: [...policy.regions],
    min_age: policy.age_min,
    max_age: policy.age_max,
    application_start: policy.application_start,
    application_end: policy.application_end,
    application_status: policy.application_status ?? 'open',
    data_quality_status: policy.data_quality_status,
    score: computeScore(policy, request),
    reasons: buildReasons(policy, request),
    unknown_conditions,
    disclaimer: RECOMMENDATION_DEFAULT_DISCLAIMER,
  };
}

function matchesRecommendationFilters(
  policy: PolicyDto,
  request: ResolvedRecommendationRequest,
): boolean {
  if (!request.include_partial && policy.data_quality_status === 'partial') {
    return false;
  }

  const requestedCategories = selectedCategories(request);
  if (
    requestedCategories.length > 0 &&
    !requestedCategories.some((category) =>
      policy.categories.includes(category as PolicyDto['categories'][number]))
  ) {
    return false;
  }

  if (request.region && !policy.regions.includes(request.region)) {
    return false;
  }

  if (
    request.age !== undefined &&
    ((policy.age_min !== null && request.age < policy.age_min) ||
      (policy.age_max !== null && request.age > policy.age_max))
  ) {
    return false;
  }

  if (
    request.status &&
    policy.application_status !== mapApplicationStatusForFilter(request.status)
  ) {
    return false;
  }

  return true;
}

export function buildMockRecommendationResponse(
  policies: readonly PolicyDto[],
  request: ResolvedRecommendationRequest,
): RecommendationResponse {
  const items = [...policies]
    .filter((policy) => matchesRecommendationFilters(policy, request))
    .map((policy) => toRecommendationItem(policy, request))
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }

      return left.id - right.id;
    })
    .slice(0, request.limit);

  return {
    items,
    total: items.length,
    evaluated_at: MOCK_RECOMMENDATION_EVALUATED_AT,
  };
}

export function createEmptyRecommendationResponse(): RecommendationResponse {
  return {
    items: [],
    total: 0,
    evaluated_at: MOCK_RECOMMENDATION_EVALUATED_AT,
  };
}

export function isMockEmptyRecommendationRequest(
  request: RecommendationRequest,
): boolean {
  return request.region?.trim() === MOCK_RECOMMENDATION_EMPTY_REGION;
}

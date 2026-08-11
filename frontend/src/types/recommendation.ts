/**
 * Recommendation API contract (Frontend 06 / FE6-00).
 *
 * Aligns with Backend recommendation draft on `origin/feature/backend/policy-recommendation`.
 * W4-G0 proposal — not approved as current public API contract.
 *
 * @see docs/development/develop_plan/integration/06_recommendation_vertical_slice.md
 */

import type { PolicyCategory } from './policy.js';

/** Client router path — distinct from NL search at `/search`. */
export const RECOMMENDATION_APP_ROUTE = '/recommendations';

export const RECOMMENDATION_ENDPOINTS = {
  post: {
    method: 'POST' as const,
    path: '/api/v1/recommendations',
  },
  get: {
    method: 'GET' as const,
    path: '/api/v1/policies/recommendations',
  },
} as const;

/** Backend draft status filter (`open` | `upcoming` | `closed`). Differs from public `ApplicationStatus`. */
export type RecommendationStatusFilter = 'open' | 'upcoming' | 'closed';

export interface RecommendationRequest {
  age?: number | null;
  region?: string | null;
  /** Backend accepts string category code (e.g. finance, housing). */
  category?: PolicyCategory | string | null;
  status?: RecommendationStatusFilter | string | null;
  include_partial?: boolean;
  limit?: number;
}

export interface RecommendationReasonDto {
  code: string;
  label: string;
}

export interface RecommendationItemDto {
  id: number;
  source_id: string;
  external_id: string;
  title: string;
  lead: string | null;
  category: string;
  regions: string[];
  min_age: number | null;
  max_age: number | null;
  application_start: string | null;
  application_end: string | null;
  application_status: string;
  data_quality_status: string;
  /** Request-internal ordering only — not eligibility probability (W4-G0). */
  score: number;
  reasons: RecommendationReasonDto[];
  unknown_conditions: string[];
  disclaimer: string;
}

export interface RecommendationResponse {
  items: RecommendationItemDto[];
  total: number;
  evaluated_at: string;
}

export const RECOMMENDATION_DEFAULTS = {
  include_partial: false,
  limit: 10,
} as const;

export const RECOMMENDATION_LIMITS = {
  ageMin: 0,
  ageMax: 120,
  limitMin: 1,
  limitMax: 50,
} as const;

export const RECOMMENDATION_DEFAULT_DISCLAIMER =
  '본 추천 결과는 자격을 확정하지 않으며, 상세 자격 및 신청 조건은 공식 원문에서 확인해야 합니다.';

export interface ResolvedRecommendationRequest {
  age?: number;
  region?: string;
  category?: string;
  status?: string;
  include_partial: boolean;
  limit: number;
}

export interface RecommendationValidationErrorBody {
  detail: string;
}

export function resolveRecommendationRequest(
  request: RecommendationRequest = {},
): ResolvedRecommendationRequest {
  const include_partial = request.include_partial ?? RECOMMENDATION_DEFAULTS.include_partial;
  const limit = request.limit ?? RECOMMENDATION_DEFAULTS.limit;

  if (
    request.age !== undefined &&
    request.age !== null &&
    (!Number.isInteger(request.age) ||
      request.age < RECOMMENDATION_LIMITS.ageMin ||
      request.age > RECOMMENDATION_LIMITS.ageMax)
  ) {
    throw new Error('Recommendation age must be an integer from 0 to 120.');
  }

  if (
    !Number.isInteger(limit) ||
    limit < RECOMMENDATION_LIMITS.limitMin ||
    limit > RECOMMENDATION_LIMITS.limitMax
  ) {
    throw new Error('Recommendation limit must be an integer from 1 to 50.');
  }

  const region = request.region?.trim();
  const category = request.category?.toString().trim();
  const status = request.status?.toString().trim();

  return {
    include_partial,
    limit,
    ...(request.age !== undefined && request.age !== null ? { age: request.age } : {}),
    ...(region ? { region } : {}),
    ...(category ? { category } : {}),
    ...(status ? { status } : {}),
  };
}

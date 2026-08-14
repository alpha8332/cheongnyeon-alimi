import type { PolicyDto } from '../types/policy.js';
import type {
  RecommendationRequest,
  RecommendationResponse,
  RecommendationValidationErrorBody,
} from '../types/recommendation.js';
import { resolveRecommendationRequest } from '../types/recommendation.js';
import {
  buildMockRecommendationResponse,
  createEmptyRecommendationResponse,
  isMockEmptyRecommendationRequest,
} from './recommendationFixtures.js';

export type RecommendationMockSuccess = {
  status: 200;
  body: RecommendationResponse;
};

export type RecommendationMockValidationFailure = {
  status: 422;
  body: RecommendationValidationErrorBody;
};

export type RecommendationMockResult =
  | RecommendationMockSuccess
  | RecommendationMockValidationFailure;

export function handleRecommendationMock(
  request: RecommendationRequest,
  policies: readonly PolicyDto[],
): RecommendationMockResult {
  try {
    const resolved = resolveRecommendationRequest(request);

    if (isMockEmptyRecommendationRequest(request)) {
      return {
        status: 200,
        body: createEmptyRecommendationResponse(),
      };
    }

    return {
      status: 200,
      body: buildMockRecommendationResponse(policies, resolved),
    };
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : 'Recommendation request is invalid.';

    return {
      status: 422,
      body: { detail: message },
    };
  }
}

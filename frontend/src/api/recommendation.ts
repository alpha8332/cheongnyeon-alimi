import axios from 'axios';
import { apiClient } from '@/api/client';
import { RecommendationApiError } from '@/api/recommendationApiError';
import { handleRecommendationMock } from '@/mocks/recommendationHandlers';
import { mockPolicies } from '@/mocks/policies';
import {
  RECOMMENDATION_ENDPOINTS,
  type RecommendationRequest,
  type RecommendationResponse,
} from '@/types/recommendation';

const MOCK_DELAY_MS = 300;
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export { RecommendationApiError } from '@/api/recommendationApiError';

export async function postRecommendations(
  request: RecommendationRequest = {},
): Promise<RecommendationResponse> {
  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    const result = handleRecommendationMock(request, mockPolicies);

    if (result.status === 422) {
      throw new RecommendationApiError(422, result.body.detail);
    }

    return result.body;
  }

  try {
    const response = await apiClient.post<RecommendationResponse>(
      RECOMMENDATION_ENDPOINTS.post.path,
      request,
    );

    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status ?? 0;
      const detail =
        typeof error.response?.data === 'object' &&
        error.response?.data !== null &&
        'detail' in error.response.data &&
        typeof (error.response.data as { detail: unknown }).detail === 'string'
          ? (error.response.data as { detail: string }).detail
          : error.message;

      throw new RecommendationApiError(status || 503, detail);
    }

    throw error;
  }
}

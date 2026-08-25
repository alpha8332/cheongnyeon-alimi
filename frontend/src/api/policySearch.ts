import axios from 'axios';
import { apiClient } from '@/api/client';
import { PolicySearchApiError } from '@/api/policySearchApiError';
import { handlePolicySearchMock } from '@/mocks/policySearchHandlers';
import { mockPolicies } from '@/mocks/policies';
import {
  POLICY_SEARCH_ENDPOINT,
  type PolicySearchQueryParams,
  type PolicySearchResponse,
} from '@/types/policySearch';

const MOCK_DELAY_MS = 300;
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export { PolicySearchApiError } from '@/api/policySearchApiError';

export async function getPolicySearch(
  query: PolicySearchQueryParams,
): Promise<PolicySearchResponse> {
  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    const result = handlePolicySearchMock(query, mockPolicies);

    if (result.status === 422) {
      throw new PolicySearchApiError(422, result.body.detail);
    }

    return result.body;
  }

  try {
    const { preferences, ...params } = query;
    const response = preferences
      ? await apiClient.post<PolicySearchResponse>(
          POLICY_SEARCH_ENDPOINT.path,
          { ...params, preferences },
        )
      : await apiClient.get<PolicySearchResponse>(
          POLICY_SEARCH_ENDPOINT.path,
          { params },
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

      throw new PolicySearchApiError(status || 503, detail);
    }

    throw error;
  }
}

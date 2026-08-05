import { apiClient } from '@/api/client';
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

export class PolicySearchApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'PolicySearchApiError';
    this.status = status;
    this.detail = detail;
  }
}

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

  const response = await apiClient.get<PolicySearchResponse>(
    POLICY_SEARCH_ENDPOINT.path,
    { params: query },
  );

  return response.data;
}

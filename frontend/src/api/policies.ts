import axios from 'axios';
import { apiClient } from '@/api/client';
import {
  buildPolicyDetailPath,
  POLICY_COLLECTION_PATH,
  resolvePolicyListQuery,
} from '@/api/policyRequest';
import {
  createMockPolicyListResponse,
  findMockPolicyById,
} from '@/mocks/policyContract';
import { mockPolicies } from '@/mocks/policies';
import type {
  PolicyDto,
  PolicyListQuery,
  PolicyListResponse,
} from '@/types/policy';

const MOCK_DELAY_MS = 300;
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export async function getPolicies(
  query: PolicyListQuery = {},
): Promise<PolicyListResponse> {
  const resolvedQuery = resolvePolicyListQuery(query);

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    return createMockPolicyListResponse(mockPolicies, resolvedQuery);
  }

  const response = await apiClient.get<PolicyListResponse>(
    POLICY_COLLECTION_PATH,
    { params: resolvedQuery },
  );
  return response.data;
}

export async function getPolicyById(
  policyId: number,
  includePartial = false,
): Promise<PolicyDto | null> {
  const detailPath = buildPolicyDetailPath(policyId);

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    return findMockPolicyById(mockPolicies, policyId, includePartial);
  }

  try {
    const response = await apiClient.get<PolicyDto>(
      detailPath,
      {
        params: {
          include_partial: includePartial,
        },
      },
    );
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }

    throw error;
  }
}

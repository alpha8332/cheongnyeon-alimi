import axios from 'axios';
import { apiClient } from '@/api/client';
import { PolicyDetailApiError } from '@/api/policyDetailApiError';
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

/** Mock audit: summary refetch on this policy id returns 503. */
export const MOCK_POLICY_SUMMARY_REFETCH_503_ID = 9101;

/** Mock audit: summary refetch with include_partial on this id returns 422. */
export const MOCK_POLICY_SUMMARY_REFETCH_422_ID = 9102;

export interface PolicyDetailFetchOptions {
  summaryRefetch?: boolean;
}

function readPolicyDetailErrorDetail(data: unknown): string {
  if (
    typeof data === 'object' &&
    data !== null &&
    'detail' in data &&
    typeof data.detail === 'string'
  ) {
    return data.detail;
  }

  return '정책 상세를 불러오지 못했습니다.';
}

function throwPolicyDetailApiErrorFromAxios(error: unknown): never {
  if (!axios.isAxiosError(error)) {
    throw error;
  }

  const status = error.response?.status ?? 0;
  throw new PolicyDetailApiError(
    status,
    readPolicyDetailErrorDetail(error.response?.data),
  );
}

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
  options: PolicyDetailFetchOptions = {},
): Promise<PolicyDto | null> {
  const detailPath = buildPolicyDetailPath(policyId);

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);

    if (
      options.summaryRefetch &&
      policyId === MOCK_POLICY_SUMMARY_REFETCH_503_ID
    ) {
      throw new PolicyDetailApiError(
        503,
        'Eligibility summary refetch unavailable for audit test.',
      );
    }

    if (
      options.summaryRefetch &&
      includePartial &&
      policyId === MOCK_POLICY_SUMMARY_REFETCH_422_ID
    ) {
      throw new PolicyDetailApiError(
        422,
        'include_partial is not supported for this mock policy.',
      );
    }

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

    throwPolicyDetailApiErrorFromAxios(error);
  }
}

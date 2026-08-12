import axios from 'axios';
import { AdminApiError } from '@/api/adminApiError';
import {
  buildAdminAuthorizationHeader,
  type AdminApiRequestOptions,
} from '@/api/adminRequest';
import { apiClient } from '@/api/client';
import {
  handleAdminPolicyDetailMock,
  handleAdminPolicyListMock,
} from '@/mocks/adminObservabilityHandlers';
import { mockPolicies } from '@/mocks/policies';
import type {
  AdminPolicyDetailDto,
  AdminPolicyListQuery,
  AdminPolicyListResponse,
} from '@/types/adminPolicyData';
import {
  ADMIN_POLICY_DATA_PATH,
  buildAdminPolicyDetailPath,
  resolveAdminPolicyListQuery,
} from '@/types/adminPolicyData';
import { parseAdminApiErrorDetail } from '@/utils/adminApiErrors';

const MOCK_DELAY_MS = 300;
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function toAdminApiError(error: unknown, fallback: string): AdminApiError {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 503;
    const detail = parseAdminApiErrorDetail(error.response?.data, fallback);
    return new AdminApiError(status, detail);
  }

  if (error instanceof AdminApiError) {
    return error;
  }

  throw error;
}

export async function getAdminPolicies(
  query: AdminPolicyListQuery = {},
  options: AdminApiRequestOptions = {},
): Promise<AdminPolicyListResponse> {
  const resolvedQuery = resolveAdminPolicyListQuery(query);

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);

    if (resolvedQuery.source_id === 'MOCK_503') {
      throw new AdminApiError(
        503,
        'Service unavailable for admin policy list audit test.',
      );
    }

    if (resolvedQuery.source_id === 'MOCK_401') {
      throw new AdminApiError(401, 'Admin session expired for audit test.');
    }

    if (resolvedQuery.source_id === 'MOCK_422') {
      throw new AdminApiError(
        422,
        'Invalid filter parameter for admin policy list audit test.',
      );
    }

    return handleAdminPolicyListMock(mockPolicies, resolvedQuery);
  }

  try {
    const response = await apiClient.get<AdminPolicyListResponse>(
      ADMIN_POLICY_DATA_PATH,
      {
        params: resolvedQuery,
        headers: buildAdminAuthorizationHeader(options.accessToken),
      },
    );
    return response.data;
  } catch (error: unknown) {
    throw toAdminApiError(error, 'Admin policy list request failed.');
  }
}

export async function getAdminPolicyById(
  policyId: number,
  options: AdminApiRequestOptions = {},
): Promise<AdminPolicyDetailDto | null> {
  if (!Number.isSafeInteger(policyId) || policyId < 1) {
    return null;
  }

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    const result = handleAdminPolicyDetailMock(mockPolicies, policyId);

    if (result.status === 404) {
      return null;
    }

    return result.body;
  }

  try {
    const response = await apiClient.get<AdminPolicyDetailDto>(
      buildAdminPolicyDetailPath(policyId),
      {
        headers: buildAdminAuthorizationHeader(options.accessToken),
      },
    );
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }

    throw toAdminApiError(error, 'Admin policy detail request failed.');
  }
}

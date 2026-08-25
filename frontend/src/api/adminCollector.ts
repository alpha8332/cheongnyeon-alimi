import axios from 'axios';
import { AdminApiError } from '@/api/adminApiError';
import {
  buildAdminAuthorizationHeader,
  type AdminApiRequestOptions,
} from '@/api/adminRequest';
import { apiClient } from '@/api/client';
import { handleAdminCollectorStatusMock } from '@/mocks/adminCollectorHandlers';
import {
  ADMIN_COLLECTORS_PATH,
  type AdminCollectorStatusResponse,
} from '@/types/adminCollector';
import { parseAdminApiErrorDetail } from '@/utils/adminApiErrors';

const MOCK_DELAY_MS = 300;
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function getAdminCollectorStatus(
  options: AdminApiRequestOptions = {},
): Promise<AdminCollectorStatusResponse> {
  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    return handleAdminCollectorStatusMock();
  }

  try {
    const response = await apiClient.get<AdminCollectorStatusResponse>(
      ADMIN_COLLECTORS_PATH,
      { headers: buildAdminAuthorizationHeader(options.accessToken) },
    );
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      throw new AdminApiError(
        error.response?.status ?? 503,
        parseAdminApiErrorDetail(
          error.response?.data,
          '수집기 상태를 불러오지 못했습니다.',
        ),
      );
    }
    throw error;
  }
}


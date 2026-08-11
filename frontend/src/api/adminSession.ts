import axios from 'axios';
import { AdminApiError } from '@/api/adminApiError';
import { ADMIN_SESSION_PATH } from '@/api/adminRequest';
import { apiClient } from '@/api/client';
import { handleAdminSessionMock } from '@/mocks/adminSessionHandlers';
import type {
  AdminSessionRequest,
  AdminSessionResponse,
} from '@/types/adminSession';
import { parseAdminApiErrorDetail } from '@/utils/adminApiErrors';

const MOCK_DELAY_MS = 300;
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export { AdminApiError } from '@/api/adminApiError';

export async function createAdminSession(
  request: AdminSessionRequest,
): Promise<AdminSessionResponse> {
  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    const result = handleAdminSessionMock(request);

    if (result.status !== 200) {
      throw new AdminApiError(result.status, result.body.message);
    }

    return result.body;
  }

  try {
    const response = await apiClient.post<AdminSessionResponse>(
      ADMIN_SESSION_PATH,
      request,
    );
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status ?? 503;
      const detail = parseAdminApiErrorDetail(
        error.response?.data,
        'Admin session request failed.',
      );
      throw new AdminApiError(status, detail);
    }

    throw error;
  }
}

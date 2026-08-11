import axios from 'axios';
import { AdminApiError } from '@/api/adminApiError';
import {
  buildAdminAuthorizationHeader,
  type AdminApiRequestOptions,
} from '@/api/adminRequest';
import { apiClient } from '@/api/client';
import {
  handleAdminLogArchiveDeleteMock,
  handleAdminLogEventListMock,
  handleAdminLogFileListMock,
  handleAdminLogRotateCurrentMock,
} from '@/mocks/adminObservabilityHandlers';
import type {
  AdminLogDeleteResultDto,
  AdminLogEventListQuery,
  AdminLogEventListResponse,
  AdminLogFileListQuery,
  AdminLogFileListResponse,
  AdminLogRotateResultDto,
} from '@/types/adminLog';
import {
  ADMIN_LOG_FILES_PATH,
  ADMIN_LOG_ROTATE_CURRENT_PATH,
  buildAdminLogArchiveDeletePath,
  resolveAdminLogEventListQuery,
  resolveAdminLogFileListQuery,
} from '@/types/adminLog';
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

export async function getAdminLogFiles(
  query: AdminLogFileListQuery = {},
  options: AdminApiRequestOptions = {},
): Promise<AdminLogFileListResponse> {
  const resolvedQuery = resolveAdminLogFileListQuery(query);

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    return handleAdminLogFileListMock(resolvedQuery);
  }

  try {
    const response = await apiClient.get<AdminLogFileListResponse>(
      ADMIN_LOG_FILES_PATH,
      {
        params: resolvedQuery,
        headers: buildAdminAuthorizationHeader(options.accessToken),
      },
    );
    return response.data;
  } catch (error: unknown) {
    throw toAdminApiError(error, 'Admin log file list request failed.');
  }
}

export async function getAdminLogEvents(
  query: AdminLogEventListQuery = {},
  options: AdminApiRequestOptions = {},
): Promise<AdminLogEventListResponse> {
  const resolvedQuery = resolveAdminLogEventListQuery(query);

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    return handleAdminLogEventListMock(resolvedQuery);
  }

  try {
    const response = await apiClient.get<AdminLogEventListResponse>(
      `${ADMIN_LOG_FILES_PATH}/events`,
      {
        params: resolvedQuery,
        headers: buildAdminAuthorizationHeader(options.accessToken),
      },
    );
    return response.data;
  } catch (error: unknown) {
    throw toAdminApiError(error, 'Admin log event list request failed.');
  }
}

export async function deleteAdminLogArchive(
  fileId: string,
  options: AdminApiRequestOptions = {},
): Promise<AdminLogDeleteResultDto> {
  const trimmed = fileId.trim();

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    const result = handleAdminLogArchiveDeleteMock(trimmed);

    if (result.status !== 200) {
      throw new AdminApiError(result.status, result.body.detail);
    }

    return result.body;
  }

  try {
    const response = await apiClient.delete<AdminLogDeleteResultDto>(
      buildAdminLogArchiveDeletePath(trimmed),
      {
        headers: buildAdminAuthorizationHeader(options.accessToken),
      },
    );
    return response.data;
  } catch (error: unknown) {
    throw toAdminApiError(error, 'Admin log archive delete request failed.');
  }
}

export async function rotateAdminLogCurrent(
  options: AdminApiRequestOptions = {},
): Promise<AdminLogRotateResultDto> {
  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    return handleAdminLogRotateCurrentMock();
  }

  try {
    const response = await apiClient.post<AdminLogRotateResultDto>(
      ADMIN_LOG_ROTATE_CURRENT_PATH,
      {},
      {
        headers: buildAdminAuthorizationHeader(options.accessToken),
      },
    );
    return response.data;
  } catch (error: unknown) {
    throw toAdminApiError(error, 'Admin log rotate request failed.');
  }
}

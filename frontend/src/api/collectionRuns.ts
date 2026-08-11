import axios from 'axios';
import { AdminApiError } from '@/api/adminApiError';
import {
  buildAdminAuthorizationHeader,
  buildCollectionRunDetailPath,
  COLLECTION_RUNS_PATH,
  COLLECTION_RUN_TRIGGER_PATH,
  resolveCollectionRunListQuery,
  type AdminApiRequestOptions,
} from '@/api/adminRequest';
import { apiClient } from '@/api/client';
import {
  handleCollectionRunDetailMock,
  handleCollectionRunListMock,
  handleCollectionRunTriggerMock,
} from '@/mocks/collectionRunHandlers';
import type {
  CollectionRunDetailDto,
  CollectionRunListQuery,
  CollectionRunListResponse,
  CollectionRunTriggerRequest,
  CollectionRunTriggerResponse,
} from '@/types/collectionRun';
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

export { AdminApiError } from '@/api/adminApiError';

export async function getCollectionRuns(
  query: CollectionRunListQuery = {},
  options: AdminApiRequestOptions = {},
): Promise<CollectionRunListResponse> {
  const resolvedQuery = resolveCollectionRunListQuery(query);

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    return handleCollectionRunListMock(resolvedQuery);
  }

  try {
    const response = await apiClient.get<CollectionRunListResponse>(
      COLLECTION_RUNS_PATH,
      {
        params: resolvedQuery,
        headers: buildAdminAuthorizationHeader(options.accessToken),
      },
    );
    return response.data;
  } catch (error: unknown) {
    throw toAdminApiError(error, 'Collection run list request failed.');
  }
}

export async function getCollectionRunById(
  runId: string,
  options: AdminApiRequestOptions = {},
): Promise<CollectionRunDetailDto | null> {
  const detailPath = buildCollectionRunDetailPath(runId);

  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    const result = handleCollectionRunDetailMock(runId.trim());

    if (result.status === 404) {
      return null;
    }

    return result.body;
  }

  try {
    const response = await apiClient.get<CollectionRunDetailDto>(detailPath, {
      headers: buildAdminAuthorizationHeader(options.accessToken),
    });
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }

    throw toAdminApiError(error, 'Collection run detail request failed.');
  }
}

export async function triggerManualCollectionRun(
  request: CollectionRunTriggerRequest = {},
  options: AdminApiRequestOptions = {},
): Promise<CollectionRunTriggerResponse> {
  if (USE_MOCK) {
    await delay(MOCK_DELAY_MS);
    return handleCollectionRunTriggerMock(request);
  }

  try {
    const response = await apiClient.post<CollectionRunTriggerResponse>(
      COLLECTION_RUN_TRIGGER_PATH,
      request,
      {
        headers: buildAdminAuthorizationHeader(options.accessToken),
      },
    );
    return response.data;
  } catch (error: unknown) {
    throw toAdminApiError(error, 'Manual collection run request failed.');
  }
}

import { apiClient } from '@/api/client';
import { mockPrograms } from '@/mocks/programs';
import type { NormalizedProgram } from '@/types/policy';
import { matchesProgramIdentity } from '@/utils/programId';

const MOCK_DELAY_MS = 300;
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function fetchMockPrograms(): Promise<NormalizedProgram[]> {
  await delay(MOCK_DELAY_MS);
  return [...mockPrograms];
}

async function fetchMockProgram(
  sourceId: string,
  externalId: string,
): Promise<NormalizedProgram | null> {
  await delay(MOCK_DELAY_MS);
  return (
    mockPrograms.find((program) =>
      matchesProgramIdentity(program, sourceId, externalId),
    ) ?? null
  );
}

export async function getPrograms(): Promise<NormalizedProgram[]> {
  if (USE_MOCK) {
    return fetchMockPrograms();
  }

  const response = await apiClient.get<NormalizedProgram[]>('/api/v1/programs');
  return response.data;
}

export async function getProgramByIdentity(
  sourceId: string,
  externalId: string,
): Promise<NormalizedProgram | null> {
  if (USE_MOCK) {
    return fetchMockProgram(sourceId, externalId);
  }

  const response = await apiClient.get<NormalizedProgram>(
    `/api/v1/programs/${encodeURIComponent(sourceId)}/${encodeURIComponent(externalId)}`,
  );
  return response.data;
}

import { useQuery } from '@tanstack/react-query';
import { getCollectionRunById, getCollectionRuns } from '@/api/collectionRuns';
import { resolveCollectionRunListQuery } from '@/api/adminRequest';
import type { CollectionRunListQuery } from '@/types/collectionRun';

export function useCollectionRunsQuery(
  query: CollectionRunListQuery = {},
  accessToken?: string,
) {
  const resolvedQuery = resolveCollectionRunListQuery(query);

  return useQuery({
    queryKey: ['collectionRuns', resolvedQuery, accessToken ?? 'anonymous'],
    queryFn: () => getCollectionRuns(resolvedQuery, { accessToken }),
  });
}

export function useCollectionRunDetailQuery(runId: string, accessToken?: string) {
  const trimmedRunId = runId.trim();

  return useQuery({
    queryKey: ['collectionRun', trimmedRunId, accessToken ?? 'anonymous'],
    queryFn: () => getCollectionRunById(trimmedRunId, { accessToken }),
    enabled: trimmedRunId.length > 0,
  });
}

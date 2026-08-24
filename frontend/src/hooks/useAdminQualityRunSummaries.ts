import { useMemo } from 'react';
import { useQueries } from '@tanstack/react-query';
import { getCollectionRunById } from '@/api/collectionRuns';
import { useCollectionRunsQuery } from '@/hooks/useCollectionRunsQuery';
import type {
  CollectionRunDetailDto,
  CollectionRunListItemDto,
} from '@/types/collectionRun';

export const ADMIN_QUALITY_RUN_PAGE_SIZE = 10;

export interface CollectionRunQualitySummary {
  listItem: CollectionRunListItemDto;
  detail: CollectionRunDetailDto | null;
  detailLoading: boolean;
  detailError: boolean;
}

export function useAdminQualityRunSummaries(
  accessToken: string | undefined,
  pageSize = ADMIN_QUALITY_RUN_PAGE_SIZE,
) {
  const listQuery = useMemo(
    () => ({ page: 1, size: pageSize }),
    [pageSize],
  );

  const {
    data: listResponse,
    isLoading: isListLoading,
    isError: isListError,
    error: listError,
    refetch: refetchList,
    isFetching: isListFetching,
  } = useCollectionRunsQuery(listQuery, accessToken);

  const runIds = useMemo(
    () => listResponse?.items.map((item) => item.run_id) ?? [],
    [listResponse?.items],
  );

  const detailQueries = useQueries({
    queries: runIds.map((runId) => ({
      queryKey: ['collectionRun', runId, accessToken ?? 'anonymous'],
      queryFn: () => getCollectionRunById(runId, { accessToken }),
      enabled: runIds.length > 0,
    })),
  });

  const summaries = useMemo((): CollectionRunQualitySummary[] => {
    if (!listResponse) {
      return [];
    }

    return listResponse.items.map((listItem, index) => {
      const detailQuery = detailQueries[index];

      return {
        listItem,
        detail: detailQuery?.data ?? null,
        detailLoading: detailQuery?.isLoading ?? false,
        detailError: detailQuery?.isError ?? false,
      };
    });
  }, [detailQueries, listResponse]);

  const isDetailsLoading =
    runIds.length > 0 && detailQueries.some((query) => query.isLoading);

  const refetchAll = async () => {
    await refetchList();
    await Promise.all(detailQueries.map((query) => query.refetch()));
  };

  return {
    listResponse,
    summaries,
    isListLoading,
    isListError,
    listError,
    isDetailsLoading,
    isListFetching,
    refetchAll,
  };
}

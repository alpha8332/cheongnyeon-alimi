import { useQuery } from '@tanstack/react-query';
import { getProgramByIdentity, getPrograms } from '@/api/programs';

export function useProgramsQuery() {
  return useQuery({
    queryKey: ['programs'],
    queryFn: getPrograms,
  });
}

export function useProgramQuery(sourceId: string | null, externalId: string | null) {
  return useQuery({
    queryKey: ['program', sourceId, externalId],
    queryFn: () => getProgramByIdentity(sourceId!, externalId!),
    enabled: Boolean(sourceId && externalId),
  });
}

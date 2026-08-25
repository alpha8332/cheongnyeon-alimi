import { useQuery } from '@tanstack/react-query';
import { getAdminCollectorStatus } from '@/api/adminCollector';

export function useAdminCollectorStatusQuery(accessToken?: string) {
  return useQuery({
    queryKey: ['adminCollectors', accessToken ?? 'anonymous'],
    queryFn: () => getAdminCollectorStatus({ accessToken }),
    refetchInterval: 30_000,
  });
}


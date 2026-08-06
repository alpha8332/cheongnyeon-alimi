import { useQuery } from '@tanstack/react-query';
import { getPolicySearch } from '@/api/policySearch';
import type { PolicySearchQueryParams } from '@/types/policySearch';
import { hasPolicySearchQuery } from '@/utils/policySearchUrl';

export function usePolicySearchQuery(query: PolicySearchQueryParams) {
  const enabled = hasPolicySearchQuery({ q: query.q });

  return useQuery({
    queryKey: ['policySearch', query],
    queryFn: () => getPolicySearch(query),
    enabled,
  });
}

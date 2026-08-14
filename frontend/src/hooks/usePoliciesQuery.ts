import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getPolicies, getPolicyById } from '@/api/policies';
import { resolvePolicyListQuery } from '@/api/policyRequest';
import type { PolicyListQuery } from '@/types/policy';

export function usePoliciesQuery(query: PolicyListQuery = {}) {
  const resolvedQuery = resolvePolicyListQuery(query);

  return useQuery({
    queryKey: ['policies', resolvedQuery],
    queryFn: () => getPolicies(resolvedQuery),
  });
}

export function usePolicyQuery(
  policyId: number | null,
  includePartial = false,
) {
  return useQuery({
    queryKey: ['policy', policyId, { include_partial: includePartial }],
    queryFn: () => getPolicyById(policyId!, includePartial),
    enabled: policyId !== null,
    placeholderData: keepPreviousData,
  });
}

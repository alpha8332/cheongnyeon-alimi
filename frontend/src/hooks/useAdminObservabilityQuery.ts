import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getAdminLogEvents, getAdminLogFiles } from '@/api/adminLog';
import { getAdminPolicies, getAdminPolicyById } from '@/api/adminPolicyData';
import { resolveAdminLogEventListQuery } from '@/types/adminLog';
import type { AdminLogEventListQuery } from '@/types/adminLog';
import type { AdminPolicyListQuery } from '@/types/adminPolicyData';
import { resolveAdminPolicyListQuery } from '@/types/adminPolicyData';

export function useAdminPolicyListQuery(
  query: AdminPolicyListQuery = {},
  accessToken?: string,
) {
  const resolvedQuery = resolveAdminPolicyListQuery(query);

  return useQuery({
    queryKey: ['adminPolicies', resolvedQuery, accessToken ?? 'anonymous'],
    queryFn: () => getAdminPolicies(resolvedQuery, { accessToken }),
    placeholderData: keepPreviousData,
  });
}

export function useAdminPolicyDetailQuery(
  policyId: number | null,
  accessToken?: string,
) {
  return useQuery({
    queryKey: ['adminPolicy', policyId, accessToken ?? 'anonymous'],
    queryFn: () => getAdminPolicyById(policyId!, { accessToken }),
    enabled: policyId !== null && policyId > 0,
  });
}

export function useAdminLogFileListQuery(
  accessToken?: string,
) {
  return useQuery({
    queryKey: ['adminLogFiles', accessToken ?? 'anonymous'],
    queryFn: () => getAdminLogFiles({ accessToken }),
  });
}

export function useAdminLogEventListQuery(
  query: AdminLogEventListQuery = {},
  accessToken?: string,
) {
  const resolvedQuery = resolveAdminLogEventListQuery(query);

  return useQuery({
    queryKey: ['adminLogEvents', resolvedQuery, accessToken ?? 'anonymous'],
    queryFn: () => getAdminLogEvents(resolvedQuery, { accessToken }),
    placeholderData: keepPreviousData,
  });
}

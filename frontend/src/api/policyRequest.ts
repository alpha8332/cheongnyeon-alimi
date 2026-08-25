import type { PolicyListQuery } from '../types/policy.js';
import { isPolicySort } from '../utils/policySort.js';

export const POLICY_COLLECTION_PATH = '/api/v1/policies';

export interface ResolvedPolicyListQuery {
  page: number;
  limit: number;
  category?: PolicyListQuery['category'];
  region?: string;
  status?: PolicyListQuery['status'];
  include_partial: boolean;
  sort: NonNullable<PolicyListQuery['sort']>;
}

export function resolvePolicyListQuery(
  query: PolicyListQuery = {},
): ResolvedPolicyListQuery {
  const page = query.page ?? 1;
  const limit = query.limit ?? 10;

  if (!Number.isSafeInteger(page) || page < 1) {
    throw new Error('Policy list page must be an integer greater than 0.');
  }

  if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100) {
    throw new Error('Policy list limit must be an integer from 1 to 100.');
  }

  if (
    query.region !== undefined &&
    (query.region.length < 1 || query.region.length > 100)
  ) {
    throw new Error('Policy list region must contain from 1 to 100 characters.');
  }

  if (query.sort !== undefined && !isPolicySort(query.sort)) {
    throw new Error('Policy list sort is not supported.');
  }

  return {
    page,
    limit,
    ...(query.category ? { category: query.category } : {}),
    ...(query.region ? { region: query.region } : {}),
    ...(query.status ? { status: query.status } : {}),
    include_partial: query.include_partial ?? false,
    sort: query.sort ?? 'default',
  };
}

export function buildPolicyDetailPath(policyId: number): string {
  if (!Number.isSafeInteger(policyId) || policyId <= 0) {
    throw new Error('Policy id must be a positive integer.');
  }

  return `${POLICY_COLLECTION_PATH}/${policyId}`;
}

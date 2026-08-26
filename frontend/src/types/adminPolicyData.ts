/**
 * Admin read-only Policy data API contract (Frontend 08 / FE8-00).
 *
 * Consumer contract aligned with the current Backend OpenAPI.
 * Exposes approved Policy projection only — no provenance, Raw, or arbitrary SQL.
 *
 * @see docs/product/features/admin_data_quality_and_logs.md
 */

import type {
  ApplicationStatus,
  PolicyCategory,
  PolicyDto,
  PublicDataQualityStatus,
} from './policy.js';

export const ADMIN_POLICY_DATA_PATH = '/api/v1/admin/policies';

export const ADMIN_POLICY_DATA_ENDPOINTS = {
  list: {
    method: 'GET' as const,
    path: ADMIN_POLICY_DATA_PATH,
  },
  detail: {
    method: 'GET' as const,
    pathPrefix: `${ADMIN_POLICY_DATA_PATH}/`,
  },
} as const;

/** Table row subset for admin policy data list (W4-G0 allowlist projection). */
export interface AdminPolicyListItemDto {
  id: number;
  source_id: string;
  source_name: string;
  external_id: string | null;
  title: string;
  organization: string | null;
  categories: PolicyCategory[];
  application_status: ApplicationStatus | null;
  application_start: string | null;
  application_end: string | null;
  regions: string[];
  data_quality_status: PublicDataQualityStatus;
  collected_at: string;
  created_at: string;
  updated_at: string;
}

/** Full approved Policy projection for admin row detail. */
export type AdminPolicyDetailDto = Omit<
  PolicyDto,
  'schema_version' | 'application_period_text' | 'application_schedule'
>;

export type AdminPolicySortField =
  | 'id'
  | 'created_at'
  | 'title'
  | 'collected_at'
  | 'updated_at';

export type AdminPolicySortOrder = 'asc' | 'desc';

export interface AdminPolicyListQuery {
  page?: number;
  limit?: number;
  source_id?: string;
  category?: PolicyCategory;
  region?: string;
  status?: ApplicationStatus;
  data_quality_status?: PublicDataQualityStatus;
  sort_by?: AdminPolicySortField;
  order?: AdminPolicySortOrder;
}

export interface AdminPolicyListResponse {
  items: AdminPolicyListItemDto[];
  total: number;
  page: number;
  limit: number;
}

export const ADMIN_POLICY_SORT_FIELDS: readonly AdminPolicySortField[] = [
  'id',
  'created_at',
  'title',
  'collected_at',
  'updated_at',
] as const;

export const ADMIN_POLICY_LIST_SIZE_LIMITS = {
  min: 1,
  max: 100,
  default: 10,
} as const;

export interface ResolvedAdminPolicyListQuery {
  page: number;
  limit: number;
  source_id?: string;
  category?: PolicyCategory;
  region?: string;
  status?: ApplicationStatus;
  data_quality_status?: PublicDataQualityStatus;
  sort_by: AdminPolicySortField;
  order: AdminPolicySortOrder;
}

const POLICY_CATEGORIES = new Set<PolicyCategory>([
  'housing',
  'finance',
  'welfare',
  'employment',
  'startup',
  'education',
  'other',
]);

const APPLICATION_STATUSES = new Set<ApplicationStatus>([
  'open',
  'closed',
  'scheduled',
]);

const DATA_QUALITY_STATUSES = new Set<PublicDataQualityStatus>([
  'valid',
  'partial',
]);

const SORT_FIELDS = new Set<AdminPolicySortField>(ADMIN_POLICY_SORT_FIELDS);

export function buildAdminPolicyDetailPath(policyId: number): string {
  if (!Number.isSafeInteger(policyId) || policyId < 1) {
    throw new Error('Admin policy id must be a positive integer.');
  }

  return `${ADMIN_POLICY_DATA_ENDPOINTS.detail.pathPrefix}${policyId}`;
}

export function resolveAdminPolicyListQuery(
  query: AdminPolicyListQuery = {},
): ResolvedAdminPolicyListQuery {
  const page = query.page ?? 1;
  const limit = query.limit ?? ADMIN_POLICY_LIST_SIZE_LIMITS.default;
  const sort_by = query.sort_by ?? 'id';
  const order = query.order ?? 'desc';

  if (!Number.isSafeInteger(page) || page < 1) {
    throw new Error('Admin policy list page must be an integer greater than 0.');
  }

  if (
    !Number.isSafeInteger(limit) ||
    limit < ADMIN_POLICY_LIST_SIZE_LIMITS.min ||
    limit > ADMIN_POLICY_LIST_SIZE_LIMITS.max
  ) {
    throw new Error(
      `Admin policy list limit must be an integer from ${ADMIN_POLICY_LIST_SIZE_LIMITS.min} to ${ADMIN_POLICY_LIST_SIZE_LIMITS.max}.`,
    );
  }

  if (!SORT_FIELDS.has(sort_by)) {
    throw new Error('Admin policy list sort_by is not in the allowlist.');
  }

  if (order !== 'asc' && order !== 'desc') {
    throw new Error('Admin policy list order must be asc or desc.');
  }

  if (query.category !== undefined && !POLICY_CATEGORIES.has(query.category)) {
    throw new Error('Admin policy list category filter is invalid.');
  }

  if (query.status !== undefined && !APPLICATION_STATUSES.has(query.status)) {
    throw new Error('Admin policy list status filter is invalid.');
  }

  if (
    query.data_quality_status !== undefined &&
    !DATA_QUALITY_STATUSES.has(query.data_quality_status)
  ) {
    throw new Error('Admin policy list data_quality_status filter is invalid.');
  }

  if (
    query.source_id !== undefined &&
    (query.source_id.length < 1 || query.source_id.length > 200)
  ) {
    throw new Error('Admin policy source_id filter must contain 1 to 200 characters.');
  }

  return {
    page,
    limit,
    sort_by,
    order,
    ...(query.source_id ? { source_id: query.source_id } : {}),
    ...(query.category ? { category: query.category } : {}),
    ...(query.region ? { region: query.region } : {}),
    ...(query.status ? { status: query.status } : {}),
    ...(query.data_quality_status
      ? { data_quality_status: query.data_quality_status }
      : {}),
  };
}

export function toAdminPolicyListItem(policy: PolicyDto): AdminPolicyListItemDto {
  return {
    id: policy.id,
    source_id: policy.source_id,
    source_name: policy.source_name,
    external_id: policy.external_id,
    title: policy.title,
    organization: policy.organization,
    categories: [...policy.categories],
    application_status: policy.application_status,
    application_start: policy.application_start,
    application_end: policy.application_end,
    regions: [...policy.regions],
    data_quality_status: policy.data_quality_status,
    collected_at: policy.collected_at,
    created_at: policy.created_at,
    updated_at: policy.updated_at,
  };
}

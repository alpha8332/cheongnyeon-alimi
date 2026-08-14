import type { AdminPolicyListQuery } from '../types/adminPolicyData.js';
import type {
  ApplicationStatus,
  PolicyCategory,
  PublicDataQualityStatus,
} from '../types/policy.js';

export interface AdminPolicyFilterDraft {
  source_id: string;
  category: PolicyCategory | '';
  region: string;
  status: ApplicationStatus | '';
  data_quality_status: PublicDataQualityStatus | '';
}

export const EMPTY_ADMIN_POLICY_FILTER_DRAFT: AdminPolicyFilterDraft = {
  source_id: '',
  category: '',
  region: '',
  status: '',
  data_quality_status: '',
};

export function toAdminPolicyListQueryFromDraft(
  draft: AdminPolicyFilterDraft,
  page: number,
  size: number,
  sortBy: AdminPolicyListQuery['sort_by'],
  sortOrder: AdminPolicyListQuery['sort_order'],
): AdminPolicyListQuery {
  return {
    page,
    size,
    sort_by: sortBy,
    sort_order: sortOrder,
    ...(draft.source_id.trim() ? { source_id: draft.source_id.trim() } : {}),
    ...(draft.category ? { category: draft.category } : {}),
    ...(draft.region.trim() ? { region: draft.region.trim() } : {}),
    ...(draft.status ? { status: draft.status } : {}),
    ...(draft.data_quality_status
      ? { data_quality_status: draft.data_quality_status }
      : {}),
  };
}

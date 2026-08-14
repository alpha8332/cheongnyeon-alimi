import type { AdminPolicyListItemDto, AdminPolicySortField } from '../types/adminPolicyData.js';

export type AdminPolicyTableColumnKey = keyof AdminPolicyListItemDto;

export interface AdminPolicyTableColumnDef {
  key: AdminPolicyTableColumnKey;
  label: string;
  sortable: boolean;
  defaultVisible: boolean;
}

export const ADMIN_POLICY_TABLE_COLUMNS: readonly AdminPolicyTableColumnDef[] = [
  { key: 'id', label: 'ID', sortable: true, defaultVisible: true },
  { key: 'title', label: '제목', sortable: true, defaultVisible: true },
  { key: 'source_name', label: '출처', sortable: false, defaultVisible: true },
  { key: 'organization', label: '기관', sortable: false, defaultVisible: false },
  { key: 'categories', label: '카테고리', sortable: false, defaultVisible: false },
  {
    key: 'application_status',
    label: '신청상태',
    sortable: false,
    defaultVisible: true,
  },
  {
    key: 'application_start',
    label: '시작일',
    sortable: true,
    defaultVisible: false,
  },
  {
    key: 'application_end',
    label: '종료일',
    sortable: true,
    defaultVisible: false,
  },
  { key: 'regions', label: '지역', sortable: false, defaultVisible: false },
  { key: 'age_min', label: '최소연령', sortable: false, defaultVisible: false },
  { key: 'age_max', label: '최대연령', sortable: false, defaultVisible: false },
  {
    key: 'data_quality_status',
    label: '품질',
    sortable: false,
    defaultVisible: true,
  },
  {
    key: 'collected_at',
    label: '수집 시각',
    sortable: true,
    defaultVisible: true,
  },
  { key: 'updated_at', label: '갱신 시각', sortable: true, defaultVisible: false },
  { key: 'source_id', label: 'source_id', sortable: false, defaultVisible: false },
  { key: 'external_id', label: 'external_id', sortable: false, defaultVisible: false },
] as const;

export const DEFAULT_VISIBLE_ADMIN_POLICY_COLUMNS: AdminPolicyTableColumnKey[] =
  ADMIN_POLICY_TABLE_COLUMNS.filter((column) => column.defaultVisible).map(
    (column) => column.key,
  );

export function isAdminPolicySortField(
  columnKey: AdminPolicyTableColumnKey,
): columnKey is AdminPolicySortField {
  return ADMIN_POLICY_TABLE_COLUMNS.some(
    (column) => column.key === columnKey && column.sortable,
  );
}

export function formatAdminPolicyCellValue(
  item: AdminPolicyListItemDto,
  key: AdminPolicyTableColumnKey,
): string {
  const value = item[key];

  if (value === null || value === undefined) {
    return '—';
  }

  if (Array.isArray(value)) {
    return value.join(', ');
  }

  return String(value);
}

export function shouldExpandAdminPolicyCell(
  value: string,
  maxLength = 48,
): boolean {
  return value.length > maxLength;
}

export function truncateAdminPolicyCell(value: string, maxLength = 48): string {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength)}…`;
}

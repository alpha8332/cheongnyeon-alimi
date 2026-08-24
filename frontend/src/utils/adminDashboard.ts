import { ADMIN_APP_ROUTES } from '../api/adminRequest.js';
import type { CollectionRunDetailDto } from '../types/collectionRun.js';

export type AdminQualityMetricKey =
  | 'failed_count'
  | 'invalid_count'
  | 'duplicate_count'
  | 'inserted_count'
  | 'updated_count';

export interface AdminQualityMetricDefinition {
  key: AdminQualityMetricKey;
  label: string;
  description: string;
}

export const DASHBOARD_SUMMARY_METRICS: readonly AdminQualityMetricDefinition[] = [
  {
    key: 'failed_count',
    label: '실패',
    description: 'persist·fetch 단계 실패 건수',
  },
  {
    key: 'invalid_count',
    label: '무효',
    description: 'validate 단계 무효 건수',
  },
  {
    key: 'duplicate_count',
    label: '중복',
    description: '동일 실행 내 중복 identity 건수',
  },
  {
    key: 'inserted_count',
    label: '삽입',
    description: '신규 Policy row 삽입',
  },
  {
    key: 'updated_count',
    label: '갱신',
    description: '기존 Policy row 갱신',
  },
] as const;

export const DATA_QUALITY_COMPARE_METRICS: readonly AdminQualityMetricDefinition[] =
  DASHBOARD_SUMMARY_METRICS;

export type AdminMetricCardVariant = 'default' | 'warning' | 'danger';

export function getAdminMetricCardVariant(
  key: AdminQualityMetricKey,
  value: number,
): AdminMetricCardVariant {
  if (value <= 0) {
    return 'default';
  }

  if (key === 'failed_count') {
    return 'danger';
  }

  if (key === 'invalid_count' || key === 'duplicate_count') {
    return 'warning';
  }

  return 'default';
}

export function formatAdminMetricCount(value: number): string {
  return value.toLocaleString('ko-KR');
}

export function readAdminQualityMetricValue(
  run: CollectionRunDetailDto,
  key: AdminQualityMetricKey,
): number {
  return run[key];
}

export function buildCollectionRunDetailDrillDownUrl(runId: string): string {
  return ADMIN_APP_ROUTES.runDetail(runId);
}

export function buildAdminLogsDrillDownUrl(): string {
  return ADMIN_APP_ROUTES.logs;
}

export function shouldLinkMetricDrillDown(
  key: AdminQualityMetricKey,
  value: number,
): boolean {
  if (value <= 0) {
    return false;
  }

  return (
    key === 'failed_count' ||
    key === 'invalid_count' ||
    key === 'duplicate_count'
  );
}

export function shouldShowLogsDrillDown(run: CollectionRunDetailDto): boolean {
  return (
    run.failed_count > 0 ||
    run.status === 'failed' ||
    run.status === 'partial_failure'
  );
}

import type {
  CollectionRunStatus,
  CollectionRunTriggerType,
  CollectionRunType,
} from '../types/collectionRun.js';

const STATUS_LABELS: Record<CollectionRunStatus, string> = {
  running: '실행 중',
  succeeded: '성공',
  partial_failure: '부분 실패',
  failed: '실패',
};

const RUN_TYPE_LABELS: Record<CollectionRunType, string> = {
  seed_import: 'Seed import',
  runtime_import: 'Runtime import',
  collection: 'Collection',
};

const TRIGGER_TYPE_LABELS: Record<CollectionRunTriggerType, string> = {
  cli: 'CLI',
  scheduler: 'Scheduler',
  admin: 'Admin',
};

export function getCollectionRunStatusLabel(status: CollectionRunStatus): string {
  return STATUS_LABELS[status];
}

export function getCollectionRunTypeLabel(runType: CollectionRunType): string {
  return RUN_TYPE_LABELS[runType];
}

export function getCollectionRunTriggerTypeLabel(
  triggerType: CollectionRunTriggerType,
): string {
  return TRIGGER_TYPE_LABELS[triggerType];
}

export function isTerminalCollectionRunStatus(
  status: CollectionRunStatus,
): boolean {
  return status !== 'running';
}

export function formatAdminTimestamp(value: string | null): string {
  if (!value) {
    return '—';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString('ko-KR');
}

export function formatCollectionRunCounts(
  inserted: number,
  updated: number,
  failed: number,
): string {
  return `삽입 ${inserted} · 갱신 ${updated} · 실패 ${failed}`;
}

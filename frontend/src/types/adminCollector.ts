import type {
  CollectionRunStatus,
  CollectionRunTriggerType,
} from './collectionRun.js';

export const ADMIN_COLLECTORS_PATH = '/api/v1/admin/collectors';

export type CollectorSourceType = 'api' | 'file' | 'web';
export type CollectorRuntimeStatus =
  | 'ready'
  | 'configuration_required'
  | 'unavailable'
  | 'unknown';
export type CollectorCredentialStatus =
  | 'configured'
  | 'missing'
  | 'not_required'
  | 'unknown';

export interface CollectorQueueStatusDto {
  queue_name: string;
  broker_available: boolean;
  worker_available: boolean;
  worker_count: number;
}

export interface CollectorScheduleStatusDto {
  enabled: boolean;
  source_id: string;
  requested_count: number;
  complete_snapshot: boolean;
  cron_hour: number;
  cron_minute: number;
  timezone: string;
}

export interface CollectorRunSummaryDto {
  run_id: string;
  status: CollectionRunStatus;
  trigger_type: CollectionRunTriggerType;
  started_at: string;
  finished_at: string | null;
  is_stale: boolean;
  requested_count: number;
  inserted_count: number;
  updated_count: number;
  failed_count: number;
  error_type: string | null;
}

export interface AdminCollectorStatusDto {
  source_id: string;
  display_name: string;
  source_type: CollectorSourceType;
  manual_run_enabled: boolean;
  runtime_status: CollectorRuntimeStatus;
  worker_registered: boolean | null;
  credential_status: CollectorCredentialStatus;
  public_policy_count: number;
  active_run: CollectorRunSummaryDto | null;
  last_run: CollectorRunSummaryDto | null;
}

export interface AdminCollectorStatusResponse {
  generated_at: string;
  queue: CollectorQueueStatusDto;
  schedule: CollectorScheduleStatusDto;
  collectors: AdminCollectorStatusDto[];
}

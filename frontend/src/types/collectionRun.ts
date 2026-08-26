/**
 * CollectionRun admin API contract.
 *
 * Aligns with docs/api/admin_collection_runs.md and the current OpenAPI schema.
 *
 * List items expose a safe subset; detail includes full count aggregates.
 */

export type CollectionRunType =
  | 'seed_import'
  | 'runtime_import'
  | 'collection';

export type CollectionRunTriggerType = 'cli' | 'scheduler' | 'admin';

export type CollectionRunStatus =
  | 'queued'
  | 'running'
  | 'succeeded'
  | 'partial_failure'
  | 'failed';

export const COLLECTION_RUN_ADMIN_PATH = '/api/v1/admin/collection-runs';

export const COLLECTION_RUN_ADMIN_ENDPOINTS = {
  list: {
    method: 'GET' as const,
    path: COLLECTION_RUN_ADMIN_PATH,
  },
  detail: {
    method: 'GET' as const,
    pathPrefix: `${COLLECTION_RUN_ADMIN_PATH}/`,
  },
  trigger: {
    method: 'POST' as const,
    path: COLLECTION_RUN_ADMIN_PATH,
  },
} as const;

/** List row DTO (`CollectionRunAdminItem`). */
export interface CollectionRunListItemDto {
  run_id: string;
  source_id: string | null;
  run_type: CollectionRunType;
  trigger_type: CollectionRunTriggerType;
  started_at: string;
  finished_at: string | null;
  status: CollectionRunStatus;
  is_stale: boolean;
  is_complete_snapshot: boolean;
  inserted_count: number;
  updated_count: number;
  failed_count: number;
  error_type: string | null;
}

/** Detail DTO (`CollectionRunAdminDetail`). */
export interface CollectionRunDetailDto {
  run_id: string;
  source_id: string | null;
  run_type: CollectionRunType;
  trigger_type: CollectionRunTriggerType;
  started_at: string;
  finished_at: string | null;
  status: CollectionRunStatus;
  is_stale: boolean;
  is_complete_snapshot: boolean;
  requested_count: number;
  raw_document_count: number;
  extracted_count: number;
  accepted_count: number;
  partial_count: number;
  invalid_count: number;
  duplicate_count: number;
  rejected_count: number;
  inserted_count: number;
  updated_count: number;
  unchanged_count: number;
  skipped_count: number;
  failed_count: number;
  error_type: string | null;
}

export interface CollectionRunListQuery {
  page?: number;
  size?: number;
  source_id?: string;
  status?: CollectionRunStatus;
  run_type?: CollectionRunType;
  trigger_type?: CollectionRunTriggerType;
  start_date?: string;
  end_date?: string;
}

export interface CollectionRunListResponse {
  items: CollectionRunListItemDto[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface CollectionRunTriggerRequest {
  source_id?: string;
  requested_count?: number;
}

export interface CollectionRunTriggerResponse {
  run_id: string;
  source_id: string | null;
  run_type: CollectionRunType;
  trigger_type: CollectionRunTriggerType;
  status: CollectionRunStatus;
  started_at: string;
  message: string;
}

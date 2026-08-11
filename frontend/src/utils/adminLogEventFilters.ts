import type { AdminLogLevel } from '../types/adminLog.js';

export interface AdminLogEventFilterDraft {
  file_id: string;
  level: AdminLogLevel | '';
  component: string;
  collection_run_id: string;
  search: string;
}

export const EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT: AdminLogEventFilterDraft = {
  file_id: '',
  level: '',
  component: '',
  collection_run_id: '',
  search: '',
};

export function toAdminLogEventListQueryFromDraft(
  draft: AdminLogEventFilterDraft,
  page: number,
  size: number,
) {
  return {
    page,
    size,
    ...(draft.file_id.trim() ? { file_id: draft.file_id.trim() } : {}),
    ...(draft.level ? { level: draft.level } : {}),
    ...(draft.component.trim() ? { component: draft.component.trim() } : {}),
    ...(draft.collection_run_id.trim()
      ? { collection_run_id: draft.collection_run_id.trim() }
      : {}),
    ...(draft.search.trim() ? { search: draft.search.trim() } : {}),
  };
}

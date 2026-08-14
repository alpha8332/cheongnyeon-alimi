import type { AdminLogLevel } from '../types/adminLog.js';

export interface AdminLogEventFilterDraft {
  file_id: string;
  level: AdminLogLevel | '';
  component: string;
  search: string;
}

export const EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT: AdminLogEventFilterDraft = {
  file_id: '',
  level: '',
  component: '',
  search: '',
};

export function toAdminLogEventListQueryFromDraft(
  draft: AdminLogEventFilterDraft,
  page: number,
  limit: number,
) {
  return {
    page,
    limit,
    ...(draft.file_id.trim() ? { file_id: draft.file_id.trim() } : {}),
    ...(draft.level ? { level: draft.level } : {}),
    ...(draft.component.trim() ? { component: draft.component.trim() } : {}),
    ...(draft.search.trim() ? { q: draft.search.trim() } : {}),
  };
}

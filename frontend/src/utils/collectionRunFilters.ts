import type {
  CollectionRunStatus,
  CollectionRunTriggerType,
  CollectionRunType,
} from '../types/collectionRun.js';

export interface CollectionRunFilterDraft {
  source_id: string;
  status: CollectionRunStatus | '';
  run_type: CollectionRunType | '';
  trigger_type: CollectionRunTriggerType | '';
  start_date: string;
  end_date: string;
}

export const EMPTY_COLLECTION_RUN_FILTER_DRAFT: CollectionRunFilterDraft = {
  source_id: '',
  status: '',
  run_type: '',
  trigger_type: '',
  start_date: '',
  end_date: '',
};

export function toCollectionRunListQueryFromDraft(
  draft: CollectionRunFilterDraft,
  page: number,
  size: number,
) {
  return {
    page,
    size,
    ...(draft.source_id.trim() ? { source_id: draft.source_id.trim() } : {}),
    ...(draft.status ? { status: draft.status } : {}),
    ...(draft.run_type ? { run_type: draft.run_type } : {}),
    ...(draft.trigger_type ? { trigger_type: draft.trigger_type } : {}),
    ...(draft.start_date ? { start_date: draft.start_date } : {}),
    ...(draft.end_date ? { end_date: draft.end_date } : {}),
  };
}

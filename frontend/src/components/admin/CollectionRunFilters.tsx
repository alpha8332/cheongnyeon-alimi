import type {
  CollectionRunStatus,
  CollectionRunTriggerType,
  CollectionRunType,
} from '@/types/collectionRun';
import type { CollectionRunFilterDraft } from '@/utils/collectionRunFilters';

interface CollectionRunFiltersProps {
  draft: CollectionRunFilterDraft;
  onChange: (next: CollectionRunFilterDraft) => void;
  onApply: () => void;
  onReset: () => void;
}

const STATUS_OPTIONS: Array<{ value: CollectionRunStatus | ''; label: string }> =
  [
    { value: '', label: '전체 상태' },
    { value: 'queued', label: '대기 중' },
    { value: 'running', label: '실행 중' },
    { value: 'succeeded', label: '성공' },
    { value: 'partial_failure', label: '부분 실패' },
    { value: 'failed', label: '실패' },
  ];

const RUN_TYPE_OPTIONS: Array<{ value: CollectionRunType | ''; label: string }> =
  [
    { value: '', label: '전체 run type' },
    { value: 'collection', label: 'Collection' },
    { value: 'runtime_import', label: 'Runtime import' },
    { value: 'seed_import', label: 'Seed import' },
  ];

const TRIGGER_TYPE_OPTIONS: Array<{
  value: CollectionRunTriggerType | '';
  label: string;
}> = [
  { value: '', label: '전체 trigger' },
  { value: 'admin', label: 'Admin' },
  { value: 'scheduler', label: 'Scheduler' },
  { value: 'cli', label: 'CLI' },
];

export default function CollectionRunFilters({
  draft,
  onChange,
  onApply,
  onReset,
}: CollectionRunFiltersProps) {
  return (
    <section className="collection-run-filters" aria-label="실행 기록 필터">
      <div className="collection-run-filters__grid">
        <label className="collection-run-filters__field">
          <span className="collection-run-filters__label">source_id</span>
          <input
            className="collection-run-filters__input"
            type="text"
            value={draft.source_id}
            onChange={(event) =>
              onChange({ ...draft, source_id: event.target.value })
            }
            placeholder="예: youthcenter-api"
          />
        </label>

        <label className="collection-run-filters__field">
          <span className="collection-run-filters__label">status</span>
          <select
            className="collection-run-filters__input"
            value={draft.status}
            onChange={(event) =>
              onChange({
                ...draft,
                status: event.target.value as CollectionRunFilterDraft['status'],
              })
            }
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="collection-run-filters__field">
          <span className="collection-run-filters__label">run_type</span>
          <select
            className="collection-run-filters__input"
            value={draft.run_type}
            onChange={(event) =>
              onChange({
                ...draft,
                run_type: event.target.value as CollectionRunFilterDraft['run_type'],
              })
            }
          >
            {RUN_TYPE_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="collection-run-filters__field">
          <span className="collection-run-filters__label">trigger_type</span>
          <select
            className="collection-run-filters__input"
            value={draft.trigger_type}
            onChange={(event) =>
              onChange({
                ...draft,
                trigger_type:
                  event.target.value as CollectionRunFilterDraft['trigger_type'],
              })
            }
          >
            {TRIGGER_TYPE_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="collection-run-filters__field">
          <span className="collection-run-filters__label">start_date</span>
          <input
            className="collection-run-filters__input"
            type="date"
            value={draft.start_date}
            onChange={(event) =>
              onChange({ ...draft, start_date: event.target.value })
            }
          />
        </label>

        <label className="collection-run-filters__field">
          <span className="collection-run-filters__label">end_date</span>
          <input
            className="collection-run-filters__input"
            type="date"
            value={draft.end_date}
            onChange={(event) =>
              onChange({ ...draft, end_date: event.target.value })
            }
          />
        </label>
      </div>

      <div className="collection-run-filters__actions">
        <button type="button" className="btn btn-primary" onClick={onApply}>
          필터 적용
        </button>
        <button type="button" className="btn btn-secondary" onClick={onReset}>
          초기화
        </button>
      </div>
    </section>
  );
}

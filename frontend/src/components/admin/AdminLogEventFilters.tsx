import { ADMIN_LOG_LEVELS } from '@/types/adminLog';
import type { AdminLogEventFilterDraft } from '@/utils/adminLogEventFilters';
import type { RefObject } from 'react';

interface AdminLogEventFiltersProps {
  draft: AdminLogEventFilterDraft;
  onChange: (next: AdminLogEventFilterDraft) => void;
  onApply: () => void;
  onReset: () => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  refreshButtonRef?: RefObject<HTMLButtonElement | null>;
}

export default function AdminLogEventFilters({
  draft,
  onChange,
  onApply,
  onReset,
  onRefresh,
  isRefreshing = false,
  refreshButtonRef,
}: AdminLogEventFiltersProps) {
  return (
    <section className="admin-log-event-filters" aria-label="Log event 필터">
      <div className="admin-log-event-filters__grid">
        <label className="admin-log-event-filters__field">
          <span className="admin-log-event-filters__label">file_id</span>
          <input
            className="admin-log-event-filters__input"
            type="text"
            value={draft.file_id}
            onChange={(event) =>
              onChange({ ...draft, file_id: event.target.value })
            }
          />
        </label>

        <label className="admin-log-event-filters__field">
          <span className="admin-log-event-filters__label">level</span>
          <select
            className="admin-log-event-filters__input"
            value={draft.level}
            onChange={(event) =>
              onChange({
                ...draft,
                level: event.target.value as AdminLogEventFilterDraft['level'],
              })
            }
          >
            <option value="">전체</option>
            {ADMIN_LOG_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </label>

        <label className="admin-log-event-filters__field">
          <span className="admin-log-event-filters__label">component</span>
          <input
            className="admin-log-event-filters__input"
            type="text"
            value={draft.component}
            onChange={(event) =>
              onChange({ ...draft, component: event.target.value })
            }
          />
        </label>

        <label className="admin-log-event-filters__field">
          <span className="admin-log-event-filters__label">collection_run_id</span>
          <input
            className="admin-log-event-filters__input"
            type="text"
            value={draft.collection_run_id}
            onChange={(event) =>
              onChange({ ...draft, collection_run_id: event.target.value })
            }
          />
        </label>

        <label className="admin-log-event-filters__field">
          <span className="admin-log-event-filters__label">search</span>
          <input
            className="admin-log-event-filters__input"
            type="search"
            value={draft.search}
            onChange={(event) =>
              onChange({ ...draft, search: event.target.value })
            }
          />
        </label>
      </div>

      <div className="admin-log-event-filters__actions">
        <button type="button" className="btn btn-primary" onClick={onApply}>
          필터 적용
        </button>
        <button type="button" className="btn btn-secondary" onClick={onReset}>
          초기화
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          ref={refreshButtonRef}
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          {isRefreshing ? '새로고침 중…' : '새로고침'}
        </button>
      </div>
    </section>
  );
}

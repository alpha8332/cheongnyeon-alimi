import type { PolicyCategory } from '@/types/policy';
import type { AdminPolicyFilterDraft } from '@/utils/adminPolicyFilters';

interface AdminPolicyDataFiltersProps {
  draft: AdminPolicyFilterDraft;
  onChange: (next: AdminPolicyFilterDraft) => void;
  onApply: () => void;
  onReset: () => void;
}

const CATEGORY_OPTIONS: PolicyCategory[] = [
  'housing',
  'finance',
  'welfare',
  'employment',
  'startup',
  'education',
  'other',
];

export default function AdminPolicyDataFilters({
  draft,
  onChange,
  onApply,
  onReset,
}: AdminPolicyDataFiltersProps) {
  return (
    <section className="admin-policy-filters" aria-label="정책 데이터 필터">
      <div className="admin-policy-filters__grid">
        <label className="admin-policy-filters__field">
          <span className="admin-policy-filters__label">source_id</span>
          <input
            className="admin-policy-filters__input"
            type="text"
            value={draft.source_id}
            onChange={(event) =>
              onChange({ ...draft, source_id: event.target.value })
            }
          />
        </label>

        <label className="admin-policy-filters__field">
          <span className="admin-policy-filters__label">category</span>
          <select
            className="admin-policy-filters__input"
            value={draft.category}
            onChange={(event) =>
              onChange({
                ...draft,
                category: event.target.value as AdminPolicyFilterDraft['category'],
              })
            }
          >
            <option value="">전체</option>
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="admin-policy-filters__field">
          <span className="admin-policy-filters__label">region</span>
          <input
            className="admin-policy-filters__input"
            type="text"
            value={draft.region}
            onChange={(event) =>
              onChange({ ...draft, region: event.target.value })
            }
          />
        </label>

        <label className="admin-policy-filters__field">
          <span className="admin-policy-filters__label">status</span>
          <select
            className="admin-policy-filters__input"
            value={draft.status}
            onChange={(event) =>
              onChange({
                ...draft,
                status: event.target.value as AdminPolicyFilterDraft['status'],
              })
            }
          >
            <option value="">전체</option>
            <option value="open">open</option>
            <option value="closed">closed</option>
            <option value="scheduled">scheduled</option>
          </select>
        </label>

        <label className="admin-policy-filters__field">
          <span className="admin-policy-filters__label">data_quality_status</span>
          <select
            className="admin-policy-filters__input"
            value={draft.data_quality_status}
            onChange={(event) =>
              onChange({
                ...draft,
                data_quality_status:
                  event.target.value as AdminPolicyFilterDraft['data_quality_status'],
              })
            }
          >
            <option value="">전체</option>
            <option value="valid">valid</option>
            <option value="partial">partial</option>
          </select>
        </label>
      </div>

      <div className="admin-policy-filters__actions">
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

import type { ConditionAnalysisRow } from '@/utils/policySearchReason';
import './PolicySearchSidebar.css';

interface SearchReasonBlockProps {
  rows: ConditionAnalysisRow[];
  reasonMessage: string | null;
  selectedTitle: string | null;
}

function getCheckDotClass(status: ConditionAnalysisRow['status']): string {
  switch (status) {
    case 'match':
    case 'keyword':
      return 'check-dot check-dot--ok';
    case 'mismatch':
    case 'unknown':
    case 'ambiguous':
    case 'unmapped':
      return 'check-dot check-dot--warn';
    default:
      return 'check-dot check-dot--neutral';
  }
}

export default function SearchReasonBlock({
  rows,
  reasonMessage,
  selectedTitle,
}: SearchReasonBlockProps) {
  return (
    <section className="panel policy-search-sidebar__panel">
      <h3 className="panel-title">✅ 자격 조건 &amp; 키워드</h3>

      {selectedTitle ? (
        <p className="policy-search-sidebar__selected">
          선택 정책: <strong>{selectedTitle}</strong>
        </p>
      ) : (
        <p className="policy-search-sidebar__selected policy-search-sidebar__selected--muted">
          정책을 선택하면 항목별 판정이 표시됩니다.
        </p>
      )}

      {rows.length > 0 ? (
        <ul className="policy-search-checklist">
          {rows.map((row) => (
            <li key={row.id} className="policy-search-check-item">
              <span className={getCheckDotClass(row.status)} aria-hidden="true" />
              <span>{row.label}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="policy-search-sidebar__empty">
          해석된 검색 조건이 없습니다.
        </p>
      )}

      {reasonMessage ? (
        <p className="policy-search-sidebar__reason">{reasonMessage}</p>
      ) : null}
    </section>
  );
}

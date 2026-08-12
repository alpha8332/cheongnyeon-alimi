import { useEffect } from 'react';
import type { AdminPolicyDetailDto } from '@/types/adminPolicyData';
import {
  formatApplicationStatus,
  formatCategoryTags,
  formatCollectedAt,
  formatOrganization,
  formatRegion,
  getCategoryLabel,
} from '@/utils/policyDisplay';

interface AdminPolicyRowDetailProps {
  policy: AdminPolicyDetailDto | null | undefined;
  isOpen: boolean;
  isLoading: boolean;
  isNotFound: boolean;
  onClose: () => void;
}

export default function AdminPolicyRowDetail({
  policy,
  isOpen,
  isLoading,
  isNotFound,
  onClose,
}: AdminPolicyRowDetailProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen && !policy && !isLoading && !isNotFound) {
    return null;
  }

  return (
    <div
      className={
        isOpen
          ? 'admin-policy-row-detail-drawer admin-policy-row-detail-drawer--open'
          : 'admin-policy-row-detail-drawer'
      }
      aria-hidden={!isOpen}
    >
      <button
        type="button"
        className="admin-policy-row-detail-drawer__backdrop"
        aria-label="Policy row 상세 닫기"
        tabIndex={isOpen ? 0 : -1}
        onClick={onClose}
      />

      <aside
        className="admin-policy-row-detail-drawer__panel admin-policy-row-detail"
        aria-label="Policy row 상세"
        role="dialog"
        aria-modal="true"
      >
        <header className="admin-policy-row-detail__header">
          <h2 className="admin-policy-row-detail__title">Policy row 상세</h2>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            닫기
          </button>
        </header>

        {isLoading ? <p role="status">상세를 불러오는 중입니다…</p> : null}

        {isNotFound ? (
          <p className="admin-policy-row-detail__error" role="alert">
            선택한 Policy row를 찾을 수 없습니다.
          </p>
        ) : null}

        {policy ? (
          <dl className="admin-policy-row-detail__grid">
            <div>
              <dt>id</dt>
              <dd>{policy.id}</dd>
            </div>
            <div>
              <dt>title</dt>
              <dd>{policy.title}</dd>
            </div>
            <div>
              <dt>source</dt>
              <dd>
                {policy.source_name} ({policy.source_id})
              </dd>
            </div>
            <div>
              <dt>organization</dt>
              <dd>{formatOrganization(policy)}</dd>
            </div>
            <div>
              <dt>categories</dt>
              <dd>{formatCategoryTags(policy).join(', ')}</dd>
            </div>
            <div>
              <dt>application_status</dt>
              <dd>
                {policy.application_status
                  ? formatApplicationStatus(policy.application_status)
                  : '—'}
              </dd>
            </div>
            <div>
              <dt>application period</dt>
              <dd>
                {policy.application_start ?? '—'} ~ {policy.application_end ?? '—'}
              </dd>
            </div>
            <div>
              <dt>regions</dt>
              <dd>{formatRegion(policy)}</dd>
            </div>
            <div>
              <dt>age range</dt>
              <dd>
                {policy.age_min ?? '—'} ~ {policy.age_max ?? '—'}
              </dd>
            </div>
            <div>
              <dt>data_quality_status</dt>
              <dd>{policy.data_quality_status}</dd>
            </div>
            <div>
              <dt>collected_at</dt>
              <dd>{formatCollectedAt(policy.collected_at)}</dd>
            </div>
            <div>
              <dt>updated_at</dt>
              <dd>{formatCollectedAt(policy.updated_at)}</dd>
            </div>
            {policy.summary ? (
              <div className="admin-policy-row-detail__full">
                <dt>summary</dt>
                <dd>{policy.summary}</dd>
              </div>
            ) : null}
            {policy.category_text ? (
              <div>
                <dt>category_text</dt>
                <dd>{policy.category_text}</dd>
              </div>
            ) : null}
            {policy.categories[0] ? (
              <div>
                <dt>primary category</dt>
                <dd>{getCategoryLabel(policy.categories[0])}</dd>
              </div>
            ) : null}
          </dl>
        ) : null}

        <p className="admin-policy-row-detail__note" role="note">
          provenance·Raw payload·internal DB field는 표시하지 않습니다.
        </p>
      </aside>
    </div>
  );
}

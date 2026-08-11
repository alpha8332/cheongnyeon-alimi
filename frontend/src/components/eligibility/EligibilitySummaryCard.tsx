import Button from '@/components/common/Button';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import EligibilityComparisonBadge from '@/components/eligibility/EligibilityComparisonBadge';
import EligibilitySectionList from '@/components/eligibility/EligibilitySectionList';
import type { EligibilitySummaryDto } from '@/types/eligibilitySummary';
import type { PolicyDto } from '@/types/policy';
import type { UserSavedConditions } from '@/types/userLocalStorage';
import {
  compareSavedPolicyCategory,
  hasSavedConditionsForComparison,
} from '@/utils/eligibilityComparison';
import { ELIGIBILITY_SUMMARY_STATUS_LABELS } from '@/utils/eligibilitySummaryDisplay';

interface EligibilitySummaryCardProps {
  policy: PolicyDto;
  summary: EligibilitySummaryDto | null | undefined;
  savedConditions: UserSavedConditions | null;
  isLoading?: boolean;
  errorMessage?: string | null;
  onRetry?: () => void;
}

export default function EligibilitySummaryCard({
  policy,
  summary,
  savedConditions,
  isLoading = false,
  errorMessage = null,
  onRetry,
}: EligibilitySummaryCardProps) {
  if (isLoading) {
    return (
      <LoadingState message="핵심 신청 조건을 불러오는 중입니다." />
    );
  }

  if (errorMessage) {
    return <ErrorState message={errorMessage} onRetry={onRetry} />;
  }

  if (!summary) {
    return (
      <EmptyState message="구조화된 핵심 신청 조건이 아직 제공되지 않습니다." />
    );
  }

  const categoryComparison =
    savedConditions && hasSavedConditionsForComparison(savedConditions)
      ? compareSavedPolicyCategory(policy, savedConditions)
      : null;

  return (
    <article className="eligibility-summary-card" aria-labelledby="eligibility-summary-title">
      <header className="eligibility-summary-card__header">
        <h2 id="eligibility-summary-title" className="eligibility-summary-card__title">
          핵심 신청 조건
        </h2>
        <span
          className={`eligibility-summary-card__status eligibility-summary-card__status--${summary.status}`}
        >
          {ELIGIBILITY_SUMMARY_STATUS_LABELS[summary.status]}
        </span>
      </header>

      {summary.status === 'partial' ? (
        <p className="eligibility-summary-card__banner" role="note">
          일부 조건은 원문 확인 또는 추가 검증이 필요합니다. 신청 가능 여부를
          단정하지 않습니다.
        </p>
      ) : null}

      {summary.status === 'unknown' ? (
        <p className="eligibility-summary-card__banner eligibility-summary-card__banner--unknown" role="note">
          자격요건을 구조화할 수 없습니다. 공식 원문 또는 담당 기관 안내를
          확인해 주세요.
        </p>
      ) : null}

      {categoryComparison ? (
        <div className="eligibility-summary-card__saved-category">
          <span className="eligibility-summary-card__saved-category-label">
            저장된 관심 분야
          </span>
          <EligibilityComparisonBadge status={categoryComparison} />
        </div>
      ) : null}

      <EligibilitySectionList
        summary={summary}
        policy={policy}
        savedConditions={savedConditions}
      />

      {summary.institutional_contacts.length > 0 ? (
        <section className="eligibility-summary-card__contacts" aria-label="기관 연락처">
          <h3 className="eligibility-summary-card__contacts-title">기관 안내</h3>
          <ul className="eligibility-summary-card__contacts-list">
            {summary.institutional_contacts.map((contact) => (
              <li key={`${contact.label}-${contact.value}`}>
                <span className="eligibility-summary-card__contact-label">
                  {contact.label}
                </span>
                {contact.contact_type === 'url' ? (
                  <a
                    href={contact.value}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="eligibility-summary-card__contact-link"
                  >
                    {contact.value}
                  </a>
                ) : (
                  <span className="eligibility-summary-card__contact-value">
                    {contact.value}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <footer className="eligibility-summary-card__footer">
        <Button
          variant="gradient"
          onClick={() => {
            window.open(policy.source_url, '_blank', 'noopener,noreferrer');
          }}
        >
          공식 원문 확인
        </Button>
        <p className="eligibility-summary-card__footer-note" role="note">
          위 조건은 안내용이며 최종 신청 가능 여부를 확정하지 않습니다.
        </p>
      </footer>
    </article>
  );
}

import type { EligibilityComparisonStatus } from '@/utils/eligibilityComparison';
import { ELIGIBILITY_COMPARISON_LABELS } from '@/utils/eligibilityComparison';

interface EligibilityComparisonBadgeProps {
  status: EligibilityComparisonStatus;
}

const BADGE_ICONS: Record<EligibilityComparisonStatus, string> = {
  match: '✓',
  mismatch: '!',
  needs_review: '?',
};

export default function EligibilityComparisonBadge({
  status,
}: EligibilityComparisonBadgeProps) {
  return (
    <span
      className={`eligibility-comparison-badge eligibility-comparison-badge--${status}`}
      role="status"
      aria-label={ELIGIBILITY_COMPARISON_LABELS[status]}
      title={ELIGIBILITY_COMPARISON_LABELS[status]}
    >
      <span className="eligibility-comparison-badge__icon" aria-hidden="true">
        {BADGE_ICONS[status]}
      </span>
      <span className="eligibility-comparison-badge__label">
        {ELIGIBILITY_COMPARISON_LABELS[status]}
      </span>
    </span>
  );
}

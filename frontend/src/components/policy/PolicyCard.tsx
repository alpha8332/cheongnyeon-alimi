import { Link } from 'react-router';
import FavoriteToggleButton from '@/components/policy/FavoriteToggleButton';
import PartialBadge from '@/components/policy/PartialBadge';
import PolicyCategoryBadge from '@/components/policy/PolicyCategoryBadge';
import PolicyStatusBadge from '@/components/policy/PolicyStatusBadge';
import type { PolicyCategory, PolicyDto } from '@/types/policy';
import { buildProgramDetailRoutePath } from '@/utils/policyDetailNavigation';
import { getPolicyCardDDayBadgeLabel } from '@/utils/policyDeadline';
import {
  formatAge,
  formatApplicationPeriodCard,
  formatOrganization,
  formatRegionSummary,
  getPolicyCategoryDisplayOrder,
} from '@/utils/policyDisplay';

interface PolicyCardProps {
  policy: PolicyDto;
  highlightedCategory?: PolicyCategory | null;
}

export default function PolicyCard({
  policy,
  highlightedCategory = null,
}: PolicyCardProps) {
  const detailPath = buildProgramDetailRoutePath(policy.id, {
    includePartial: policy.data_quality_status === 'partial',
  });
  const categories = getPolicyCategoryDisplayOrder(policy, highlightedCategory);
  const dDayBadgeLabel = getPolicyCardDDayBadgeLabel(policy);

  return (
    <article className="policy-card">
      <div className="policy-card__visual">
        <div className="policy-card__visual-badges">
          <PolicyStatusBadge policy={policy} compact />
          {categories.map((category) => (
            <PolicyCategoryBadge key={category} category={category} compact />
          ))}
        </div>
      </div>
      <div className="policy-card__body">
        <h3 className="policy-card__title">
          <Link to={detailPath}>{policy.title}</Link>
          <PartialBadge policy={policy} />
          <span className="policy-card__title-actions">
            {dDayBadgeLabel ? (
              <span className="policy-card__dday" aria-label={`마감 ${dDayBadgeLabel}`}>
                {dDayBadgeLabel}
              </span>
            ) : null}
            <FavoriteToggleButton policyId={policy.id} />
          </span>
        </h3>
        <p className="policy-card__period">{formatApplicationPeriodCard(policy)}</p>
        <p className="policy-card__meta">
          {[formatRegionSummary(policy), formatOrganization(policy)].filter(Boolean).join(' · ')}
        </p>
        <div className="policy-card__footer">
          <span className="policy-card__eligibility">
            {formatAge(policy)} · {formatRegionSummary(policy)}
          </span>
          <Link to={detailPath} className="policy-card__arrow" aria-label="상세 보기">
            →
          </Link>
        </div>
      </div>
    </article>
  );
}

import { Link } from 'react-router';
import FavoriteToggleButton from '@/components/policy/FavoriteToggleButton';
import PartialBadge from '@/components/policy/PartialBadge';
import PolicyCategoryBadge from '@/components/policy/PolicyCategoryBadge';
import PolicyStatusBadge from '@/components/policy/PolicyStatusBadge';
import type { PolicyDto } from '@/types/policy';
import { getPrimaryPolicyCategory } from '@/utils/calendarCategoryTheme';
import { buildProgramDetailRoutePath } from '@/utils/policyDetailNavigation';
import {
  formatAge,
  formatApplicationPeriodCard,
  formatOrganization,
  formatRegion,
  getDDayLabel,
} from '@/utils/policyDisplay';

interface PolicyCardProps {
  policy: PolicyDto;
}

export default function PolicyCard({ policy }: PolicyCardProps) {
  const detailPath = buildProgramDetailRoutePath(policy.id, {
    includePartial: policy.data_quality_status === 'partial',
  });
  const primaryCategory = getPrimaryPolicyCategory(policy);

  return (
    <article className="policy-card">
      <div className="policy-card__visual">
        <div className="policy-card__visual-badges">
          <PolicyStatusBadge policy={policy} compact />
          <PolicyCategoryBadge category={primaryCategory} compact />
        </div>
      </div>
      <div className="policy-card__body">
        <h3 className="policy-card__title">
          <Link to={detailPath}>{policy.title}</Link>
          <PartialBadge policy={policy} />
          <FavoriteToggleButton policyId={policy.id} />
        </h3>
        <p className="policy-card__period">{formatApplicationPeriodCard(policy)}</p>
        <p className="policy-card__meta">
          {[formatRegion(policy), formatOrganization(policy), getDDayLabel(policy)]
            .filter(Boolean)
            .join(' · ')}
        </p>
        <div className="policy-card__footer">
          <span className="policy-card__eligibility">
            {formatAge(policy)} · {formatRegion(policy)}
          </span>
          <Link to={detailPath} className="policy-card__arrow" aria-label="상세 보기">
            →
          </Link>
        </div>
      </div>
    </article>
  );
}

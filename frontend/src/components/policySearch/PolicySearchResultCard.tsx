import { Link } from 'react-router';
import PartialBadge from '@/components/policy/PartialBadge';
import PolicyCategoryBadge from '@/components/policy/PolicyCategoryBadge';
import PolicyStatusBadge from '@/components/policy/PolicyStatusBadge';
import { RegionUnconfirmedBadge } from '@/components/policySearch/PolicySearchBadges';
import type { PolicyCategory } from '@/types/policy';
import type { PolicySearchHit } from '@/types/policySearch';
import { buildPolicySearchHitDetailPath } from '@/utils/policyDetailNavigation';
import {
  formatAge,
  formatApplicationPeriodCard,
  formatOrganization,
  formatRegionSummary,
  getDDayLabel,
  getPolicyCategoryDisplayOrder,
} from '@/utils/policyDisplay';

function formatCardMeta(hit: PolicySearchHit): string {
  return [
    formatRegionSummary(hit.policy),
    formatOrganization(hit.policy),
    getDDayLabel(hit.policy),
  ]
    .filter(Boolean)
    .join(' · ');
}

interface PolicySearchResultCardProps {
  hit: PolicySearchHit;
  searchIncludePartial?: boolean;
  isSelected?: boolean;
  onSelect?: (hit: PolicySearchHit) => void;
  highlightedCategory?: PolicyCategory | null;
}

export default function PolicySearchResultCard({
  hit,
  searchIncludePartial = false,
  isSelected = false,
  onSelect,
  highlightedCategory = null,
}: PolicySearchResultCardProps) {
  const detailPath = buildPolicySearchHitDetailPath(hit, searchIncludePartial);
  const isHoverSelectable = Boolean(onSelect);
  const categories = getPolicyCategoryDisplayOrder(
    hit.policy,
    highlightedCategory,
  );
  const showPartialBadge = hit.policy.data_quality_status === 'partial';

  return (
    <Link
      to={detailPath}
      className={`policy-card policy-card--selectable${isSelected ? ' policy-card--selected' : ''}`}
      aria-label={`${hit.policy.title} 상세 보기`}
      onMouseEnter={isHoverSelectable ? () => onSelect?.(hit) : undefined}
      onFocus={isHoverSelectable ? () => onSelect?.(hit) : undefined}
    >
      <div className="policy-card__visual">
        <div className="policy-card__visual-badges">
          <PolicyStatusBadge policy={hit.policy} compact />
          {categories.map((category) => (
            <PolicyCategoryBadge key={category} category={category} compact />
          ))}
          {hit.verdicts.region === 'unknown' ? <RegionUnconfirmedBadge /> : null}
        </div>
      </div>
      <div className="policy-card__body">
        <h3 className="policy-card__title">
          {hit.policy.title}
          {showPartialBadge ? <PartialBadge policy={hit.policy} /> : null}
        </h3>

        <p className="policy-card__period">
          {formatApplicationPeriodCard(hit.policy)}
        </p>
        <p className="policy-card__meta">{formatCardMeta(hit)}</p>
        <div className="policy-card__footer">
          <span className="policy-card__eligibility">
            {`${formatAge(hit.policy)} · ${formatRegionSummary(hit.policy)}`}
          </span>
          <span className="policy-card__arrow" aria-hidden="true">
            →
          </span>
        </div>
      </div>
    </Link>
  );
}

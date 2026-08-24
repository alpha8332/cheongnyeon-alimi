import { Link } from 'react-router';
import FavoriteToggleButton from '@/components/policy/FavoriteToggleButton';
import PolicyCategoryBadge from '@/components/policy/PolicyCategoryBadge';
import PolicyStatusBadge from '@/components/policy/PolicyStatusBadge';
import RecommendationUnknownConditionsAccordion from '@/components/recommendation/RecommendationUnknownConditionsAccordion';
import RegionListCollapse from '@/components/recommendation/RegionListCollapse';
import {
  PARTIAL_QUALITY_BADGE_HELP,
  PARTIAL_QUALITY_BADGE_LABEL,
} from '@/constants/policySearchDisplay';
import type { PolicyCategory } from '@/types/policy';
import type { RecommendationItemDto } from '@/types/recommendation';
import { buildRecommendationItemDetailPath } from '@/utils/policyDetailNavigation';
import { getPolicyDeadlineInfo } from '@/utils/policyDeadline';
import {
  formatApplicationPeriodCard,
  getCategoryLabel,
} from '@/utils/policyDisplay';
import {
  formatRecommendationAge,
  formatRecommendationReasonSummary,
  hasRecommendationUnknownConditions,
} from '@/utils/recommendationReasonHelpers';
import {
  normalizeRecommendationCategory,
  recommendationItemToPolicyDto,
} from '@/utils/recommendationPolicyMapping';

interface RecommendationResultCardProps {
  item: RecommendationItemDto;
}

function formatRecommendationDDay(item: RecommendationItemDto): string {
  return getPolicyDeadlineInfo(recommendationItemToPolicyDto(item)).label;
}

function formatCategoryLabel(category: string): string {
  const known = [
    'housing',
    'finance',
    'welfare',
    'employment',
    'startup',
    'education',
    'other',
  ] as const;

  if (known.includes(category as (typeof known)[number])) {
    return getCategoryLabel(category as PolicyCategory);
  }

  return category;
}

export default function RecommendationResultCard({
  item,
}: RecommendationResultCardProps) {
  const detailPath = buildRecommendationItemDetailPath(item);
  const policy = recommendationItemToPolicyDto(item);
  const showPartial = item.data_quality_status === 'partial';
  const showUnknown = hasRecommendationUnknownConditions(item);
  const reasonSummary = formatRecommendationReasonSummary(item);
  const dDay = formatRecommendationDDay(item);
  const category = normalizeRecommendationCategory(item.category);

  return (
    <article className="policy-card recommendation-result-card">
      <div className="policy-card__visual">
        <div className="policy-card__visual-badges">
          <PolicyStatusBadge policy={policy} compact />
          <PolicyCategoryBadge category={category} compact />
        </div>
      </div>
      <div className="policy-card__body">
        <h3 className="policy-card__title">
          <Link to={detailPath}>{item.title}</Link>
          {showPartial ? (
            <span className="badge-partial" title={PARTIAL_QUALITY_BADGE_HELP}>
              {PARTIAL_QUALITY_BADGE_LABEL}
            </span>
          ) : null}
          <FavoriteToggleButton policyId={item.id} />
        </h3>

        {showUnknown ? (
          <RecommendationUnknownConditionsAccordion conditions={item.unknown_conditions} />
        ) : null}

        <p className="policy-card__period">{formatApplicationPeriodCard(policy)}</p>
        <p className="policy-card__meta">
          <RegionListCollapse regions={item.regions} /> · {formatCategoryLabel(item.category)}
          {dDay ? ` · ${dDay}` : ''}
        </p>

        {item.lead ? (
          <p className="recommendation-result-card__lead">{item.lead}</p>
        ) : null}

        <p className="recommendation-result-card__reason" role="note">
          {reasonSummary}
        </p>

        <div className="policy-card__footer">
          <span className="policy-card__eligibility">
            {formatRecommendationAge(item)}
          </span>
          <Link to={detailPath} className="policy-card__arrow" aria-label="상세 보기">
            →
          </Link>
        </div>
      </div>
    </article>
  );
}

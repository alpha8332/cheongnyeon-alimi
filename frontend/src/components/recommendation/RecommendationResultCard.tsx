import { Link } from 'react-router';
import FavoriteToggleButton from '@/components/policy/FavoriteToggleButton';
import PolicyCategoryBadge from '@/components/policy/PolicyCategoryBadge';
import PolicyStatusBadge from '@/components/policy/PolicyStatusBadge';
import RecommendationUnknownConditionsAccordion from '@/components/recommendation/RecommendationUnknownConditionsAccordion';
import RegionListCollapse from '@/components/policy/RegionListCollapse';
import {
  PARTIAL_QUALITY_BADGE_HELP,
  PARTIAL_QUALITY_BADGE_LABEL,
} from '@/constants/policySearchDisplay';
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
  hasRecommendationUnconfirmedRegion,
  hasRecommendationUnknownConditions,
} from '@/utils/recommendationReasonHelpers';
import { recommendationItemToPolicyDto } from '@/utils/recommendationPolicyMapping';

interface RecommendationResultCardProps {
  item: RecommendationItemDto;
}

function formatRecommendationDDay(item: RecommendationItemDto): string {
  return getPolicyDeadlineInfo(recommendationItemToPolicyDto(item)).label;
}

export default function RecommendationResultCard({
  item,
}: RecommendationResultCardProps) {
  const detailPath = buildRecommendationItemDetailPath(item);
  const policy = recommendationItemToPolicyDto(item);
  const showPartial = item.data_quality_status === 'partial';
  const showUnknown = hasRecommendationUnknownConditions(item);
  const showUnconfirmedRegion = hasRecommendationUnconfirmedRegion(item);
  const reasonSummary = formatRecommendationReasonSummary(item);
  const dDay = formatRecommendationDDay(item);

  return (
    <article className="policy-card recommendation-result-card">
      <div className="policy-card__visual">
        <div className="policy-card__visual-badges">
          <PolicyStatusBadge policy={policy} compact />
          {policy.categories.map((category) => (
            <PolicyCategoryBadge key={category} category={category} compact />
          ))}
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
          {showUnconfirmedRegion ? (
            <span
              className="recommendation-region-unconfirmed-badge"
              title="출처 데이터에 지역 정보가 없어 선택한 거주지와의 일치 여부를 확인할 수 없습니다."
            >
              지역 일치 미확인
            </span>
          ) : null}
          <FavoriteToggleButton policyId={item.id} />
        </h3>

        {showUnknown ? (
          <RecommendationUnknownConditionsAccordion conditions={item.unknown_conditions} />
        ) : null}

        <p className="policy-card__period">{formatApplicationPeriodCard(policy)}</p>
        <p className="policy-card__meta">
          <RegionListCollapse regions={item.regions} /> ·{' '}
          {policy.categories.map(getCategoryLabel).join(', ')}
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

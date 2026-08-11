import { Link } from 'react-router';
import FavoriteToggleButton from '@/components/policy/FavoriteToggleButton';
import RegionListCollapse from '@/components/recommendation/RegionListCollapse';
import {
  PARTIAL_QUALITY_BADGE_HELP,
  PARTIAL_QUALITY_BADGE_LABEL,
} from '@/constants/policySearchDisplay';
import type { ApplicationStatus, PolicyCategory, PolicyDto } from '@/types/policy';
import type { RecommendationItemDto } from '@/types/recommendation';
import { buildRecommendationItemDetailPath } from '@/utils/policyDetailNavigation';
import { getPolicyDeadlineInfo } from '@/utils/policyDeadline';
import {
  formatApplicationStatus,
  getCategoryLabel,
} from '@/utils/policyDisplay';
import {
  formatRecommendationReasonSummary,
  hasRecommendationUnknownConditions,
} from '@/utils/recommendationReasonHelpers';

interface RecommendationResultCardProps {
  item: RecommendationItemDto;
}

function formatRecommendationDDay(item: RecommendationItemDto): string {
  const deadlinePolicy = {
    application_end: item.application_end,
    application_status: item.application_status as ApplicationStatus,
    application_schedule: 'fixed_period',
  } as PolicyDto;

  return getPolicyDeadlineInfo(deadlinePolicy).label;
}

function getStatusLabel(item: RecommendationItemDto): string {
  if (item.application_status) {
    return formatApplicationStatus(
      item.application_status as 'open' | 'closed' | 'scheduled',
    );
  }

  return '정책';
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
  const showPartial = item.data_quality_status === 'partial';
  const showUnknown = hasRecommendationUnknownConditions(item);
  const reasonSummary = formatRecommendationReasonSummary(item);
  const dDay = formatRecommendationDDay(item);

  return (
    <article className="policy-card recommendation-result-card">
      <div className="policy-card__visual">
        <span className="policy-card__tag">{getStatusLabel(item)}</span>
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
          <div
            className="recommendation-result-card__unknown"
            role="note"
            aria-label="미확정 조건"
          >
            <span className="recommendation-result-card__unknown-badge">
              추가 확인 필요
            </span>
            <ul className="recommendation-result-card__unknown-list">
              {item.unknown_conditions.map((condition) => (
                <li key={condition}>{condition}</li>
              ))}
            </ul>
          </div>
        ) : null}

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
            {item.min_age !== null || item.max_age !== null
              ? `${item.min_age ?? '—'}~${item.max_age ?? '—'}세`
              : '연령 정보 없음'}
          </span>
          <Link to={detailPath} className="policy-card__arrow" aria-label="상세 보기">
            →
          </Link>
        </div>
      </div>
    </article>
  );
}

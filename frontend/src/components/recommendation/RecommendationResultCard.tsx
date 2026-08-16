import { Link } from 'react-router';
import FavoriteToggleButton from '@/components/policy/FavoriteToggleButton';
import PolicyCategoryBadge from '@/components/policy/PolicyCategoryBadge';
import PolicyStatusBadge from '@/components/policy/PolicyStatusBadge';
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
  formatApplicationPeriodCard,
  getCategoryLabel,
} from '@/utils/policyDisplay';
import {
  formatRecommendationReasonSummary,
  hasRecommendationUnknownConditions,
} from '@/utils/recommendationReasonHelpers';

interface RecommendationResultCardProps {
  item: RecommendationItemDto;
}

function toPolicyDto(item: RecommendationItemDto): PolicyDto {
  return {
    schema_version: '1.2.0',
    source_id: item.source_id,
    source_name: item.source_id,
    external_id: item.external_id,
    title: item.title,
    organization: null,
    summary: null,
    category_text: null,
    categories: [item.category as PolicyCategory],
    application_period_text: null,
    application_start: item.application_start,
    application_end: item.application_end,
    application_schedule: 'fixed_period',
    application_status: item.application_status as ApplicationStatus,
    region_text: null,
    regions: item.regions,
    age_min: item.min_age,
    age_max: item.max_age,
    age_condition_text: null,
    eligibility_text: null,
    support_content: null,
    application_method: null,
    education_statuses: [],
    employment_statuses: [],
    required_conditions: [],
    preferred_conditions: [],
    excluded_conditions: [],
    source_url: '',
    collected_at: new Date(0).toISOString(),
    data_quality_status: item.data_quality_status as PolicyDto['data_quality_status'],
    id: item.id,
    created_at: new Date(0).toISOString(),
    updated_at: new Date(0).toISOString(),
  };
}

function formatRecommendationDDay(item: RecommendationItemDto): string {
  return getPolicyDeadlineInfo(toPolicyDto(item)).label;
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
  const policy = toPolicyDto(item);
  const showPartial = item.data_quality_status === 'partial';
  const showUnknown = hasRecommendationUnknownConditions(item);
  const reasonSummary = formatRecommendationReasonSummary(item);
  const dDay = formatRecommendationDDay(item);
  const category = item.category as PolicyCategory;

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

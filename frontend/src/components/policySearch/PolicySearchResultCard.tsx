import { Link } from 'react-router';
import PartialBadge from '@/components/policy/PartialBadge';
import UnconfirmedConditionsBadge, {
  UnknownVerdictBadge,
} from '@/components/policySearch/PolicySearchBadges';
import type { PolicySearchHit } from '@/types/policySearch';
import {
  hasUnknownVerdicts,
  hasUnconfirmedConditions,
} from '@/constants/policySearchDisplay';
import { buildPolicySearchHitDetailPath } from '@/utils/policyDetailNavigation';
import {
  formatAge,
  formatApplicationStatus,
  formatOrganization,
  formatRegion,
  getDDayLabel,
} from '@/utils/policyDisplay';
import './PolicySearchBadges.css';

type CardTagVariant = '' | 'hot';

/** Status-only visual tag (모집중·마감 임박). Quality/verdict badges are separate. */
function getStatusCardTag(
  hit: PolicySearchHit,
): { label: string; variant: CardTagVariant } {
  const { policy } = hit;
  const dDay = getDDayLabel(policy);

  if (dDay.startsWith('D-')) {
    const days = Number(dDay.replace('D-', ''));
    if (!Number.isNaN(days) && days <= 7) {
      return { label: '마감 임박', variant: 'hot' };
    }
  }

  if (policy.application_status === 'open') {
    return { label: '모집중', variant: '' };
  }

  if (policy.application_status) {
    return {
      label: formatApplicationStatus(policy.application_status),
      variant: '',
    };
  }

  return { label: '정책', variant: '' };
}

function formatCardMeta(hit: PolicySearchHit): string {
  return [
    formatRegion(hit.policy),
    formatOrganization(hit.policy),
    getDDayLabel(hit.policy),
  ]
    .filter(Boolean)
    .join(' · ');
}

function formatCardEligibility(hit: PolicySearchHit): string {
  if (hasUnconfirmedConditions(hit) || hasUnknownVerdicts(hit)) {
    return '일부 조건 정보 없음 · 원문 확인 필요';
  }

  return `${formatAge(hit.policy)} · ${formatRegion(hit.policy)}`;
}

interface PolicySearchResultCardProps {
  hit: PolicySearchHit;
  searchIncludePartial?: boolean;
  isSelected?: boolean;
  onSelect?: (hit: PolicySearchHit) => void;
}

export default function PolicySearchResultCard({
  hit,
  searchIncludePartial = false,
  isSelected = false,
  onSelect,
}: PolicySearchResultCardProps) {
  const tag = getStatusCardTag(hit);
  const detailPath = buildPolicySearchHitDetailPath(hit, searchIncludePartial);
  const showUnknownVerdict =
    hasUnknownVerdicts(hit) && hit.policy.data_quality_status !== 'partial';
  const showPartialBadge = hit.policy.data_quality_status === 'partial';
  const showUnconfirmed = hasUnconfirmedConditions(hit);
  const isHoverSelectable = Boolean(onSelect);

  return (
    <Link
      to={detailPath}
      className={`policy-card policy-card--selectable${isSelected ? ' policy-card--selected' : ''}`}
      aria-label={`${hit.policy.title} 상세 보기`}
      onMouseEnter={isHoverSelectable ? () => onSelect?.(hit) : undefined}
      onFocus={isHoverSelectable ? () => onSelect?.(hit) : undefined}
    >
      <div className="policy-card__visual">
        <span
          className={`policy-card__tag${tag.variant ? ` policy-card__tag--${tag.variant}` : ''}`}
        >
          {tag.label}
        </span>
      </div>
      <div className="policy-card__body">
        <h3 className="policy-card__title">{hit.policy.title}</h3>

        {showPartialBadge || showUnknownVerdict || showUnconfirmed ? (
          <div className="policy-search-card__badges">
            {showPartialBadge ? <PartialBadge policy={hit.policy} /> : null}
            {showUnknownVerdict ? <UnknownVerdictBadge /> : null}
            {showUnconfirmed ? (
              <UnconfirmedConditionsBadge
                conditions={hit.unconfirmed_conditions}
              />
            ) : null}
          </div>
        ) : null}

        <p className="policy-card__meta">{formatCardMeta(hit)}</p>
        <div className="policy-card__footer">
          <span
            className={
              hasUnknownVerdicts(hit) || hasUnconfirmedConditions(hit)
                ? 'policy-card__eligibility policy-search-card__eligibility--unknown'
                : 'policy-card__eligibility'
            }
          >
            {formatCardEligibility(hit)}
          </span>
          <span className="policy-card__arrow" aria-hidden="true">
            →
          </span>
        </div>
      </div>
    </Link>
  );
}

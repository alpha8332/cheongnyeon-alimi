import type { PolicySearchHit } from '@/types/policySearch';
import {
  formatAge,
  formatApplicationStatus,
  formatOrganization,
  formatRegion,
  getDDayLabel,
} from '@/utils/policyDisplay';

type CardTagVariant = '' | 'warn' | 'hot';

function getCardTag(hit: PolicySearchHit): { label: string; variant: CardTagVariant } {
  const { policy } = hit;

  if (policy.data_quality_status === 'partial' || hit.unknown_count > 0) {
    return { label: '정보 미확인', variant: 'warn' };
  }

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
  if (hit.unknown_count > 0) {
    return '지역·연령 미확인';
  }

  return `${formatAge(hit.policy)} · ${formatRegion(hit.policy)}`;
}

interface PolicySearchResultCardProps {
  hit: PolicySearchHit;
}

export default function PolicySearchResultCard({
  hit,
}: PolicySearchResultCardProps) {
  const tag = getCardTag(hit);

  return (
    <article className="policy-card">
      <div className="policy-card__visual">
        <span
          className={`policy-card__tag${tag.variant ? ` policy-card__tag--${tag.variant}` : ''}`}
        >
          {tag.label}
        </span>
      </div>
      <div className="policy-card__body">
        <h3 className="policy-card__title">{hit.policy.title}</h3>
        <p className="policy-card__meta">{formatCardMeta(hit)}</p>
        <div className="policy-card__footer">
          <span className="policy-card__eligibility">
            {formatCardEligibility(hit)}
          </span>
          <span className="policy-card__arrow" aria-hidden="true">
            →
          </span>
        </div>
      </div>
    </article>
  );
}

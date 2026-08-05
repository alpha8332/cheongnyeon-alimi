import { useId } from 'react';
import type { UnconfirmedCondition } from '@/types/policySearch';
import {
  MATCH_VERDICT_LABELS,
  UNKNOWN_ELIGIBILITY_BADGE_HELP,
  UNKNOWN_ELIGIBILITY_BADGE_LABEL,
} from '@/constants/policySearchDisplay';
import './PolicySearchBadges.css';

interface UnconfirmedConditionsBadgeProps {
  conditions: UnconfirmedCondition[];
}

export default function UnconfirmedConditionsBadge({
  conditions,
}: UnconfirmedConditionsBadgeProps) {
  const tooltipId = useId();

  if (conditions.length === 0) {
    return null;
  }

  return (
    <span className="policy-search-badge-wrap">
      <button
        type="button"
        className="policy-search-badge policy-search-badge--unconfirmed"
        aria-describedby={tooltipId}
        aria-label={`${UNKNOWN_ELIGIBILITY_BADGE_LABEL}. 상세 사유 보기`}
      >
        {UNKNOWN_ELIGIBILITY_BADGE_LABEL}
      </button>
      <span
        id={tooltipId}
        role="tooltip"
        className="policy-search-badge__tooltip"
      >
        <strong className="policy-search-badge__tooltip-title">
          {UNKNOWN_ELIGIBILITY_BADGE_HELP}
        </strong>
        <ul className="policy-search-badge__tooltip-list">
          {conditions.map((condition) => (
            <li key={`${condition.field}-${condition.reason_code}`}>
              {condition.message}
            </li>
          ))}
        </ul>
      </span>
    </span>
  );
}

export function UnknownVerdictBadge() {
  return (
    <span
      className="policy-search-badge policy-search-badge--unknown"
      title="출처 데이터에 해당 조건 정보가 없습니다. 전국 적용 또는 제한 없음으로 해석하지 마세요."
    >
      {MATCH_VERDICT_LABELS.unknown}
    </span>
  );
}

/**
 * Policy Search display labels (Frontend 04 FE4-18).
 *
 * Promoted from `frontend/src/types/draft/policySearchDisplay.ts`.
 */

import type { MatchVerdict, PolicySearchHit, UnconfirmedCondition } from '@/types/policySearch';

export type PolicySearchBadgeVariant =
  | 'match'
  | 'mismatch'
  | 'unknown'
  | 'partial'
  | 'status-open'
  | 'status-closed'
  | 'status-scheduled'
  | 'status-unknown';

export const MATCH_VERDICT_LABELS: Record<MatchVerdict, string> = {
  match: '조건 일치',
  mismatch: '조건 불일치',
  unknown: '정보 미확인',
};

/** unknown is NOT "전국" or "제한 없음". */
export const MATCH_VERDICT_HELP: Record<MatchVerdict, string> = {
  match: '이 정책에 대해 해당 조건이 확인되었습니다.',
  mismatch: '요청 조건과 확인된 정보가 다릅니다. 결과에서 제외되었을 수 있습니다.',
  unknown:
    '출처 데이터에 해당 조건 정보가 없습니다. 지원 가능 여부를 확정할 수 없습니다.',
};

export const PARTIAL_QUALITY_BADGE_LABEL = '정보 일부 누락';

export const PARTIAL_QUALITY_BADGE_HELP =
  '일부 검색 조건(지역·연령·신청 상태 등)이 데이터에 없습니다. 원문을 확인하세요.';

export const UNKNOWN_ELIGIBILITY_BADGE_LABEL = '자격요건 직접 확인 필요';

export const UNKNOWN_ELIGIBILITY_BADGE_HELP =
  '정책 원문에서 아래 항목을 직접 확인해 주세요. 전국 적용 또는 제한 없음으로 해석하지 마세요.';

export function hasUnknownVerdicts(hit: Pick<PolicySearchHit, 'unknown_count'>): boolean {
  return hit.unknown_count > 0;
}

export function hasUnconfirmedConditions(
  hit: Pick<PolicySearchHit, 'unconfirmed_conditions'>,
): boolean {
  return hit.unconfirmed_conditions.length > 0;
}

export function formatUnconfirmedConditionsTooltip(
  conditions: readonly UnconfirmedCondition[],
): string {
  return conditions.map((item) => item.message).join('\n');
}

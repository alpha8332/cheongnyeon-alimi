/**
 * W3-F0 DRAFT — UI display semantics for search consumption (G1 pending).
 * Maps Backend verdicts and quality states to user-visible copy.
 * Frontend must not infer unknown as match or national coverage.
 */

import type { PolicyMatchVerdict } from '@/types/draft/policySearch.contract';
import type { PublicDataQualityStatus } from '@/types/policy';

/** Badge variant keys for design system / Tailwind mapping post-G1. */
export type PolicySearchBadgeVariant =
  | 'match'
  | 'mismatch'
  | 'unknown'
  | 'partial'
  | 'status-open'
  | 'status-closed'
  | 'status-scheduled'
  | 'status-unknown';

export const POLICY_MATCH_VERDICT_LABELS: Record<PolicyMatchVerdict, string> = {
  match: '조건 일치',
  mismatch: '조건 불일치',
  unknown: '정보 미확인',
};

/**
 * Tooltip/helper copy — unknown is NOT "전국" or "제한 없음".
 */
export const POLICY_MATCH_VERDICT_HELP: Record<PolicyMatchVerdict, string> = {
  match: '이 정책에 대해 해당 조건이 확인되었습니다.',
  mismatch: '요청 조건과 확인된 정보가 다릅니다. 결과에서 제외되었을 수 있습니다.',
  unknown:
    '출처 데이터에 해당 조건 정보가 없습니다. 지원 가능 여부를 확정할 수 없습니다.',
};

export const PARTIAL_QUALITY_BADGE_LABEL = '정보 일부 누락';

export const PARTIAL_QUALITY_BADGE_HELP =
  '일부 검색 조건(지역·연령·신청 상태 등)이 데이터에 없습니다. 원문을 확인하세요.';

export function qualityStatusToBadge(
  status: PublicDataQualityStatus,
): PolicySearchBadgeVariant | null {
  return status === 'partial' ? 'partial' : null;
}

export function verdictToBadge(verdict: PolicyMatchVerdict): PolicySearchBadgeVariant {
  return verdict;
}

/** G1-pending: global unconfirmed banner when query has unknown dimensions. */
export function formatUnconfirmedBanner(unconfirmedDimensions: string[]): string | null {
  if (unconfirmedDimensions.length === 0) {
    return null;
  }

  return `다음 조건은 아직 확인되지 않았습니다: ${unconfirmedDimensions.join(', ')}. 미확인 정책도 결과에 포함될 수 있습니다.`;
}

/**
 * W3-F0 DRAFT — Display token labels only (Gate G1 pending).
 *
 * Mapping functions (banner format, badge variant lookup) belong to post-G1 UI Slices.
 * See docs/product/features/search_and_discovery.md.
 */

import type { MatchVerdict } from '@/types/policySearch';

/** Post-G1 design-system badge variant keys. */
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

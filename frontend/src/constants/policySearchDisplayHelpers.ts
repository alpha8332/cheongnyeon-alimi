import type { MatchVerdict, UnconfirmedCondition } from '../types/policySearch.js';

export const MATCH_VERDICT_LABELS: Record<MatchVerdict, string> = {
  match: '조건 일치',
  mismatch: '조건 불일치',
  unknown: '정보 미확인',
};

export const PARTIAL_QUALITY_BADGE_LABEL = '정보 일부 누락';

export const UNKNOWN_ELIGIBILITY_BADGE_LABEL = '자격요건 직접 확인 필요';

export function hasUnknownVerdicts(hit: { unknown_count: number }): boolean {
  return hit.unknown_count > 0;
}

export function hasUnconfirmedConditions(hit: {
  unconfirmed_conditions: readonly UnconfirmedCondition[];
}): boolean {
  return hit.unconfirmed_conditions.length > 0;
}

export function formatUnconfirmedConditionsTooltip(
  conditions: readonly UnconfirmedCondition[],
): string {
  return conditions.map((item) => item.message).join('\n');
}

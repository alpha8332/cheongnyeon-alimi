import type {
  RecommendationItemDto,
  RecommendationResponse,
} from '../types/recommendation.js';

export function formatRecommendationReasonSummary(
  item: RecommendationItemDto,
): string {
  const labels = item.reasons
    .map((reason) => reason.label.trim())
    .filter(Boolean);

  if (labels.length > 0) {
    return labels.join(' · ');
  }

  return '입력 조건과 관련된 정책 후보입니다.';
}

export function formatRecommendationAge(item: RecommendationItemDto): string {
  if (item.min_age === 0 && item.max_age === 0) {
    return '연령 정보 없음';
  }
  if (item.min_age !== null || item.max_age !== null) {
    return `${item.min_age ?? '—'}~${item.max_age ?? '—'}세`;
  }
  if (item.reasons.some((reason) => reason.code === 'AGE_UNRESTRICTED')) {
    return '연령 제한 없음';
  }
  return '연령 정보 없음';
}

export function hasRecommendationUnknownConditions(
  item: RecommendationItemDto,
): boolean {
  return item.unknown_conditions.length > 0;
}

export function hasQueryLevelRecommendationWarnings(
  response: RecommendationResponse | null | undefined,
): boolean {
  if (!response) {
    return false;
  }

  return response.items.some(hasRecommendationUnknownConditions);
}

export function countRecommendationUnknownItems(
  response: RecommendationResponse,
): number {
  return response.items.filter(hasRecommendationUnknownConditions).length;
}

export function buildRecommendationQueryWarningMessage(
  response: RecommendationResponse,
): string {
  const unknownCount = countRecommendationUnknownItems(response);

  if (unknownCount === 0) {
    return '';
  }

  return (
    `${unknownCount}건의 추천 결과에 확인되지 않은 조건 정보가 있습니다. ` +
    '자격을 단정하지 않으며 공식 원문 확인이 필요합니다.'
  );
}

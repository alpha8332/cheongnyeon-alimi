import type { EligibilityConditionCategory } from '../types/eligibilitySummary.js';
import type { EligibilitySummaryStatus } from '../types/eligibilitySummary.js';
import { formatCollectedAt } from './policyDisplay.js';

const CATEGORY_LABELS: Record<EligibilityConditionCategory, string> = {
  age: '연령',
  region: '지역',
  income: '소득',
  asset: '재산',
  employment: '취업',
  education: '학력',
  housing: '주거',
  household: '가구',
  other: '기타',
};

export const ELIGIBILITY_SUMMARY_STATUS_LABELS: Record<
  EligibilitySummaryStatus,
  string
> = {
  complete: '구조화 완료',
  partial: '일부 확인 필요',
  unknown: '구조화 불가',
};

export function getEligibilityCategoryLabel(
  category: EligibilityConditionCategory | string,
): string {
  if (category in CATEGORY_LABELS) {
    return CATEGORY_LABELS[category as EligibilityConditionCategory];
  }

  return category.length > 0 ? category : '기타';
}

export function formatEligibilityEvidenceCollectedAt(
  collectedAt: string,
): string {
  return formatCollectedAt(collectedAt);
}

export function shouldExpandEligibilityText(
  text: string,
  maxLength = 120,
): boolean {
  return text.length > maxLength;
}

export function truncateEligibilityText(text: string, maxLength = 120): string {
  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength)}…`;
}

import type {
  ApplicationSchedule,
  ApplicationStatus,
  PolicyDto,
  PolicyCategory,
} from '../types/policy.js';
import { getDDayLabel, normalizePolicyYmd } from './policyDeadline.js';

export { getDDayLabel, normalizePolicyYmd };

const CATEGORY_LABELS: Record<PolicyCategory, string> = {
  housing: '주거',
  finance: '금융',
  welfare: '복지',
  employment: '취업',
  startup: '창업',
  education: '교육',
  other: '기타',
};

const SCHEDULE_LABELS: Record<ApplicationSchedule, string> = {
  fixed_period: '기간 한정',
  always: '상시',
  until_budget_exhausted: '예산 소진 시까지',
};

const STATUS_LABELS: Record<ApplicationStatus, string> = {
  open: '접수 중',
  closed: '마감',
  scheduled: '예정',
};

export const POLICY_ELIGIBILITY_NOTICE =
  '검색 결과는 신청 가능한 정책 후보를 안내하며, 실제 자격 충족을 확정하지 않습니다. 신청 전 원문과 세부 요건을 확인해 주세요.';

export function getCategoryLabel(category: PolicyCategory): string {
  return CATEGORY_LABELS[category];
}

export function getPolicyCategoryDisplayOrder(
  policy: Pick<PolicyDto, 'categories'>,
  highlightedCategory?: PolicyCategory | null,
): PolicyCategory[] {
  const categories = Array.from(new Set(policy.categories));
  if (categories.length === 0) {
    return ['other'];
  }

  if (!highlightedCategory || !categories.includes(highlightedCategory)) {
    return categories;
  }

  return [
    highlightedCategory,
    ...categories.filter((category) => category !== highlightedCategory),
  ];
}

export function formatCategoryTags(
  policy: Pick<PolicyDto, 'categories' | 'category_text'>,
): string[] {
  if (policy.categories.length > 0) {
    return policy.categories.map(getCategoryLabel);
  }

  if (policy.category_text) {
    return [policy.category_text];
  }

  return ['분류 없음'];
}

export function formatOrganization(
  policy: Pick<PolicyDto, 'organization'>,
): string {
  return policy.organization ?? '기관 정보 없음';
}

export function formatRegion(
  policy: Pick<PolicyDto, 'regions' | 'region_text'>,
): string {
  if (policy.regions.length > 0) {
    return policy.regions.join(', ');
  }

  return policy.region_text ?? '지역 미정';
}

export function formatAge(policy: PolicyDto): string {
  const compactAgeText = policy.age_condition_text?.replace(/\s+/g, '');
  if (
    (policy.age_min === 0 && policy.age_max === 0) ||
    compactAgeText === '0세~0세' ||
    compactAgeText === '0~0'
  ) {
    return '연령 정보 없음';
  }

  if (policy.age_min !== null && policy.age_max !== null) {
    return `${policy.age_min}세 ~ ${policy.age_max}세`;
  }

  if (policy.age_min !== null) {
    return `${policy.age_min}세 이상`;
  }

  if (policy.age_max !== null) {
    return `${policy.age_max}세 이하`;
  }

  return policy.age_condition_text ?? '연령 정보 없음';
}

export function formatApplicationSchedule(
  schedule: ApplicationSchedule | null,
): string {
  if (!schedule) {
    return '일정 미확인';
  }

  return SCHEDULE_LABELS[schedule];
}

export function formatApplicationStatus(
  status: ApplicationStatus | null,
): string {
  if (!status) {
    return '상태 미확인';
  }

  return STATUS_LABELS[status];
}

/** YYYY-MM-DD / ISO datetime → `YYYY.MM.DD` */
export function formatPolicyDateDot(value: string | null | undefined): string | null {
  const normalized = normalizePolicyYmd(value);
  if (!normalized) {
    return null;
  }

  const [year, month, day] = normalized.split('-');
  return `${year}.${month}.${day}`;
}

function normalizePeriodTextDates(text: string): string {
  return text
    .replace(/\b(\d{4})(\d{2})(\d{2})\b/g, '$1.$2.$3')
    .replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g, '$1.$2.$3')
    .replace(
      /\b(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?\b/g,
      (_, year: string, month: string, day: string) =>
        `${year}.${month.padStart(2, '0')}.${day.padStart(2, '0')}`,
    )
    .replace(/\s{2,}/g, ' ')
    .trim();
}

/** 상세·modal용 신청 기간 (`YYYY.MM.DD`) */
export function formatApplicationPeriodDisplay(policy: PolicyDto): string {
  if (policy.application_period_text) {
    return normalizePeriodTextDates(policy.application_period_text);
  }

  const start = formatPolicyDateDot(policy.application_start);
  const end = formatPolicyDateDot(policy.application_end);

  if (start && end) {
    return `${start} ~ ${end}`;
  }

  if (start) {
    return `${start} ~`;
  }

  if (end) {
    return `~ ${end}`;
  }

  if (policy.application_schedule === 'always') {
    return '상시';
  }

  return '신청 기간 미정';
}

/** 목록 카드용 compact 신청 기간 */
export function formatApplicationPeriodCard(policy: PolicyDto): string {
  const start = formatPolicyDateDot(policy.application_start);
  const end = formatPolicyDateDot(policy.application_end);

  if (start && end) {
    return `${start} ~ ${end}`;
  }

  if (end) {
    return `${end} 마감`;
  }

  if (start) {
    return `${start} 시작`;
  }

  if (policy.application_schedule === 'always') {
    return '상시';
  }

  if (policy.application_period_text) {
    const normalized = normalizePeriodTextDates(policy.application_period_text);
    return normalized.length > 48 ? `${normalized.slice(0, 48)}…` : normalized;
  }

  return '기간 미정';
}

export function formatApplicationPeriod(policy: PolicyDto): string {
  return formatApplicationPeriodDisplay(policy);
}

export function formatCollectedAt(value: string): string {
  const collectedAt = new Date(value);
  if (Number.isNaN(collectedAt.getTime())) {
    return '수집 시각 미확인';
  }

  const kst = new Date(collectedAt.getTime() + 9 * 60 * 60 * 1000);
  const [date, time] = kst.toISOString().slice(0, 16).split('T');
  return `${date} ${time} KST`;
}

export function formatNullableText(
  value: string | null,
  fallback: string,
): string {
  return value ?? fallback;
}

function stripHtmlTags(value: string): string {
  return value.replace(/<[^>]*>/g, '').trim();
}

/** Calendar·카드 등 UI 표시용 정책명 (API 필드명·HTML 변형 폴백). */
export function getPolicyDisplayTitle(
  policy: Pick<PolicyDto, 'title' | 'category_text'>,
): string {
  const legacy = policy as Pick<PolicyDto, 'title' | 'category_text'> &
    Record<string, unknown>;
  const candidates = [
    policy.title,
    legacy['policy_name'],
    legacy['name'],
    legacy['polyBizSjnm'],
    legacy['plcyNm'],
    policy.category_text,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === 'string') {
      const normalized = stripHtmlTags(candidate);
      if (normalized) {
        return normalized;
      }
    }
  }

  return '정책';
}

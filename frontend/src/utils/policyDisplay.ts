import type {
  ApplicationSchedule,
  ApplicationStatus,
  PolicyDto,
  PolicyCategory,
} from '../types/policy.js';

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

export function getCategoryLabel(category: PolicyCategory): string {
  return CATEGORY_LABELS[category];
}

export function formatCategoryTags(policy: PolicyDto): string[] {
  if (policy.categories.length > 0) {
    return policy.categories.map(getCategoryLabel);
  }

  if (policy.category_text) {
    return [policy.category_text];
  }

  return ['분류 없음'];
}

export function formatOrganization(policy: PolicyDto): string {
  return policy.organization ?? '기관 정보 없음';
}

export function formatRegion(policy: PolicyDto): string {
  if (policy.regions.length > 0) {
    return policy.regions.join(', ');
  }

  return policy.region_text ?? '지역 미정';
}

export function formatAge(policy: PolicyDto): string {
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

export function formatApplicationPeriod(policy: PolicyDto): string {
  if (policy.application_period_text) {
    return policy.application_period_text;
  }

  if (policy.application_start && policy.application_end) {
    return `${policy.application_start} ~ ${policy.application_end}`;
  }

  if (policy.application_start) {
    return `${policy.application_start} ~`;
  }

  if (policy.application_end) {
    return `~ ${policy.application_end}`;
  }

  return '신청 기간 미정';
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

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function parseDateOnly(value: string): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
}

export function getDDayLabel(
  policy: PolicyDto,
  referenceDate: Date = new Date(),
): string {
  if (policy.application_status === 'closed') {
    return '마감';
  }

  if (policy.application_schedule === 'always' && policy.application_status === 'open') {
    return '상시';
  }

  if (!policy.application_end) {
    return '일정 미정';
  }

  const today = startOfDay(referenceDate);
  const endDate = startOfDay(parseDateOnly(policy.application_end));
  const diffDays = Math.ceil(
    (endDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24),
  );

  if (diffDays > 0) {
    return `D-${diffDays}`;
  }

  if (diffDays === 0) {
    return 'D-Day';
  }

  return '마감';
}

export function formatNullableText(
  value: string | null,
  fallback: string,
): string {
  return value ?? fallback;
}

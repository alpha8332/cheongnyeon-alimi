import type {
  ApplicationSchedule,
  ApplicationStatus,
  NormalizedProgram,
  PolicyCategory,
} from '@/types/policy';

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

export function formatCategoryTags(program: NormalizedProgram): string[] {
  if (program.categories.length > 0) {
    return program.categories.map(getCategoryLabel);
  }

  if (program.category_text) {
    return [program.category_text];
  }

  return ['분류 없음'];
}

export function formatOrganization(program: NormalizedProgram): string {
  return program.organization ?? '기관 정보 없음';
}

export function formatRegion(program: NormalizedProgram): string {
  if (program.regions.length > 0) {
    return program.regions.join(', ');
  }

  return program.region_text ?? '지역 미정';
}

export function formatAge(program: NormalizedProgram): string {
  if (program.age_min !== null && program.age_max !== null) {
    return `${program.age_min}세 ~ ${program.age_max}세`;
  }

  if (program.age_min !== null) {
    return `${program.age_min}세 이상`;
  }

  if (program.age_max !== null) {
    return `${program.age_max}세 이하`;
  }

  return program.age_condition_text ?? '연령 정보 없음';
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

export function formatApplicationPeriod(program: NormalizedProgram): string {
  if (program.application_period_text) {
    return program.application_period_text;
  }

  if (program.application_start && program.application_end) {
    return `${program.application_start} ~ ${program.application_end}`;
  }

  if (program.application_start) {
    return `${program.application_start} ~`;
  }

  if (program.application_end) {
    return `~ ${program.application_end}`;
  }

  return '신청 기간 미정';
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function parseDateOnly(value: string): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
}

export function getDDayLabel(
  program: NormalizedProgram,
  referenceDate: Date = new Date(),
): string {
  if (program.application_status === 'closed') {
    return '마감';
  }

  if (program.application_schedule === 'always' && program.application_status === 'open') {
    return '상시';
  }

  if (!program.application_end) {
    return '일정 미정';
  }

  const today = startOfDay(referenceDate);
  const endDate = startOfDay(parseDateOnly(program.application_end));
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

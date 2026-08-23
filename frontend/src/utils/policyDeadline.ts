import type { PolicyDto } from '../types/policy.js';

export const KST_TIME_ZONE = 'Asia/Seoul';

/** Normalize API date strings to YYYY-MM-DD (KST calendar date). */
export function normalizePolicyYmd(
  value: string | null | undefined,
): string | null {
  if (typeof value !== 'string') {
    return null;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return trimmed;
  }

  const datePrefix = trimmed.match(/^(\d{4}-\d{2}-\d{2})/);
  return datePrefix?.[1] ?? null;
}

export type PolicyDeadlineKind =
  | 'closed'
  | 'always'
  | 'unknown'
  | 'upcoming'
  | 'today'
  | 'past';

export interface PolicyDeadlineInfo {
  kind: PolicyDeadlineKind;
  label: string;
  daysRemaining: number | null;
  /** True when `application_end` is present and a calendar slot may be shown. */
  hasCalendarSlot: boolean;
  applicationEnd: string | null;
}

/** YYYY-MM-DD in Asia/Seoul for the given instant. */
export function getKstDateString(referenceDate: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: KST_TIME_ZONE }).format(
    referenceDate,
  );
}

export function diffDaysBetweenYmd(fromYmd: string, toYmd: string): number {
  const parseYmd = (ymd: string): number => {
    const [year, month, day] = ymd.split('-').map(Number);
    return Date.UTC(year, month - 1, day);
  };

  return Math.round((parseYmd(toYmd) - parseYmd(fromYmd)) / 86_400_000);
}

export function getPolicyDeadlineInfo(
  policy: PolicyDto,
  referenceDate: Date = new Date(),
): PolicyDeadlineInfo {
  const applicationEnd = normalizePolicyYmd(policy.application_end);

  if (policy.application_status === 'closed') {
    return {
      kind: 'closed',
      label: '마감',
      daysRemaining: null,
      hasCalendarSlot: false,
      applicationEnd,
    };
  }

  if (
    policy.application_schedule === 'always' &&
    policy.application_status === 'open' &&
    !applicationEnd
  ) {
    return {
      kind: 'always',
      label: '상시',
      daysRemaining: null,
      hasCalendarSlot: false,
      applicationEnd: null,
    };
  }

  if (!applicationEnd) {
    return {
      kind: 'unknown',
      label: '일정 미정',
      daysRemaining: null,
      hasCalendarSlot: false,
      applicationEnd: null,
    };
  }

  const todayKst = getKstDateString(referenceDate);
  const daysRemaining = diffDaysBetweenYmd(todayKst, applicationEnd);

  if (daysRemaining > 0) {
    return {
      kind: 'upcoming',
      label: `D-${daysRemaining}`,
      daysRemaining,
      hasCalendarSlot: true,
      applicationEnd,
    };
  }

  if (daysRemaining === 0) {
    return {
      kind: 'today',
      label: 'D-Day',
      daysRemaining: 0,
      hasCalendarSlot: true,
      applicationEnd,
    };
  }

  return {
    kind: 'past',
    label: '마감',
    daysRemaining,
    hasCalendarSlot: true,
    applicationEnd,
  };
}

export function getPolicyCardDDayBadgeLabel(
  policy: PolicyDto,
  referenceDate: Date = new Date(),
): string | null {
  const info = getPolicyDeadlineInfo(policy, referenceDate);

  if (info.kind === 'upcoming' || info.kind === 'today') {
    return info.label;
  }

  return null;
}

export function getDDayLabel(
  policy: PolicyDto,
  referenceDate: Date = new Date(),
): string {
  return getPolicyDeadlineInfo(policy, referenceDate).label;
}

export function isImminentDeadline(
  policy: PolicyDto,
  withinDays = 7,
  referenceDate: Date = new Date(),
): boolean {
  const info = getPolicyDeadlineInfo(policy, referenceDate);

  if (!info.hasCalendarSlot || info.daysRemaining === null) {
    return false;
  }

  return info.daysRemaining >= 0 && info.daysRemaining <= withinDays;
}

/** 홈 첫 화면 featured 카드 — 마감·예정·지난 마감일 제외, open·상시 위주 */
export function isHomeFeaturedPolicy(
  policy: PolicyDto,
  referenceDate: Date = new Date(),
): boolean {
  if (
    policy.application_status === 'closed' ||
    policy.application_status === 'scheduled'
  ) {
    return false;
  }

  const deadline = getPolicyDeadlineInfo(policy, referenceDate);
  if (deadline.kind === 'closed' || deadline.kind === 'past') {
    return false;
  }

  if (
    policy.application_schedule === 'always' &&
    policy.application_status === 'open'
  ) {
    return true;
  }

  return policy.application_status === 'open';
}

export function groupPoliciesByApplicationEnd(
  policies: readonly PolicyDto[],
): Map<string, PolicyDto[]> {
  const grouped = new Map<string, PolicyDto[]>();

  for (const policy of policies) {
    const info = getPolicyDeadlineInfo(policy);
    if (!info.hasCalendarSlot || !info.applicationEnd) {
      continue;
    }

    const bucket = grouped.get(info.applicationEnd) ?? [];
    bucket.push(policy);
    grouped.set(info.applicationEnd, bucket);
  }

  for (const [date, items] of grouped) {
    grouped.set(
      date,
      [...items].sort((left, right) => left.title.localeCompare(right.title, 'ko')),
    );
  }

  return grouped;
}

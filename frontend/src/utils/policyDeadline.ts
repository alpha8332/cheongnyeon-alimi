import type { PolicyDto } from '../types/policy.js';

export const KST_TIME_ZONE = 'Asia/Seoul';

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
  const applicationEnd = policy.application_end;

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

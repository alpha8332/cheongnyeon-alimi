import type { PolicyDto } from '../types/policy.js';
import { getPolicyDeadlineInfo, normalizePolicyYmd } from './policyDeadline.js';

export type CalendarEventKind = 'start' | 'end';

export interface CalendarPolicyEvent {
  policy: PolicyDto;
  date: string;
  kind: CalendarEventKind;
}

export const CALENDAR_MAX_VISIBLE_BADGES_PER_DAY = 2;

function canShowCalendarStartEvent(
  policy: PolicyDto,
  normalizedStart: string | null,
): boolean {
  if (!normalizedStart) {
    return false;
  }

  if (policy.application_status === 'closed') {
    return false;
  }

  if (
    policy.application_schedule === 'always' &&
    policy.application_status === 'open' &&
    !normalizePolicyYmd(policy.application_end)
  ) {
    return false;
  }

  return true;
}

export function collectCalendarPolicyEvents(
  policies: readonly PolicyDto[],
): CalendarPolicyEvent[] {
  const events: CalendarPolicyEvent[] = [];
  const seen = new Set<string>();

  for (const policy of policies) {
    const deadline = getPolicyDeadlineInfo(policy);
    const normalizedEnd = normalizePolicyYmd(deadline.applicationEnd);

    if (deadline.hasCalendarSlot && normalizedEnd) {
      const key = `${policy.id}:end:${normalizedEnd}`;
      if (!seen.has(key)) {
        seen.add(key);
        events.push({
          policy,
          date: normalizedEnd,
          kind: 'end',
        });
      }
    }

    const normalizedStart = normalizePolicyYmd(policy.application_start);
    if (canShowCalendarStartEvent(policy, normalizedStart) && normalizedStart) {
      const key = `${policy.id}:start:${normalizedStart}`;
      if (!seen.has(key)) {
        seen.add(key);
        events.push({
          policy,
          date: normalizedStart,
          kind: 'start',
        });
      }
    }
  }

  return events.sort((left, right) => {
    const dateCompare = left.date.localeCompare(right.date);
    if (dateCompare !== 0) {
      return dateCompare;
    }

    if (left.kind !== right.kind) {
      return left.kind === 'start' ? -1 : 1;
    }

    return left.policy.title.localeCompare(right.policy.title, 'ko');
  });
}

export function groupCalendarEventsByDate(
  events: readonly CalendarPolicyEvent[],
): Map<string, CalendarPolicyEvent[]> {
  const grouped = new Map<string, CalendarPolicyEvent[]>();

  for (const event of events) {
    const bucket = grouped.get(event.date) ?? [];
    bucket.push(event);
    grouped.set(event.date, bucket);
  }

  return grouped;
}

export function getCalendarEventKindLabel(kind: CalendarEventKind): string {
  return kind === 'start' ? '신청 시작' : '신청 마감';
}

import type { PolicyDto } from '../types/policy.js';
import { getPolicyDeadlineInfo } from './policyDeadline.js';

export type CalendarEventKind = 'start' | 'end';

export interface CalendarPolicyEvent {
  policy: PolicyDto;
  date: string;
  kind: CalendarEventKind;
}

export const CALENDAR_MAX_VISIBLE_BADGES_PER_DAY = 2;

function isValidYmd(value: string | null | undefined): value is string {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function canShowCalendarStartEvent(policy: PolicyDto): boolean {
  if (!isValidYmd(policy.application_start)) {
    return false;
  }

  if (policy.application_status === 'closed') {
    return false;
  }

  if (
    policy.application_schedule === 'always' &&
    policy.application_status === 'open' &&
    !policy.application_end
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
    if (deadline.hasCalendarSlot && isValidYmd(deadline.applicationEnd)) {
      const key = `${policy.id}:end:${deadline.applicationEnd}`;
      if (!seen.has(key)) {
        seen.add(key);
        events.push({
          policy,
          date: deadline.applicationEnd,
          kind: 'end',
        });
      }
    }

    if (canShowCalendarStartEvent(policy)) {
      const startDate = policy.application_start!;
      const key = `${policy.id}:start:${startDate}`;
      if (!seen.has(key)) {
        seen.add(key);
        events.push({
          policy,
          date: startDate,
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

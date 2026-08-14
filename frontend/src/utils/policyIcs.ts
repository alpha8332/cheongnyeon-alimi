import type { PolicyDto } from '../types/policy.js';
import { getPolicyDeadlineInfo } from './policyDeadline.js';

const ICS_LINE_END = '\r\n';

/** RFC5545 TEXT escaping for SUMMARY·DESCRIPTION fields. */
export function escapeIcsText(value: string): string {
  return value
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\r\n|\n|\r/g, '\\n');
}

function formatIcsDate(ymd: string): string {
  return ymd.replace(/-/g, '');
}

function addDaysToYmd(ymd: string, days: number): string {
  const [year, month, day] = ymd.split('-').map(Number);
  const next = new Date(Date.UTC(year, month - 1, day + days));
  const y = next.getUTCFullYear();
  const m = String(next.getUTCMonth() + 1).padStart(2, '0');
  const d = String(next.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function canDownloadPolicyIcs(policy: PolicyDto): boolean {
  return getPolicyDeadlineInfo(policy).hasCalendarSlot;
}

export function buildPolicyDeadlineIcs(policy: PolicyDto): string | null {
  const deadline = getPolicyDeadlineInfo(policy);
  if (!deadline.applicationEnd) {
    return null;
  }

  const dtStart = formatIcsDate(deadline.applicationEnd);
  const dtEnd = formatIcsDate(addDaysToYmd(deadline.applicationEnd, 1));
  const uid = `policy-${policy.id}-${deadline.applicationEnd}@cheongnyeon-alimi.local`;
  const summary = escapeIcsText(`${policy.title} 신청 마감`);
  const description = escapeIcsText(
    `정책 신청 마감일 알림입니다. 자격 충족을 확정하지 않으며 공식 원문을 확인하세요.\n${policy.source_url}`,
  );
  const now = new Date()
    .toISOString()
    .replace(/[-:]/g, '')
    .replace(/\.\d{3}Z$/, 'Z');

  return [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//cheongnyeon-alimi//Policy Deadline//KO',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${now}`,
    `DTSTART;VALUE=DATE:${dtStart}`,
    `DTEND;VALUE=DATE:${dtEnd}`,
    `SUMMARY:${summary}`,
    `DESCRIPTION:${description}`,
    'END:VEVENT',
    'END:VCALENDAR',
  ].join(ICS_LINE_END);
}

export function downloadPolicyIcs(
  policy: PolicyDto,
  filename?: string,
): boolean {
  const content = buildPolicyDeadlineIcs(policy);
  if (content === null) {
    return false;
  }

  if (typeof document === 'undefined') {
    return false;
  }

  const blob = new Blob([content], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename ?? `policy-${policy.id}-deadline.ics`;
  anchor.rel = 'noopener';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  return true;
}

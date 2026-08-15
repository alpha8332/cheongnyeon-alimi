import assert from 'node:assert/strict';
import test from 'node:test';
import {
  addCalendarMonths,
  addDaysToYmd,
  buildMonthlyCalendarGrid,
  formatCalendarMonthLabel,
} from '../src/utils/calendarMonthGrid.js';
import type { PolicyDto } from '../src/types/policy.js';
import {
  CALENDAR_MAX_VISIBLE_BADGES_PER_DAY,
  collectCalendarPolicyEvents,
  getCalendarEventKindLabel,
  groupCalendarEventsByDate,
} from '../src/utils/calendarPolicyEvents.js';

function createPolicy(overrides: Partial<PolicyDto> = {}): PolicyDto {
  return {
    schema_version: '1.1.0',
    source_id: 'test',
    source_name: 'Test Source',
    external_id: null,
    title: 'Test Policy',
    organization: null,
    summary: null,
    category_text: null,
    categories: ['other'],
    application_period_text: null,
    application_start: null,
    application_end: '2026-08-20',
    application_schedule: 'fixed_period',
    application_status: 'open',
    region_text: null,
    regions: ['전국'],
    age_min: null,
    age_max: null,
    age_condition_text: null,
    eligibility_text: null,
    support_content: null,
    application_method: null,
    education_statuses: [],
    employment_statuses: [],
    required_conditions: [],
    preferred_conditions: [],
    excluded_conditions: [],
    source_url: 'https://example.gov/policy',
    collected_at: '2026-08-11T00:00:00.000Z',
    data_quality_status: 'valid',
    id: 1,
    created_at: '2026-08-11T00:00:00.000Z',
    updated_at: '2026-08-11T00:00:00.000Z',
    ...overrides,
  };
}

test('buildMonthlyCalendarGrid는 42칸 Sunday-start grid를 생성한다', () => {
  const cells = buildMonthlyCalendarGrid(2026, 8, '2026-08-11');
  assert.equal(cells.length, 42);
  assert.equal(cells[0]?.date, '2026-07-26');
  assert.equal(cells.find((cell) => cell.date === '2026-08-01')?.inCurrentMonth, true);
  assert.equal(cells.find((cell) => cell.date === '2026-07-31')?.inCurrentMonth, false);
  assert.equal(cells.find((cell) => cell.isToday)?.date, '2026-08-11');
});

test('addCalendarMonths와 formatCalendarMonthLabel', () => {
  assert.deepEqual(addCalendarMonths(2026, 1, 1), { year: 2026, month: 2 });
  assert.deepEqual(addCalendarMonths(2026, 12, 1), { year: 2027, month: 1 });
  assert.equal(formatCalendarMonthLabel(2026, 8), '2026년 08월');
  assert.equal(addDaysToYmd('2026-08-11', 1), '2026-08-12');
});

test('collectCalendarPolicyEvents는 start·end 이벤트를 수집한다', () => {
  const events = collectCalendarPolicyEvents([
    createPolicy({
      id: 1,
      title: '마감 정책',
      application_start: '2026-08-01',
      application_end: '2026-08-20',
    }),
    createPolicy({
      id: 2,
      title: '시작만',
      application_start: '2026-08-05',
      application_end: null,
      application_status: 'scheduled',
    }),
    createPolicy({
      id: 3,
      title: 'closed',
      application_start: '2026-08-03',
      application_end: '2026-08-30',
      application_status: 'closed',
    }),
  ]);

  assert.equal(events.length, 3);
  assert.equal(
    events.some((event) => event.kind === 'end' && event.date === '2026-08-20'),
    true,
  );
  assert.equal(
    events.some((event) => event.kind === 'start' && event.date === '2026-08-05'),
    true,
  );
  assert.equal(events.some((event) => event.policy.id === 3), false);
});

test('groupCalendarEventsByDate는 date bucket을 만든다', () => {
  const events = collectCalendarPolicyEvents([
    createPolicy({ id: 1, application_end: '2026-08-20' }),
    createPolicy({ id: 2, application_end: '2026-08-20', title: 'B' }),
  ]);
  const grouped = groupCalendarEventsByDate(events);
  assert.equal(grouped.get('2026-08-20')?.length, 2);
});

test('calendar badge helper 상수', () => {
  assert.equal(CALENDAR_MAX_VISIBLE_BADGES_PER_DAY, 2);
  assert.equal(getCalendarEventKindLabel('start'), '신청 시작');
  assert.equal(getCalendarEventKindLabel('end'), '신청 마감');
});

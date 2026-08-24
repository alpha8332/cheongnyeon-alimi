import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto } from '../src/types/policy.js';
import {
  CALENDAR_FILTER_CATEGORIES,
  createDefaultEnabledCategories,
  getPrimaryPolicyCategory,
  policyMatchesCategoryFilters,
} from '../src/utils/calendarCategoryTheme.js';
import {
  formatCalendarToolbarTitle,
  getWeekDatesSundayStart,
  shiftFocusDate,
} from '../src/utils/calendarViewNavigation.js';

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
    categories: ['housing'],
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

test('createDefaultEnabledCategories는 모든 필터 분야를 포함한다', () => {
  const enabled = createDefaultEnabledCategories();
  assert.equal(enabled.size, CALENDAR_FILTER_CATEGORIES.length);
  for (const category of CALENDAR_FILTER_CATEGORIES) {
    assert.equal(enabled.has(category), true);
  }
});

test('policyMatchesCategoryFilters는 categories·other fallback을 처리한다', () => {
  const enabled = new Set(['housing', 'other'] as const);
  assert.equal(policyMatchesCategoryFilters(createPolicy({ categories: ['housing'] }), enabled), true);
  assert.equal(policyMatchesCategoryFilters(createPolicy({ categories: ['finance'] }), enabled), false);
  assert.equal(policyMatchesCategoryFilters(createPolicy({ categories: [] }), enabled), true);
});

test('getPrimaryPolicyCategory는 첫 분야 또는 other를 반환한다', () => {
  assert.equal(getPrimaryPolicyCategory(createPolicy({ categories: ['finance', 'welfare'] })), 'finance');
  assert.equal(getPrimaryPolicyCategory(createPolicy({ categories: [] })), 'other');
});

test('getWeekDatesSundayStart는 Sunday-start 7일 범위를 만든다', () => {
  const week = getWeekDatesSundayStart('2026-08-13');
  assert.deepEqual(week, [
    '2026-08-09',
    '2026-08-10',
    '2026-08-11',
    '2026-08-12',
    '2026-08-13',
    '2026-08-14',
    '2026-08-15',
  ]);
});

test('shiftFocusDate와 formatCalendarToolbarTitle', () => {
  assert.equal(shiftFocusDate('2026-08-13', 'day', 1), '2026-08-14');
  assert.equal(shiftFocusDate('2026-08-13', 'week', 1), '2026-08-20');
  assert.equal(shiftFocusDate('2026-08-13', 'month', 1), '2026-09-13');
  assert.equal(shiftFocusDate('2026-01-31', 'month', 1), '2026-02-28');
  assert.equal(formatCalendarToolbarTitle('2026-08-13', 'month'), 'August 2026');
  assert.equal(formatCalendarToolbarTitle('2026-08-13', 'day'), 'August 13, 2026');
  assert.match(formatCalendarToolbarTitle('2026-08-13', 'week'), /Aug 9.*Aug 15, 2026/);
});

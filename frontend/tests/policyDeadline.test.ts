import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto } from '../src/types/policy.js';
import {
  diffDaysBetweenYmd,
  getDDayLabel,
  getKstDateString,
  getPolicyDeadlineInfo,
} from '../src/utils/policyDeadline.js';

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

test('getKstDateString은 Asia/Seoul 날짜를 반환한다', () => {
  const kstDate = getKstDateString(new Date('2026-08-10T20:00:00.000Z'));
  assert.equal(kstDate, '2026-08-11');
});

test('종료일 null 정책은 D-Day·달력 slot을 생성하지 않는다', () => {
  const info = getPolicyDeadlineInfo(
    createPolicy({ application_end: null, application_schedule: 'always' }),
  );

  assert.equal(info.label, '상시');
  assert.equal(info.hasCalendarSlot, false);
});

test('KST 기준 D-Day 라벨을 계산한다', () => {
  const reference = new Date('2026-08-11T05:00:00.000Z');
  const label = getDDayLabel(
    createPolicy({ application_end: '2026-08-20' }),
    reference,
  );

  assert.equal(label, 'D-9');
});

test('마감일 당일은 D-Day를 반환한다', () => {
  const reference = new Date('2026-08-11T05:00:00.000Z');
  const label = getDDayLabel(
    createPolicy({ application_end: '2026-08-11' }),
    reference,
  );

  assert.equal(label, 'D-Day');
});

test('diffDaysBetweenYmd는 YYYY-MM-DD 차이를 계산한다', () => {
  assert.equal(diffDaysBetweenYmd('2026-08-11', '2026-08-20'), 9);
});

test('closed 상태 정책은 마감 라벨과 calendar slot 없음', () => {
  const info = getPolicyDeadlineInfo(
    createPolicy({ application_status: 'closed', application_end: '2026-12-31' }),
  );

  assert.equal(info.label, '마감');
  assert.equal(info.hasCalendarSlot, false);
});

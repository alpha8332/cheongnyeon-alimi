import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDto } from '../src/types/policy.js';
import {
  buildPolicyDeadlineIcs,
  canDownloadPolicyIcs,
  escapeIcsText,
} from '../src/utils/policyIcs.js';

function createPolicy(overrides: Partial<PolicyDto> = {}): PolicyDto {
  return {
    schema_version: '1.1.0',
    source_id: 'test',
    source_name: 'Test',
    external_id: null,
    title: 'Policy; A, test',
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
    id: 42,
    created_at: '2026-08-11T00:00:00.000Z',
    updated_at: '2026-08-11T00:00:00.000Z',
    ...overrides,
  };
}

test('escapeIcsText는 RFC5545 특수문자를 escape한다', () => {
  assert.equal(escapeIcsText('a;b,c\nd'), 'a\\;b\\,c\\nd');
});

test('canDownloadPolicyIcs는 application_end 없으면 false', () => {
  assert.equal(canDownloadPolicyIcs(createPolicy({ application_end: null })), false);
});

test('buildPolicyDeadlineIcs는 all-day VEVENT를 생성한다', () => {
  const ics = buildPolicyDeadlineIcs(createPolicy());
  assert.ok(ics);
  assert.match(ics!, /BEGIN:VCALENDAR/);
  assert.match(ics!, /DTSTART;VALUE=DATE:20260820/);
  assert.match(ics!, /DTEND;VALUE=DATE:20260821/);
  assert.match(ics!, /Policy\\; A\\, test 신청 마감/);
});

import assert from 'node:assert/strict';
import test from 'node:test';
import type { PolicyDetailDto } from '../src/types/policy.js';
import { addDaysToYmd } from '../src/utils/calendarMonthGrid.js';
import { getKstDateString } from '../src/utils/policyDeadline.js';
import {
  formatPolicyIncomeSummary,
  getPolicyStatusBadge,
  getPolicyDetailStatusBadges,
  sanitizePolicyText,
  splitPolicyTextToBullets,
  splitPolicyTextToItems,
  splitCircleBulletLines,
} from '../src/utils/policyDetailContent.js';

function createPolicy(overrides: Partial<PolicyDetailDto> = {}): PolicyDetailDto {
  return {
    schema_version: '1.2.0',
    source_id: 'test',
    source_name: 'Test Source',
    external_id: null,
    title: 'Test Policy',
    organization: 'Test Org',
    summary: null,
    category_text: null,
    categories: ['housing'],
    application_period_text: null,
    application_start: '2026-08-01',
    application_end: '2026-08-20',
    application_schedule: 'fixed_period',
    application_status: 'open',
    region_text: null,
    regions: ['서울특별시'],
    age_min: 19,
    age_max: 34,
    age_condition_text: null,
    eligibility_text: '청년 대상',
    support_content: '월 30만원 지원',
    application_method: '온라인 신청',
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
    eligibility_summary: {
      coverage: 'partial',
      requirements: [],
      exclusions: [],
      preferences: [],
      documents: [],
      unknowns: [],
      institutional_contacts: [],
    },
    ...overrides,
  };
}

test('sanitizePolicyText는 HTML·공백을 정제한다', () => {
  assert.equal(
    sanitizePolicyText('<b>주거</b>  지원\n\n\n•  신청'),
    '주거 지원\n\n• 신청',
  );
});

test('splitPolicyTextToBullets는 줄 단위 bullet을 분리한다', () => {
  assert.deepEqual(splitPolicyTextToBullets('첫 줄\n• 둘째 줄\n- 셋째'), [
    '첫 줄',
    '둘째 줄',
    '셋째',
  ]);
});

test('splitPolicyTextToItems는 번호 목록을 ordered로 분리한다', () => {
  const result = splitPolicyTextToItems('1. 첫 항목\n2. 둘째 항목\n3. 셋째 항목');
  assert.equal(result.ordered, true);
  assert.deepEqual(result.items, ['첫 항목', '둘째 항목', '셋째 항목']);
});

test('splitPolicyTextToItems는 세미콜론 구분을 bullet으로 분리한다', () => {
  const result = splitPolicyTextToItems('서류 A; 서류 B; 서류 C');
  assert.equal(result.ordered, false);
  assert.deepEqual(result.items, ['서류 A', '서류 B', '서류 C']);
});

test('splitPolicyTextToItems는 날짜 slash를 보존하고 ※ 항목만 분리한다', () => {
  const result = splitPolicyTextToItems(
    '※ 1/9~12/31. 방문 접수 ※ 1차 종료/ 2차 5~6월 예정',
  );
  assert.equal(result.ordered, false);
  assert.deepEqual(result.items, [
    '1/9~12/31. 방문 접수',
    '1차 종료/ 2차 5~6월 예정',
  ]);
});

test('splitCircleBulletLines는 ○ 구분 요약을 줄 단위로 분리한다', () => {
  assert.deepEqual(
    splitCircleBulletLines('○ (지원대상) 청년 ○ (소득요건) 중위소득 150% ○ (지원내용) 월 30만원'),
    ['(지원대상) 청년', '(소득요건) 중위소득 150%', '(지원내용) 월 30만원'],
  );
  assert.deepEqual(splitCircleBulletLines('단일 문단 요약'), ['단일 문단 요약']);
});

test('getPolicyStatusBadge는 모집중·마감임박·상시를 구분한다', () => {
  assert.deepEqual(
    getPolicyStatusBadge(createPolicy({ application_end: '2027-12-31' })),
    { label: '모집중', variant: 'open' },
  );
  assert.deepEqual(
    getPolicyStatusBadge(
      createPolicy({
        application_end: addDaysToYmd(getKstDateString(), 3),
        application_status: 'open',
      }),
    ),
    { label: '마감임박', variant: 'hot' },
  );
  assert.deepEqual(
    getPolicyStatusBadge(
      createPolicy({
        application_schedule: 'always',
        application_end: null,
        application_status: 'open',
      }),
    ),
    { label: '상시', variant: 'always' },
  );
  assert.deepEqual(
    getPolicyStatusBadge(createPolicy({ application_status: 'closed' })),
    { label: '마감', variant: 'closed' },
  );
});

test('getPolicyDetailStatusBadges는 상시 일정과 접수 중 상태를 분리한다', () => {
  assert.deepEqual(
    getPolicyDetailStatusBadges(
      createPolicy({
        application_schedule: 'always',
        application_end: null,
        application_status: 'open',
      }),
    ),
    [
      { label: '상시', variant: 'always' },
      { label: '접수 중', variant: 'open' },
    ],
  );
});

test('formatPolicyIncomeSummary는 eligibility_summary income을 우선한다', () => {
  assert.equal(
    formatPolicyIncomeSummary(
      createPolicy({
        eligibility_summary: {
          coverage: 'partial',
          requirements: [{ category: 'income', text: '중위소득 150% 이하', evidence: [] }],
          exclusions: [],
          preferences: [],
          documents: [],
          unknowns: [],
          institutional_contacts: [],
        },
      }),
    ),
    '중위소득 150% 이하',
  );
});

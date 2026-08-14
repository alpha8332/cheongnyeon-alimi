import type { EligibilitySummaryDto } from '../types/eligibilitySummary.js';
import type { PolicyDto } from '../types/policy.js';

type EligibilityFixturePolicyDetail = PolicyDto & {
  eligibility_summary: EligibilitySummaryDto;
};

const MOCK_DETAIL_TIMESTAMP = '2026-08-11T00:00:00.000Z';

const COMPLETE_ELIGIBILITY_SUMMARY: EligibilitySummaryDto = {
  status: 'complete',
  requirements: [
    {
      category: 'age',
      content: '만 19세 이상 34세 이하 청년',
      evidence: {
        source_id: 'youthcenter',
        source_url: 'https://example.gov/youth-housing/apply',
        collected_at: '2026-08-10T12:00:00.000Z',
      },
    },
    {
      category: 'region',
      content:
        '해당 시·군·구 거주 또는 전입 예정자. ' +
        '상세 거주 요건 및 전입 일정은 지자체 공고를 확인해야 합니다. '.repeat(4) +
        '전입 신고 예정일과 실제 거주지가 신청 시점에 일치하는지 담당 기관에 문의할 수 있습니다.',
      evidence: {
        source_id: 'youthcenter',
        source_url: 'https://example.gov/youth-housing/apply',
        collected_at: '2026-08-10T12:00:00.000Z',
      },
    },
    {
      category: 'income',
      content: '가구 소득 기준 중위소득 150% 이하',
      evidence: {
        source_id: 'youthcenter',
        source_url: 'https://example.gov/youth-housing/apply',
        collected_at: '2026-08-10T12:00:00.000Z',
      },
    },
  ],
  exclusions: [
    {
      category: 'housing',
      content: '본인 또는 배우자 명의 주택을 보유한 경우',
      evidence: {
        source_id: 'youthcenter',
        source_url: 'https://example.gov/youth-housing/apply',
        collected_at: '2026-08-10T12:00:00.000Z',
      },
    },
  ],
  preferences: [
    {
      category: 'employment',
      content: '미취업 청년 또는 구직활동 중인 경우 우대',
      evidence: {
        source_id: 'youthcenter',
        source_url: 'https://example.gov/youth-housing/apply',
        collected_at: '2026-08-10T12:00:00.000Z',
      },
    },
  ],
  required_documents: [
    {
      name: '주민등록등본',
      content: '최근 1개월 이내 발급',
      evidence: {
        source_id: 'youthcenter',
        source_url: 'https://example.gov/youth-housing/apply',
        collected_at: '2026-08-10T12:00:00.000Z',
      },
    },
    {
      name: '소득증명서',
      content: null,
      evidence: {
        source_id: 'youthcenter',
        source_url: 'https://example.gov/youth-housing/apply',
        collected_at: '2026-08-10T12:00:00.000Z',
      },
    },
  ],
  unknown_conditions: [],
  institutional_contacts: [
    {
      label: '청년주거 상담',
      value: '1588-0000',
      contact_type: 'phone',
    },
    {
      label: '공식 신청 페이지',
      value: 'https://example.gov/youth-housing/apply',
      contact_type: 'url',
    },
  ],
};

const PARTIAL_ELIGIBILITY_SUMMARY: EligibilitySummaryDto = {
  status: 'partial',
  requirements: [
    {
      category: 'age',
      content: '만 19세 이상 39세 이하',
      evidence: {
        source_id: 'bokjiro',
        source_url: 'https://example.gov/welfare/loan',
        collected_at: '2026-08-09T09:30:00.000Z',
      },
    },
    {
      category: 'other',
      content: '참여 대상 세부 요건은 기관 안내에 따름',
      evidence: null,
    },
  ],
  exclusions: [],
  preferences: [
    {
      category: 'employment',
      content: '창업 준비 중인 청년',
      evidence: null,
    },
  ],
  required_documents: [
    {
      name: '신분증 사본',
      content: null,
      evidence: {
        source_id: 'bokjiro',
        source_url: 'https://example.gov/welfare/loan',
        collected_at: '2026-08-09T09:30:00.000Z',
      },
    },
  ],
  unknown_conditions: [
    '가구 단위 소득·재산 기준은 원문 표와 기준연도 확인 필요',
    '타 지원과 중복 수혜 가능 여부는 담당 기관 확인 필요',
  ],
  institutional_contacts: [
    {
      label: '복지로 안내',
      value: 'https://example.gov/welfare/loan',
      contact_type: 'url',
    },
  ],
};

const UNKNOWN_ELIGIBILITY_SUMMARY: EligibilitySummaryDto = {
  status: 'unknown',
  requirements: [],
  exclusions: [],
  preferences: [],
  required_documents: [],
  unknown_conditions: [
    '원문에 자격요건 상세가 없어 구조화할 수 없음',
    '공식 신청 페이지 또는 담당 기관 문의로 확인 필요',
  ],
  institutional_contacts: [],
};

export const ELIGIBILITY_SUMMARY_FIXTURES: Readonly<
  Record<EligibilitySummaryDto['status'], EligibilitySummaryDto>
> = {
  complete: COMPLETE_ELIGIBILITY_SUMMARY,
  partial: PARTIAL_ELIGIBILITY_SUMMARY,
  unknown: UNKNOWN_ELIGIBILITY_SUMMARY,
};

function createPolicyDetailFixture(
  id: number,
  title: string,
  eligibilitySummary: EligibilitySummaryDto,
): EligibilityFixturePolicyDetail {
  return {
    schema_version: '1.1.0',
    source_id: 'mock-eligibility',
    source_name: 'Mock Eligibility Fixture',
    external_id: `mock-eligibility-${id}`,
    title,
    organization: 'Mock Organization',
    summary: 'FE7-00 eligibility summary mock detail envelope',
    category_text: '주거',
    categories: ['housing'],
    application_period_text: '상시',
    application_start: null,
    application_end: null,
    application_schedule: 'always',
    application_status: 'open',
    region_text: '전국',
    regions: ['전국'],
    age_min: 19,
    age_max: 34,
    age_condition_text: null,
    eligibility_text: '원문 자격 안내(레거시 필드)',
    support_content: null,
    application_method: null,
    education_statuses: [],
    employment_statuses: [],
    required_conditions: [],
    preferred_conditions: [],
    excluded_conditions: [],
    source_url: 'https://example.gov/mock-eligibility',
    collected_at: MOCK_DETAIL_TIMESTAMP,
    data_quality_status: 'valid',
    id,
    created_at: MOCK_DETAIL_TIMESTAMP,
    updated_at: MOCK_DETAIL_TIMESTAMP,
    eligibility_summary: eligibilitySummary,
  };
}

/** Mock policy detail envelopes for Browser·contract tests (FE7-00). */
export const MOCK_POLICY_DETAIL_FIXTURES: readonly EligibilityFixturePolicyDetail[] = [
  createPolicyDetailFixture(
    9101,
    'Mock Complete Eligibility Policy',
    COMPLETE_ELIGIBILITY_SUMMARY,
  ),
  createPolicyDetailFixture(
    9102,
    'Mock Partial Eligibility Policy',
    PARTIAL_ELIGIBILITY_SUMMARY,
  ),
  createPolicyDetailFixture(
    9103,
    'Mock Unknown Eligibility Policy',
    UNKNOWN_ELIGIBILITY_SUMMARY,
  ),
];

export const MOCK_ELIGIBILITY_POLICY_IDS = {
  complete: 9101,
  partial: 9102,
  unknown: 9103,
} as const;

export function getMockPolicyDetailById(
  policyId: number,
): EligibilityFixturePolicyDetail | undefined {
  return MOCK_POLICY_DETAIL_FIXTURES.find((policy) => policy.id === policyId);
}

export function getEligibilitySummaryFixture(
  status: EligibilitySummaryDto['status'],
): EligibilitySummaryDto {
  return ELIGIBILITY_SUMMARY_FIXTURES[status];
}

export function attachEligibilitySummary(
  policy: PolicyDto,
  summary: EligibilitySummaryDto,
): EligibilityFixturePolicyDetail {
  return {
    ...policy,
    eligibility_summary: summary,
  };
}

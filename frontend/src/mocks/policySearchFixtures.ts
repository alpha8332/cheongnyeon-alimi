import type { PolicyDto } from '@/types/policy';
import type {
  DimensionVerdicts,
  InterpretedCondition,
  PolicySearchHit,
  PolicySearchInterpretedConditions,
  PolicySearchResponse,
  UnconfirmedCondition,
} from '@/types/policySearch';
import type { ResolvedPolicySearchQuery } from '@/mocks/policySearchRequest';

export type PolicySearchMockScenarioId = 'M1' | 'M2' | 'M3' | 'M4' | 'M6';

export interface PolicySearchHitFixture {
  policy_id: number;
  score: number;
  verdicts: DimensionVerdicts;
  reason_codes: string[];
  message: string;
  unconfirmed_conditions: UnconfirmedCondition[];
}

export interface PolicySearchScenarioFixture {
  scenario: PolicySearchMockScenarioId;
  description: string;
  total: number;
  interpreted_conditions: PolicySearchInterpretedConditions;
  items: PolicySearchHitFixture[];
}

export function countUnknownVerdicts(verdicts: DimensionVerdicts): number {
  return (Object.values(verdicts) as Array<DimensionVerdicts[keyof DimensionVerdicts]>).filter(
    (verdict) => verdict === 'unknown',
  ).length;
}

export function materializePolicySearchHit(
  policies: readonly PolicyDto[],
  fixture: PolicySearchHitFixture,
): PolicySearchHit {
  const policy = policies.find((candidate) => candidate.id === fixture.policy_id);

  if (!policy) {
    throw new Error(
      `Mock policy id ${fixture.policy_id} is missing from canonical Seed policies.`,
    );
  }

  return {
    policy,
    score: fixture.score,
    verdicts: fixture.verdicts,
    unknown_count: countUnknownVerdicts(fixture.verdicts),
    reason_codes: [...fixture.reason_codes],
    message: fixture.message,
    unconfirmed_conditions: fixture.unconfirmed_conditions.map((item) => ({
      ...item,
    })),
  };
}

export function materializePolicySearchResponse(
  policies: readonly PolicyDto[],
  fixture: PolicySearchScenarioFixture,
  query: ResolvedPolicySearchQuery,
): PolicySearchResponse {
  const hits = fixture.items.map((item) =>
    materializePolicySearchHit(policies, item),
  );
  const offset = (query.page - 1) * query.limit;

  return {
    total: fixture.total,
    page: query.page,
    limit: query.limit,
    interpreted_conditions: {
      ...fixture.interpreted_conditions,
      conditions: fixture.interpreted_conditions.conditions.map(cloneCondition),
      override_fields: [...fixture.interpreted_conditions.override_fields],
      uninterpreted_terms: [...fixture.interpreted_conditions.uninterpreted_terms],
    },
    items: hits.slice(offset, offset + query.limit),
  };
}

function cloneCondition(condition: InterpretedCondition): InterpretedCondition {
  return {
    ...condition,
    candidates: [...condition.candidates],
  };
}

export const POLICY_SEARCH_SCENARIO_FIXTURES: Record<
  PolicySearchMockScenarioId,
  PolicySearchScenarioFixture
> = {
  M1: {
    scenario: 'M1',
    description: 'q=서울 주거, region=서울특별시 — region match baseline',
    total: 1,
    interpreted_conditions: {
      q_raw: '서울 주거',
      q_clean: '서울 주거',
      conditions: [
        {
          dimension: 'region',
          value: '서울특별시',
          source: 'explicit',
          resolution: 'resolved',
          candidates: [],
        },
        {
          dimension: 'keyword',
          value: '주거',
          source: 'q',
          resolution: 'resolved',
          candidates: [],
        },
      ],
      override_fields: ['region'],
      uninterpreted_terms: [],
    },
    items: [
      {
        policy_id: 1,
        score: 0.91,
        verdicts: {
          region: 'match',
          age: null,
          status: null,
          category: 'match',
        },
        reason_codes: ['REGION_MATCH', 'KEYWORD_MATCH'],
        message: '서울 지역 주거 조건과 일치하는 온통청년 정책입니다.',
        unconfirmed_conditions: [],
      },
    ],
  },
  M2: {
    scenario: 'M2',
    description: 'q=전국 청년 — region unknown mixed results',
    total: 2,
    interpreted_conditions: {
      q_raw: '전국 청년',
      q_clean: '전국 청년',
      conditions: [
        {
          dimension: 'region',
          value: '전국',
          source: 'q',
          resolution: 'resolved',
          candidates: [],
        },
        {
          dimension: 'keyword',
          value: '청년',
          source: 'q',
          resolution: 'resolved',
          candidates: [],
        },
      ],
      override_fields: [],
      uninterpreted_terms: [],
    },
    items: [
      {
        policy_id: 2,
        score: 0.88,
        verdicts: {
          region: 'unknown',
          age: null,
          status: 'match',
          category: null,
        },
        reason_codes: ['REGION_UNKNOWN', 'STATUS_MATCH'],
        message: '전국 단위로 안내되나 지역 근거가 제한적입니다.',
        unconfirmed_conditions: [
          {
            field: 'region',
            reason_code: 'DATA_MISSING_REGION',
            message: '정책 원문에 지역 제한 근거가 없어 판단할 수 없습니다.',
          },
        ],
      },
      {
        policy_id: 1,
        score: 0.72,
        verdicts: {
          region: 'mismatch',
          age: 'match',
          status: 'mismatch',
          category: 'match',
        },
        reason_codes: ['REGION_MISMATCH', 'AGE_MATCH'],
        message: '청년·주거 키워드는 관련 있으나 전국 조건과 지역 정보가 다릅니다.',
        unconfirmed_conditions: [],
      },
    ],
  },
  M3: {
    scenario: 'M3',
    description: 'q=25세 일자리, age=25 — age match employment',
    total: 1,
    interpreted_conditions: {
      q_raw: '25세 일자리',
      q_clean: '25세 일자리',
      conditions: [
        {
          dimension: 'age',
          value: 25,
          source: 'explicit',
          resolution: 'resolved',
          candidates: [],
        },
        {
          dimension: 'category',
          value: 'employment',
          source: 'q',
          resolution: 'resolved',
          candidates: [],
        },
        {
          dimension: 'keyword',
          value: '일자리',
          source: 'q',
          resolution: 'resolved',
          candidates: [],
        },
      ],
      override_fields: ['age'],
      uninterpreted_terms: [],
    },
    items: [
      {
        policy_id: 2,
        score: 0.86,
        verdicts: {
          region: null,
          age: 'match',
          status: 'match',
          category: 'unknown',
        },
        reason_codes: ['AGE_MATCH', 'CATEGORY_UNKNOWN'],
        message: '25세 조건은 충족하나 일자리 카테고리 근거가 제한적입니다.',
        unconfirmed_conditions: [
          {
            field: 'category',
            reason_code: 'DATA_MISSING_CATEGORY',
            message: '카테고리 분류 근거가 불명확합니다.',
          },
        ],
      },
    ],
  },
  M4: {
    scenario: 'M4',
    description: 'q=복지로 생활 — partial-only multi-unknown',
    total: 2,
    interpreted_conditions: {
      q_raw: '복지로 생활',
      q_clean: '복지로 생활',
      conditions: [
        {
          dimension: 'keyword',
          value: '생활',
          source: 'q',
          resolution: 'resolved',
          candidates: [],
        },
      ],
      override_fields: [],
      uninterpreted_terms: ['복지로'],
    },
    items: [
      {
        policy_id: 3,
        score: 0.65,
        verdicts: {
          region: 'unknown',
          age: 'unknown',
          status: 'unknown',
          category: 'unknown',
        },
        reason_codes: ['PARTIAL_POLICY_DATA', 'REGION_UNKNOWN', 'AGE_UNKNOWN'],
        message: '복지로 partial 정책으로 다수 조건 근거가 없습니다.',
        unconfirmed_conditions: [
          {
            field: 'region',
            reason_code: 'DATA_MISSING_REGION',
            message: '지역 정보가 없습니다.',
          },
          {
            field: 'age',
            reason_code: 'DATA_MISSING_AGE',
            message: '연령 정보가 없습니다.',
          },
          {
            field: 'status',
            reason_code: 'DATA_MISSING_STATUS',
            message: '신청 상태 정보가 없습니다.',
          },
        ],
      },
      {
        policy_id: 4,
        score: 0.58,
        verdicts: {
          region: 'unknown',
          age: 'unknown',
          status: 'unknown',
          category: 'unknown',
        },
        reason_codes: ['PARTIAL_POLICY_DATA'],
        message: '목록 전용 partial 정책으로 자격요건 직접 확인이 필요합니다.',
        unconfirmed_conditions: [
          {
            field: 'general',
            reason_code: 'PARTIAL_POLICY_DATA',
            message: 'partial 품질 등급으로 일부 차원 판정이 유보됩니다.',
          },
        ],
      },
    ],
  },
  M6: {
    scenario: 'M6',
    description: 'q=지원금&keyword=지원금 — explicit keyword with required q',
    total: 1,
    interpreted_conditions: {
      q_raw: '지원금',
      q_clean: '지원금',
      conditions: [
        {
          dimension: 'keyword',
          value: '지원금',
          source: 'explicit',
          resolution: 'resolved',
          candidates: [],
        },
      ],
      override_fields: ['keyword'],
      uninterpreted_terms: [],
    },
    items: [
      {
        policy_id: 3,
        score: 0.77,
        verdicts: {
          region: 'unknown',
          age: null,
          status: null,
          category: 'match',
        },
        reason_codes: ['KEYWORD_MATCH', 'PARTIAL_POLICY_DATA'],
        message: '지원금 키워드와 부분 일치하는 partial 정책입니다.',
        unconfirmed_conditions: [
          {
            field: 'region',
            reason_code: 'DATA_MISSING_REGION',
            message: '지역 정보가 없어 지원 가능 여부를 확정할 수 없습니다.',
          },
        ],
      },
    ],
  },
};

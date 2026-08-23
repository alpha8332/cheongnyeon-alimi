import { test as baseTest, type APIRequestContext } from '@playwright/test';

/** Playwright webServer가 `VITE_USE_MOCK=false`로 기동된 actual API E2E 환경 */
export function isActualApiMode(): boolean {
  return process.env.VITE_USE_MOCK === 'false';
}

export function skipUnlessActualApi(
  test: typeof baseTest,
  reason = 'VITE_USE_MOCK=false + Backend API가 준비된 환경에서만 실행합니다.',
): void {
  test.skip(!isActualApiMode(), reason);
}

export function skipIfActualApi(
  test: typeof baseTest,
  reason = 'Mock Seed 전용 시나리오 — Actual API(VITE_USE_MOCK=false) 환경에서는 skip합니다.',
): void {
  test.skip(isActualApiMode(), reason);
}

interface ActualPolicyDto {
  id: number;
  source_id: string;
  external_id: string;
  title: string;
  application_end: string | null;
  data_quality_status: string;
  eligibility_summary: { coverage: string } | null;
}

interface ActualPolicySearchResponse {
  items: Array<{ policy: ActualPolicyDto }>;
}

export const DATA06_KOSAF_IDENTITY = {
  query: '국가근로장학금',
  sourceId: 'kosaf-scholarship-web',
  externalId: 'scholarship05_04_01',
  title: '국가근로장학금',
  eligibilityCoverage: 'unknown',
} as const;

/** Numeric DB id 대신 stable source identity로 canonical actual 정책을 찾는다. */
export async function resolveActualPolicyByIdentity(
  request: APIRequestContext,
  identity = DATA06_KOSAF_IDENTITY,
): Promise<ActualPolicyDto> {
  const apiBaseUrl = process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
  const response = await request.get(`${apiBaseUrl}/api/v1/policies/search`, {
    params: {
      q: identity.query,
      include_partial: 'true',
      page: '1',
      limit: '20',
    },
  });

  if (!response.ok()) {
    throw new Error(`Actual policy search failed: HTTP ${response.status()}`);
  }

  const payload = (await response.json()) as ActualPolicySearchResponse;
  const match = payload.items
    .map((item) => item.policy)
    .find(
      (policy) =>
        policy.source_id === identity.sourceId &&
        policy.external_id === identity.externalId,
    );

  if (!match) {
    throw new Error(
      `Actual policy not found: ${identity.sourceId}/${identity.externalId}`,
    );
  }

  return match;
}

/** 현재 PostgreSQL snapshot에서 내용으로 검증하는 actual API golden fixture. */
export const ACTUAL_API_FIXTURES = {
  SEARCH_GOLDEN_POLICY_TITLE: '청년단기숙소 지원사업',
  SEARCH_GOLDEN_QUERY:
    '/search?q=%EC%B2%9C%EC%95%88+%EC%82%AC%EB%8A%94+27%EC%82%B4+%EC%B2%AD%EB%85%84+%EB%8B%A8%EA%B8%B0%EC%88%99%EC%86%8C+%EC%A7%80%EC%9B%90+%EB%B0%9B%EC%9D%84+%EC%88%98+%EC%9E%88%EB%82%98%3F',
  RECOMMENDATION: {
    region: '천안시',
    age: '27',
    category: 'housing',
    expectedTitle: '청년단기숙소 지원사업',
  },
} as const;

/** Mock MSW Seed 전용 식별자 (actual DB에 없음) */
export const MOCK_ONLY = {
  RECOMMENDATION_EMPTY_REGION: 'MOCK_EMPTY',
  HOUSING_POLICY_TITLE: '합성 청년 주거 지원',
  ALWAYS_OPEN_POLICY_TITLE: '합성 상시 생활 지원',
  PARTIAL_POLICY_ID: 1,
  PARTIAL_POLICY_TITLE: '합성 청년 주거 지원',
  UNKNOWN_POLICY_ID: 4,
  UNKNOWN_POLICY_TITLE: '합성 목록 전용 지원',
} as const;

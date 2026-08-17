import { test as baseTest } from '@playwright/test';

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

/**
 * 현재 PostgreSQL snapshot 기준 actual API golden fixture.
 * `15095`는 과거 handoff 예시였으나 현재 DB에는 `160`이 동일 정책(청년단기숙소)이다.
 */
export const ACTUAL_API_FIXTURES = {
  SEARCH_GOLDEN_POLICY_ID: 160,
  SEARCH_GOLDEN_POLICY_TITLE: '청년단기숙소 지원사업',
  SEARCH_GOLDEN_QUERY:
    '/search?q=%EC%B2%9C%EC%95%88+%EC%82%AC%EB%8A%94+27%EC%82%B4+%EC%B2%AD%EB%85%84+%EB%8B%A8%EA%B8%B0%EC%88%99%EC%86%8C+%EC%A7%80%EC%9B%90+%EB%B0%9B%EC%9D%84+%EC%88%98+%EC%9E%88%EB%82%98%3F',
  RECOMMENDATION: {
    region: '천안시',
    age: '27',
    category: 'housing',
    expectedTitle: '청년단기숙소 지원사업',
  },
  ELIGIBILITY_POLICY_ID: 160,
  ELIGIBILITY_POLICY_TITLE: '청년단기숙소 지원사업',
  ELIGIBILITY_COVERAGE: 'unknown',
  ICS_DISABLED_POLICY_ID: 3,
  ICS_DISABLED_POLICY_TITLE: '전세보증금반환보증 보증료 지원',
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

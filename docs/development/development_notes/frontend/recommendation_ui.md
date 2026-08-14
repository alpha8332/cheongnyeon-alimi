# Frontend Recommendation UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11 (FE6-05 Browser E2E: 2026-08-12)
- 담당 영역: Frontend
- 상태: completed
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [Recommendation UI Forest 개발 계획](../../develop_plan/frontend/06_recommendation_ui.md)
- 현재 Slice: FE6-05 completed (Forest Browser 검증 완료)

## 목적

W4-G0 결정적 추천 API 계약을 Frontend TypeScript·Mock·UI(FE6-00~04)로 소비하고
`/search` NL 검색 route와 분리한다.

## Forest 범위

이 기록은 Frontend 06 Slice 구현·검증 결과를 누적한다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE6-00 | completed | DTO·Mock handler·API client·`/recommendations` placeholder |
| FE6-01 | completed | 조건 form·FE5 localStorage 연동·submit → API |
| FE6-02 | completed | 결과 목록·reason·detail link·favorite toggle |
| FE6-03 | completed | error/empty/loading shell·retry·unconfirmed banner |
| FE6-04 | completed | `RegionListCollapse`·mobile region truncate |
| FE6-05 | completed | Playwright Browser E2E·search golden 회귀 |

## 구현 내용

### FE6-00 — 추천 DTO·Mock·route 계약

- `frontend/src/types/recommendation.ts`
- `frontend/src/mocks/recommendationFixtures.ts`, `recommendationHandlers.ts`
- `frontend/src/api/recommendation.ts`
- `frontend/src/App.tsx` — `/recommendations`
- `frontend/tests/recommendation.contract.test.ts`

### FE6-01 — 조건 입력·localStorage 연동

- `frontend/src/utils/savedConditionsForm.ts` — 홈·추천 공유 form helpers
- `frontend/src/components/recommendation/RecommendationConditionForm.tsx`
- `frontend/src/pages/user/RecommendationPage.tsx` — submit → `postRecommendations`
- `frontend/tests/savedConditionsForm.test.ts`

### FE6-02 — 추천 결과·이유 UI

- `frontend/src/components/recommendation/RecommendationResultList.tsx`
- `frontend/src/components/recommendation/RecommendationResultCard.tsx`
- `frontend/src/utils/recommendationReasonHelpers.ts`
- `frontend/src/utils/policyDetailNavigation.ts` — `buildRecommendationItemDetailPath`
- score 숫자 미노출; disclaimer·reason label만 표시

### FE6-03 — API 오류·재시도·미확정 배너

- `frontend/src/utils/recommendationErrors.ts`
- `frontend/src/types/recommendationErrors.ts`
- Error/Empty/Loading shell components
- `RecommendationUnconfirmedBanner` + row-level unknown list
- `frontend/tests/recommendationErrors.test.ts`

### FE6-04 — 지역 축약·기본 접근성

- `frontend/src/components/recommendation/RegionListCollapse.tsx`
- theme CSS — mobile word-break, expand/collapse toggle `focus-visible`

### Route·API 경계

| Route / API | 역할 |
| --- | --- |
| `/search` | Gate G1 NL `GET /api/v1/policies/search` |
| `/recommendations` | W4-G0 structured `POST /api/v1/recommendations` |

조건은 FE5 localStorage·form only; URL·서버 영구 저장 없음.

## 설계 결정

- 홈 `SavedConditionsPanel`과 추천 form은 `savedConditionsForm` utils·
  `useSavedConditions`를 공유한다.
- 추천 error UX tone은 Policy Search shell 패턴을 재사용한다.
- partial item detail link는 `include_partial=true` query를 자동 부여한다.

### FE6-05 — Real API·Browser E2E (Playwright)

- `frontend/e2e/recommendation-ui.spec.ts`
  - Mock-first 12 scenarios: route boundary·loading·results·empty·empty→results
    recovery·detail·favorite·localStorage·region display·keyboard·mobile·
    `/search` golden 회귀·503 retry(Mock bypass annotation)
  - Real API golden: `VITE_USE_MOCK=false` 환경에서만 실행(skip)
- 422 API validation error shell은 form `parseSavedConditionsDraft` client
  normalize로 Browser UI에서 unreachable — `recommendation.contract.test.ts`·
  `recommendationErrors.test.ts`로 검증.
- Mock Seed에 3+ regions policy 없음 — `RegionListCollapse` expand E2E는
  단일 지역·「더 보기 없음」만 검증. partial unknown banner는
  `include_partial=false` 기본 request로 Mock 결과에 partial item 미포함.

## 주요 변경 파일

- `frontend/src/pages/user/RecommendationPage.tsx`
- `frontend/src/components/recommendation/*`
- `frontend/src/utils/savedConditionsForm.ts`
- `frontend/src/utils/recommendationErrors.ts`
- `frontend/src/utils/recommendationReasonHelpers.ts`
- `frontend/src/components/user/SavedConditionsPanel.tsx` (shared utils refactor)
- `frontend/src/styles/theme.css`
- `frontend/tests/savedConditionsForm.test.ts`
- `frontend/tests/recommendationErrors.test.ts`
- `frontend/tests/recommendationReasonHelpers.test.ts`
- `frontend/tests/recommendationDetailNavigation.test.ts`
- `frontend/e2e/recommendation-ui.spec.ts`

## 검증 결과

```text
cd frontend && npm test   — 159 passed
cd frontend && npm run lint — passed
cd frontend && npm run build — passed (FE6-04 기준; FE6-05에서 재실행하지 않음)
cd frontend && npm run test:e2e -- e2e/recommendation-ui.spec.ts — 12 passed, 1 skipped (Real API)
python3 scripts/validate_docs.py — passed
```

Browser·Playwright E2E는 FE6-05에서 실행 완료.

## 남은 작업

- Real API E2E(`VITE_USE_MOCK=false`) 및 partial·long-region positive Browser case는
  Backend actual API·Seed 데이터 준비 후 FE9 또는 별도 회귀에서 실행
- W4-G0 Gate 후 `docs/api/` recommendation 절 추가

## 관련 문서

- [Integration 06 Recommendation Vertical Slice](../../develop_plan/integration/06_recommendation_vertical_slice.md)
- [User Service Features (FE5)](../../develop_plan/frontend/05_user_service_features.md)
- [Policy Search (FE4)](../../develop_plan/frontend/04_policy_search.md)

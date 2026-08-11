# Frontend Recommendation UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [Recommendation UI Forest 개발 계획](../../develop_plan/frontend/06_recommendation_ui.md)
- 현재 Slice: FE6-00 completed

## 목적

W4-G0 결정적 추천 API 계약을 Frontend TypeScript·Mock·route shell(FE6-00)로
고정하고 `/search` NL 검색 route와 분리한다.

## Forest 범위

이 기록은 Frontend 06 Slice 구현·검증 결과를 누적한다. 조건 form·결과 카드 UI
(FE6-01+)는 이 Slice 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE6-00 | completed | DTO·Mock handler·API client·`/recommendations` placeholder |
| FE6-01 | pending | 조건 입력·localStorage 연동 |
| FE6-02 | pending | 추천 결과·이유 UI |

## 구현 내용

### FE6-00 — 추천 DTO·Mock·route 계약

- `frontend/src/types/recommendation.ts`
  - Backend draft `RecommendationRequest`·`RecommendationItem`·`RecommendationResponse`
  - API: `POST /api/v1/recommendations`, `GET /api/v1/policies/recommendations`
  - Client route: `RECOMMENDATION_APP_ROUTE = '/recommendations'`
- `frontend/src/mocks/recommendationFixtures.ts`, `recommendationHandlers.ts`
  - seed 기반 Mock 200, `region=MOCK_EMPTY` empty 200, age/limit 422
  - deterministic sort: score DESC, id ASC
- `frontend/src/api/recommendation.ts` — Mock-first `postRecommendations`
- `frontend/src/pages/user/RecommendationPage.tsx` — route placeholder
- `frontend/src/App.tsx` — `/recommendations` 등록 (`/search`와 분리)
- `frontend/tests/recommendation.contract.test.ts`

### Route·API 경계

| Route / API | 역할 |
| --- | --- |
| `/search` | Gate G1 NL `GET /api/v1/policies/search` (PolicySearchHit nested DTO) |
| `/recommendations` | W4-G0 structured 조건 `POST /api/v1/recommendations` (flat RecommendationItem) |

조건은 FE6-01에서 localStorage·form으로 관리; URL·서버 영구 저장 없음(FE6-01).

### Backend draft 정렬 메모

| 영역 | Backend draft | FE6-00 |
| --- | --- | --- |
| Item shape | flat `RecommendationItem` (`lead`, `min_age`, single `category`) | 1:1 TypeScript |
| Status filter | `open`·`upcoming`·`closed` | `upcoming` → Policy `scheduled` Mock 매핑 |
| `score` | API 필드 포함 | DTO 포함; UI 노출은 FE6-02에서 금지 |
| Real API | `origin/feature/backend/policy-recommendation` | 로컬 merge 전 Mock-only |

## 설계 결정

- Mock handler는 Policy Search scenario(M1~M6)와 독립; 추천 전용 fixture trigger
  (`MOCK_EMPTY`) 사용.
- `RecommendationApiError`는 Policy Search와 동일 FastAPI `detail` 패턴.
- GET query client는 FE6-05 Real API 단계에서 추가 가능; FE6-00는 POST client만.

## 주요 변경 파일

- `frontend/src/types/recommendation.ts`
- `frontend/src/mocks/recommendationFixtures.ts`
- `frontend/src/mocks/recommendationHandlers.ts`
- `frontend/src/api/recommendation.ts`
- `frontend/src/api/recommendationApiError.ts`
- `frontend/src/pages/user/RecommendationPage.tsx`
- `frontend/src/App.tsx`
- `frontend/tests/recommendation.contract.test.ts`

## 검증 결과

- `npm run test` (frontend): **105 passed** (recommendation contract 7건 포함)
- `npm run lint`: passed
- `npm run build`: passed
- `python scripts/validate_docs.py`: passed

## 남은 작업

- FE6-01: 조건 form·FE5 localStorage 연동
- FE6-02: 결과·reason UI (score 숫자 미노출)
- FE6-05: Real API·Browser E2E
- W4-G0 Gate 후 `docs/api/` recommendation 절 추가

## 관련 문서

- [Integration 06 Recommendation Vertical Slice](../../develop_plan/integration/06_recommendation_vertical_slice.md)
- [User Service Features (FE5)](../../develop_plan/frontend/05_user_service_features.md)
- [Policy Search (FE4)](../../develop_plan/frontend/04_policy_search.md)

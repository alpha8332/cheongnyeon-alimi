# Frontend CollectionRun Admin UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11 (FE3-06 Toast·a11y: 2026-08-12, Phase 2 dashboard: 2026-07-28)
- 담당 영역: Frontend
- 상태: completed
- 브랜치: `feature/frontend/style-and-ux-fixes` (Phase 2)
- 관련 계획:
  [CollectionRun Admin UI Forest 개발 계획](../../develop_plan/frontend/03_collection_run_admin_ui.md)
- 현재 Slice: FE3-06 completed (Forest 완료)

## 목적

관리자 CollectionRun UI Forest(FE3)의 PIN session·실행 이력·수동 실행 UI,
Mock-first Browser E2E(FE3-05), 공통 API Toast·a11y(FE3-06)를 구현·검증한다.

## Forest 범위

이 기록은 Frontend 03 Slice 구현·검증 결과를 누적한다. Backend merge 후 Real API
smoke 재검증은 Integration Gate 후 공동 확인한다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE3-00 | completed | Admin DTO·Mock·`/admin` shell·contract tests |
| FE3-01 | completed | PIN login·in-memory session·protected route·logout |
| FE3-02 | completed | 실행 기록 list·filter·pagination |
| FE3-03 | completed | run detail·status/stale badge·404 shell |
| FE3-04 | completed | manual run confirm·duplicate guard·list refetch |
| FE3-05 | completed | Playwright admin-run spec·env toggle·Mock E2E |
| FE3-06 | completed | ApiErrorToast·admin wiring·Toast/a11y Browser E2E |
| Phase 2 dashboard | completed | 집계 기반 DashboardPage·DataQualityPage·drill-down |

## Phase 2 — 집계 기반 관리자 대시보드 (2026-07-28)

Backend list·detail 집계 API 범위 내에서 placeholder였던
`DashboardPage`·`DataQualityPage`를 구현했다. 건별 파싱 실패·중복 후보
목록 API는 미제공이므로 UI·caption에서 제외하고 run detail·Log
바로가기로 drill-down한다.

- `frontend/src/pages/admin/DashboardPage.tsx` — 최신 run 1건 list+detail,
  started_at/finished_at·status badge·집계 metric card (2026-07-28 UX: subtitle·
  페이지 내 quick link nav 제거 — shell nav 사용)
- `frontend/src/pages/admin/DataQualityPage.tsx` — 최근 10회 list + parallel
  detail fetch, 회차별 failed/invalid/duplicate 비교 table
- `frontend/src/utils/adminDashboard.ts` — metric 정의·drill-down URL·variant
- `frontend/src/hooks/useAdminQualityRunSummaries.ts`
- `frontend/src/components/admin/AdminMetricCard.tsx`
- `frontend/src/components/admin/CollectionRunQualityTable.tsx`
- `frontend/e2e/admin-collection-run.spec.ts` — dashboard·quality 시나리오 추가
- `frontend/tests/adminDashboard.test.ts`

### 설계 결정 (Phase 2)

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| invalid/duplicate 표시 | detail API 병렬 fetch | list DTO subset에 없음 |
| Log drill-down | `/admin/logs` (필터 URL 미지원) | AdminLogsPage가 query 초기화 없음 |
| 건별 failure list | UI 미구현 | Backend API 보류 |

### Phase 2 검증

```text
cd frontend && npm test              — 213 passed
cd frontend && npm run lint          — passed
cd frontend && npm run build         — passed
cd frontend && npm run test:e2e -- e2e/admin-collection-run.spec.ts — 10 passed, 1 skipped
python3 scripts/validate_docs.py   — passed
```

## 구현 내용

### FE3-00 — Admin DTO·라우팅·Mock 계약

(2026-08-11 — 기존 기록 유지)

### FE3-01 — PIN login·session UI

- `frontend/src/utils/adminSessionStorage.ts` — in-memory session (localStorage 금지)
- `frontend/src/hooks/useAdminSession.ts`
- `frontend/src/components/admin/AdminProtectedRoute.tsx`
- `frontend/src/pages/admin/AdminLoginPage.tsx` — 4자리 PIN, 401/422/429 UX
- `frontend/src/utils/adminLoginPresentation.ts`
- `frontend/src/App.tsx` — `/admin/*` protected wrapper
- `frontend/src/layouts/AdminShellLayout.tsx` — logout button
- `frontend/tests/adminSessionStorage.test.ts`
- `frontend/tests/adminLoginPresentation.test.ts`

### FE3-02 — CollectionRun 목록·필터

- `frontend/src/pages/admin/CollectionRunsPage.tsx`
- `frontend/src/components/admin/CollectionRunFilters.tsx`
- `frontend/src/utils/collectionRunFilters.ts`
- `frontend/src/hooks/useCollectionRunsQuery.ts`
- loading·empty·error UI

### FE3-03 — CollectionRun 상세·stale

- `frontend/src/pages/admin/CollectionRunDetailPage.tsx`
- `frontend/src/components/admin/CollectionRunStatusBadge.tsx`
- `frontend/src/utils/collectionRunDisplay.ts`
- running/terminal/stale badge 분리, detail count aggregates, 404 shell
- `frontend/tests/collectionRunDisplay.test.ts`

### FE3-04 — 수동 실행 UI

- `frontend/src/components/admin/ManualCollectionRunTrigger.tsx`
- confirm dialog·submitting guard·running run disable
- 성공 시 list `refetch` (Mock trigger run_id는 fixtures에 없음 — 목록 갱신 UX만)

### FE3-05 — Real API·Browser·인계

- `frontend/e2e/admin-collection-run.spec.ts`
  - protected route redirect, wrong PIN, login, list·filter, detail·stale, 404,
    manual trigger disable/confirm, list→detail navigation
  - Real API golden 1건: `VITE_USE_MOCK=false`일 때만 실행(기본 skip)
- `frontend/playwright.config.ts` — webServer에 `VITE_USE_MOCK`·
  `VITE_API_BASE_URL` env 전달
- `frontend/README.md` — admin E2E 실행 절 추가

### FE3-06 — Admin API Toast·접근성

- `frontend/src/types/apiErrorToast.ts`
- `frontend/src/utils/adminApiErrorToast.ts` — HTTP status→Toast presentation·3s dedupe key
- `frontend/src/context/ApiErrorToastContext.ts`
- `frontend/src/components/common/ApiErrorToast.tsx` — non-blocking fixed Toast (`role=alert|status`)
- `frontend/src/components/common/ApiErrorToastProvider.tsx`
- `frontend/src/hooks/useApiErrorToast.ts`
- Admin wiring:
  - `AdminShellLayout` — provider for protected admin pages
  - `AdminLoginPage` — provider + 429/5xx Toast (401/422 inline 유지)
  - `CollectionRunsPage`·`CollectionRunDetailPage` — 401 toast+redirect, 5xx retry refetch
  - `ManualCollectionRunTrigger` — Toast on API error, Escape dialog close
- Mock audit hooks:
  - login PIN `5000` → HTTP 503 Toast
  - list filter `source_id=MOCK_503` → HTTP 503 Toast + retry
- `frontend/e2e/admin-toast-a11y.spec.ts` — 429·503·list retry·Escape·Enter·mobile
- `frontend/tests/adminApiErrorToast.test.ts`
- `theme.css` — `.api-error-toast*` styles, collection-run mobile table scroll (640px)

### Browser E2E 메모 (in-memory session)

관리자 session은 in-memory module state(FE3-01)이므로 full page reload
(`page.goto` to admin deep link) 시 session이 초기화된다. E2E는 login 후
SPA link navigation 또는 `history.pushState`+`popstate`로 route를 전환한다.

## 설계 결정

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| Session storage | in-memory module state | W4-G0 PIN·token 영구 localStorage 금지 |
| Protected routes | `AdminProtectedRoute` + login redirect state | `/admin/login` 제외 |
| List fetch | React Query `useCollectionRunsQuery` | 기존 Policy list 패턴 |
| Manual trigger | running item 존재 시 disable | Backend concurrent run guard UX |
| E2E Real API | conditional skip | 로컬 `:8000` admin path 미merge |
| API error UX | Toast non-blocking + 3s dedupe | W4-F5 admin subset; 401 inline on login form |
| 404 detail | inline shell (Toast 미사용) | develop_plan Toast 표 |

## 주요 변경 파일

- `frontend/src/types/apiErrorToast.ts`
- `frontend/src/utils/adminApiErrorToast.ts`
- `frontend/src/context/ApiErrorToastContext.ts`
- `frontend/src/components/common/ApiErrorToast.tsx`
- `frontend/src/components/common/ApiErrorToastProvider.tsx`
- `frontend/src/hooks/useApiErrorToast.ts`
- `frontend/src/pages/admin/AdminLoginPage.tsx`
- `frontend/src/pages/admin/CollectionRunsPage.tsx`
- `frontend/src/pages/admin/CollectionRunDetailPage.tsx`
- `frontend/src/components/admin/ManualCollectionRunTrigger.tsx`
- `frontend/src/layouts/AdminShellLayout.tsx`
- `frontend/src/api/collectionRuns.ts` (MOCK_503 audit hook)
- `frontend/src/mocks/adminSessionHandlers.ts` (PIN 5000 audit hook)
- `frontend/src/styles/theme.css`
- `frontend/e2e/admin-toast-a11y.spec.ts`
- `frontend/tests/adminApiErrorToast.test.ts`
- `frontend/e2e/admin-collection-run.spec.ts`
- `frontend/playwright.config.ts`
- `frontend/README.md`

## 검증 결과

```text
cd frontend && npm test              — 164 passed
cd frontend && npm run lint          — passed
cd frontend && npm run test:e2e -- e2e/admin-toast-a11y.spec.ts — 6 passed
cd frontend && npm run test:e2e -- e2e/admin-collection-run.spec.ts — 9 passed, 1 skipped
python3 scripts/validate_docs.py   — (post-update)
```

Real API smoke(`VITE_USE_MOCK=false`)는 Backend 04·05 admin path가 로컬
`:8000` OpenAPI에 merge된 후 재실행한다.

## 남은 작업

- Backend admin Forest merge 후 Real API E2E golden 재실행
- FE9-02 cross-Forest Toast dedupe·full a11y matrix regression
- `BE-ADMIN-RUN-HISTORY` Real PostgreSQL→API smoke는 Backend merge Gate 후
  Integration 측과 공동 확인

## 관련 문서

- [CollectionRun Admin UI 계획](../../develop_plan/frontend/03_collection_run_admin_ui.md)
- [Backend Admin Access Control](../../develop_plan/backend/04_admin_access_control.md)
- [Backend CollectionRun Admin API](../../develop_plan/backend/05_collection_run_admin_api.md)
- [Frontend 09 Integration and Regression](../../develop_plan/frontend/09_integration_and_regression.md)

# Frontend CollectionRun Admin UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [CollectionRun Admin UI Forest 개발 계획](../../develop_plan/frontend/03_collection_run_admin_ui.md)
- 현재 Slice: FE3-05 completed

## 목적

관리자 CollectionRun UI Forest(FE3)의 PIN session·실행 이력·수동 실행 UI와
Mock-first Browser E2E(FE3-05)를 구현·검증한다.

## Forest 범위

이 기록은 Frontend 03 Slice 구현·검증 결과를 누적한다. Toast·a11y subset
(FE3-06)과 Backend merge 후 Real API smoke 재검증은 후속 Slice다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE3-00 | completed | Admin DTO·Mock·`/admin` shell·contract tests |
| FE3-01 | completed | PIN login·in-memory session·protected route·logout |
| FE3-02 | completed | 실행 기록 list·filter·pagination |
| FE3-03 | completed | run detail·status/stale badge·404 shell |
| FE3-04 | completed | manual run confirm·duplicate guard·list refetch |
| FE3-05 | completed | Playwright admin-run spec·env toggle·Mock E2E |

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

## 주요 변경 파일

- `frontend/e2e/admin-collection-run.spec.ts`
- `frontend/playwright.config.ts`
- `frontend/README.md`
- (FE3-01~04 기존 admin pages·components·tests — 상동)

## 검증 결과

```text
cd frontend && npm test              — 159 passed
cd frontend && npm run lint          — passed (FE3-05 변경 없음)
cd frontend && npm run build         — passed (FE3-05 변경 없음)
cd frontend && npm run test:e2e -- e2e/admin-collection-run.spec.ts
                                     — 9 passed, 1 skipped (Real API golden)
python3 scripts/validate_docs.py   — passed
```

Real API smoke(`VITE_USE_MOCK=false`)는 Backend 04·05 admin path가 로컬
`:8000` OpenAPI에 merge된 후 재실행한다. 현재 Mock E2E로 Frontend admin run
소비 경로(PIN→list→detail→manual trigger)를 검증했다.

## 남은 작업

- FE3-06: Admin Toast·a11y (W4-F5·F8)
- Backend admin Forest merge 후 Real API E2E golden 재실행
- `BE-ADMIN-RUN-HISTORY` Real PostgreSQL→API smoke는 Backend merge Gate 후
  Integration 측과 공동 확인

## 관련 문서

- [CollectionRun Admin UI 계획](../../develop_plan/frontend/03_collection_run_admin_ui.md)
- [Backend Admin Access Control](../../develop_plan/backend/04_admin_access_control.md)
- [Backend CollectionRun Admin API](../../develop_plan/backend/05_collection_run_admin_api.md)

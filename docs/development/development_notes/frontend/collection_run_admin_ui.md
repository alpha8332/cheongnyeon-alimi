# Frontend CollectionRun Admin UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [CollectionRun Admin UI Forest 개발 계획](../../develop_plan/frontend/03_collection_run_admin_ui.md)
- 현재 Slice: FE3-04 completed (FE3-05 draft)

## 목적

관리자 CollectionRun UI Forest(FE3)의 PIN session·실행 이력·수동 실행 UI를
구현한다.

## Forest 범위

이 기록은 Frontend 03 Slice 구현·검증 결과를 누적한다. Real API E2E·Toast
a11y(FE3-05·06)는 이 Slice 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE3-00 | completed | Admin DTO·Mock·`/admin` shell·contract tests |
| FE3-01 | completed | PIN login·in-memory session·protected route·logout |
| FE3-02 | completed | 실행 기록 list·filter·pagination |
| FE3-03 | completed | run detail·status/stale badge·404 shell |
| FE3-04 | completed | manual run confirm·duplicate guard·list refetch |

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

## 설계 결정

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| Session storage | in-memory module state | W4-G0 PIN·token 영구 localStorage 금지 |
| Protected routes | `AdminProtectedRoute` + login redirect state | `/admin/login` 제외 |
| List fetch | React Query `useCollectionRunsQuery` | 기존 Policy list 패턴 |
| Manual trigger | running item 존재 시 disable | Backend concurrent run guard UX |

## 주요 변경 파일

- `frontend/src/utils/adminSessionStorage.ts`
- `frontend/src/hooks/useAdminSession.ts`
- `frontend/src/hooks/useCollectionRunsQuery.ts`
- `frontend/src/components/admin/*`
- `frontend/src/pages/admin/AdminLoginPage.tsx`
- `frontend/src/pages/admin/CollectionRunsPage.tsx`
- `frontend/src/pages/admin/CollectionRunDetailPage.tsx`
- `frontend/src/layouts/AdminShellLayout.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles/theme.css`
- `frontend/tests/adminSessionStorage.test.ts`
- `frontend/tests/adminLoginPresentation.test.ts`
- `frontend/tests/collectionRunDisplay.test.ts`

## 검증 결과

```text
cd frontend && npm test   — passed (144 unit tests, FE3-01~04 helpers 포함)
cd frontend && npm run lint — passed
cd frontend && npm run build — passed
python3 scripts/validate_docs.py — passed
```

Browser·Playwright admin flow·Real API smoke는 FE3-05 범위이며 본 Slice에서
실행하지 않았다. 로컬 `:8000` admin path 404 상태는 FE3-00 기록과 동일.

## 남은 작업

- FE3-05: Real API·Browser E2E·`BE-ADMIN-RUN-HISTORY` Frontend 인계
- FE3-06: Admin Toast·a11y (W4-F5·F8)
- Backend admin Forest merge 후 Real API smoke

## 관련 문서

- [CollectionRun Admin UI 계획](../../develop_plan/frontend/03_collection_run_admin_ui.md)
- [Backend Admin Access Control](../../develop_plan/backend/04_admin_access_control.md)
- [Backend CollectionRun Admin API](../../develop_plan/backend/05_collection_run_admin_api.md)

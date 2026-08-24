# Frontend Admin Observability UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11 (FE8-05 Browser E2E: 2026-08-12, FE8-06 Toast·a11y: 2026-08-12)
- 담당 영역: Frontend
- 상태: completed
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [Admin Observability UI Forest 개발 계획](../../develop_plan/frontend/08_admin_observability_ui.md)
- 현재 Slice: FE8-06 completed (Forest 완료)

## 목적

관리자 Policy 데이터·구조화 file log UI Forest(FE8)의 Mock-first read-only
표·상세·log 조회·maintenance confirm UI(FE8-01~04)와 Browser E2E(FE8-05)·
Toast·a11y(FE8-06)를 Integration 09 proposal 계약에 맞춰 구현·검증한다.

## Forest 범위

이 기록은 Frontend 08 Slice 구현·검증 결과를 누적한다. 최초 구현은 W4-G0
proposal이었고, `2026-08-14` DTL4-5에서 현재 Backend OpenAPI 기준으로
TypeScript·Mock·소비 테스트를 정렬했다. Real API golden E2E는 AO5에 남아 있다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE8-00 | completed | Policy·log DTO·Mock handlers·contract tests |
| FE8-01 | completed | AdminPolicyDataPage table·filter·sort·column toggle |
| FE8-02 | completed | AdminPolicyRowDetail drawer |
| FE8-03 | completed | AdminLogsPage·event filter·refresh |
| FE8-04 | completed | AdminLogMaintenanceActions rotate·archive delete confirm |
| FE8-05 | completed | Playwright Browser E2E·admin auth flow |
| FE8-06 | completed | Admin data/log Toast·a11y Browser E2E |

## 구현 내용

### FE8-00 — Admin data·log DTO·Mock

- `frontend/src/types/adminPolicyData.ts`
  - `GET /api/v1/admin/policies` list·detail (W4-G0 proposal)
  - `AdminPolicyListItemDto` table subset vs `AdminPolicyDetailDto` (= `PolicyDto`)
  - allowlist `sort_by`·filter·`page`/`size`/`pages` envelope
- `frontend/src/types/adminLog.ts`
  - `GET /api/v1/admin/log-files`, `.../events`, `DELETE .../{file_id}`,
    `POST .../rotate-current` (proposal)
  - safe log event fields (`level`, `component`, `event`, correlation ids,
    `error_type` only)
  - `AdminObservabilityErrorBody` (`detail` string)
- `frontend/src/mocks/adminObservabilityFixtures.ts`
  - active·archive log files, correlated log events
- `frontend/src/mocks/adminObservabilityHandlers.ts`
  - policy list/detail, log file/event list, archive delete (409 on active),
    rotate-current mock
- `frontend/src/mocks/adminObservabilityContract.ts`
  - pagination envelope·forbidden field assertions
- `frontend/tests/adminObservability.contract.test.ts`

### FE8-01~02 — Policy data table·row detail

- `frontend/src/api/adminPolicyData.ts` — Mock-first list/detail client
- `frontend/src/hooks/useAdminObservabilityQuery.ts` — React Query hooks
- `frontend/src/utils/adminPolicyTableColumns.ts` — column defs·sort·cell format
- `frontend/src/components/admin/AdminPolicyDataFilters.tsx`
- `frontend/src/components/admin/AdminPolicyDataTable.tsx` (+ column toggle)
- `frontend/src/components/admin/AdminPolicyRowDetail.tsx` — approved fields only
- `frontend/src/pages/admin/AdminPolicyDataPage.tsx`
- `/admin/policies` route·AdminShell nav 항목 추가

### FE8-03~04 — Log file·event UI·maintenance

- `frontend/src/api/adminLog.ts` — file/event list·archive delete·rotate client
- `frontend/src/utils/adminLogMaintenance.ts` — typed confirm validation
- `frontend/src/components/admin/AdminLogEventFilters.tsx`
- `frontend/src/components/admin/AdminLogEventTable.tsx` (+ event detail panel)
- `frontend/src/components/admin/AdminLogMaintenanceActions.tsx`
  - rotate confirm dialog, archive delete typed `file_id` confirm
  - active file delete UI 없음, duplicate submit guard
- `frontend/src/pages/admin/AdminLogsPage.tsx`
- `/admin/logs` route·AdminShell nav 항목 추가

### FE8-05 — Real API·Browser E2E (Playwright)

- `frontend/e2e/admin-observability-ui.spec.ts`
  - Mock-first 12 scenarios: protected `/admin/policies`·`/admin/logs` redirect,
    PIN login·policy table list·sort·partial filter, row detail drawer open·close·
    Escape, log file summary·event filter·detail panel(safe error_type·no stack trace),
    explicit refresh, rotate confirm, archive typed delete, admin nav cross-route,
    mobile viewport
  - Real API golden: `VITE_USE_MOCK=false` 환경에서만 실행(skip)
- Policy drawer 404·active log HTTP 409 delete는 Browser UI unreachable —
  `adminObservability.contract.test.ts`로 검증.
- Backend Integration 09 AO1~AO3 미merge — Real API golden은 table·log shell만 검증.

### FE8-06 — Admin data/log Toast·a11y

- `AdminPolicyDataPage`·`AdminLogsPage` — FE3-06 `ApiErrorToast` wiring
  (401 login redirect·5xx retryable·422 Toast), list 5xx 시 cached response 유지
- `AdminLogMaintenanceActions` — 409/5xx Toast·dialog 유지·Escape dismiss·
  archive file_id live announcement·resolved archive select
- Mock audit hooks: policy filter `MOCK_503`/`MOCK_401`/`MOCK_422`, log filter
  `component=MOCK_503`, archive `log-file-archive-mock409`→409
- `AdminPolicyColumnToggle` popover·Escape, table sort `aria-label`·caption
  `aria-describedby`, refresh focus return
- `frontend/e2e/admin-observability-toast-a11y.spec.ts` — 7 Mock-first scenarios

### DTL4-5 계약 정렬 (`2026-08-14`)

| 영역 | 과거 FE8 proposal | DTL4-5 확정 소비 |
| --- | --- | --- |
| Policy admin API | `/api/v1/admin/policies` | 같은 경로, `limit`·`order`, Backend allowlist sort |
| Log admin API | `/api/v1/admin/log-files` | `/api/v1/admin/logs/files`·`/events`·`/archives/{file_id}`·`/rotate-current` |
| List envelope | `page`·`size`·`pages`·`total` | Policy `{items,total,page,limit}`, log files `{files}`, events `{events,total,page,limit}` |
| Error body | protected route `detail` | Backend `detail`, active delete `400` |

Mock fixture와 공개 DTO 소비 테스트 및 production build는 통과했다. Real API
Browser E2E는 Integration 09 AO5에서 재검증한다.

DTL4-5 재검증에서 관리자 observability Playwright는 **19 passed, 1 skipped**
(Real API 조건부 golden)였다.

## 설계 결정

- Admin policy projection은 공개 `PolicyDto` allowlist를 재사용하고
  `provenance`·Raw 필드는 DTO·Mock 모두에서 제외.
- Log list item은 `file_id`(opaque)와 basename `filename`만 노출; server path
  필드는 contract test에서 금지.
- Log event list item은 `message`를 detail 전용으로 두고 list 응답에서는 제외
  (Mock handler가 strip). UI detail panel은 Mock fixture에서 message를 조회.
- Active log file direct delete는 Mock에서 HTTP 409로 거부(Integration 09
  rotate-first UX 선행).
- 401은 FE3-01과 동일하게 `clearAdminSession()` + login redirect.
- list 5xx Toast 시 ErrorState와 global Toast 중복 금지; cached list ref로
  이전 table 유지.

### 버그 수정 — Policy row detail drawer 미표시 (2026-08-12)

- **1차 원인**: `AdminPolicyDataPage` layout grid 안에서 React Fragment(`<>`)가 table·
  pagination을 별도 grid item으로 분리해 pagination이 drawer 열(2열)을 점유함.
  drawer는 2행 1열에 렌더되어 화면 밖/아래로 밀려 클릭해도 보이지 않음.
- **1차 수정**: table+pagination을 `admin-policy-data-page__main` wrapper로 묶음.
- **재발 원인**: grid 2열 sidebar 방식은 drawer가 레이아웃 흐름에 묶여 z-index·
  fixed overlay로 슬라이드되지 않음.
- **최종 수정 (FE8-02)**: `AdminPolicyDataPage`에 `isDrawerOpen` 상태를 두고,
  `AdminPolicyRowDetail`을 layout grid 밖 fixed overlay drawer로 렌더.
  `isOpen`·`onClose`·`policy` prop 전달, backdrop·Escape·닫기 버튼으로 닫기.
  `theme.css`에 `admin-policy-row-detail-drawer` slide-in(`translateX`)·
  `z-index: 1100` 스타일 추가. row 클릭·`상세보기` 버튼에
  `stopPropagation` 유지.

## 주요 변경 파일

- `frontend/src/api/adminPolicyData.ts`
- `frontend/src/api/adminLog.ts`
- `frontend/src/api/adminRequest.ts`
- `frontend/src/hooks/useAdminObservabilityQuery.ts`
- `frontend/src/utils/adminPolicyTableColumns.ts`
- `frontend/src/utils/adminLogMaintenance.ts`
- `frontend/src/components/admin/AdminPolicyData*.tsx`
- `frontend/src/components/admin/AdminPolicyRowDetail.tsx`
- `frontend/src/components/admin/AdminLogEvent*.tsx`
- `frontend/src/components/admin/AdminLogMaintenanceActions.tsx`
- `frontend/src/pages/admin/AdminPolicyDataPage.tsx`
- `frontend/src/pages/admin/AdminLogsPage.tsx`
- `frontend/src/mocks/adminObservabilityFixtures.ts`
- `frontend/src/mocks/adminObservabilityHandlers.ts`
- `frontend/src/App.tsx`
- `frontend/src/layouts/AdminShellLayout.tsx`
- `frontend/src/styles/theme.css`
- `frontend/tests/adminPolicyTableColumns.test.ts`
- `frontend/tests/adminLogMaintenance.test.ts`
- `frontend/tests/adminObservability.contract.test.ts`
- `frontend/tsconfig.test.json`
- `frontend/e2e/admin-observability-ui.spec.ts`
- `frontend/e2e/admin-observability-toast-a11y.spec.ts`

## 검증 결과

```text
cd frontend && npm test   — 168 passed
cd frontend && npx eslint src/pages/admin/AdminPolicyDataPage.tsx src/pages/admin/AdminLogsPage.tsx src/components/admin/AdminLogMaintenanceActions.tsx src/components/admin/AdminPolicyDataTable.tsx — passed
cd frontend && npm run test:e2e -- e2e/admin-observability-toast-a11y.spec.ts — 7 passed
cd frontend && npm run test:e2e -- e2e/admin-observability-ui.spec.ts — 12 passed, 1 skipped (Real API)
python3 scripts/validate_docs.py — passed
```

Browser·Playwright E2E는 FE8-05·FE8-06에서 실행 완료.
전체 `npm run lint`는 `AdminLoginPage.tsx` 기존 `react-hooks/purity` 1건으로
실패(FE3-06 선행 코드, 본 Slice 범위 밖).

## 남은 작업

- W4-G0 Gate 승인 후 `docs/api/admin_observability.md`(또는 동등 API 문서) 추가
- Backend Integration 09 merge 후 Real API admin observability golden 재검증
- FE9-02 Integration Regression matrix A cross-Forest Toast dedupe 회귀

## 관련 문서

- [Integration 09 Admin Data and Log Console](../../develop_plan/integration/09_admin_data_log_console.md)
- [Frontend 03 CollectionRun Admin UI](../../develop_plan/frontend/03_collection_run_admin_ui.md)

# Frontend Admin Observability UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [Admin Observability UI Forest 개발 계획](../../develop_plan/frontend/08_admin_observability_ui.md)
- 현재 Slice: FE8-01~04 completed

## 목적

관리자 Policy 데이터·구조화 file log UI Forest(FE8)의 Mock-first read-only
표·상세·log 조회·maintenance confirm UI(FE8-01~04)를 Integration 09 proposal
계약에 맞춰 구현한다.

## Forest 범위

이 기록은 Frontend 08 Slice 구현·검증 결과를 누적한다. W4-G0 승인 전
admin policy·log API path·DTO는 proposal이며 Real API·Browser E2E(FE8-05)는
Backend merge 후 별도 Slice에서 진행한다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE8-00 | completed | Policy·log DTO·Mock handlers·contract tests |
| FE8-01 | completed | AdminPolicyDataPage table·filter·sort·column toggle |
| FE8-02 | completed | AdminPolicyRowDetail drawer |
| FE8-03 | completed | AdminLogsPage·event filter·refresh |
| FE8-04 | completed | AdminLogMaintenanceActions rotate·archive delete confirm |

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

### 계약 정렬 메모 (Backend 미구현)

| 영역 | FE8 proposal | Backend 상태 |
| --- | --- | --- |
| Policy admin API | `/api/v1/admin/policies` | `feature/backend/admin-observability` 브랜치 없음 |
| Log admin API | `/api/v1/admin/log-files` | 동일 — AO1~AO3 미merge |
| List envelope | `page`·`size`·`pages`·`total` | Backend 05 CollectionRun 패턴 따름 |
| Error body | protected route `detail` | Backend 04·FE3와 동일 |

Real API 연동·Browser E2E는 Integration 09 Backend merge 후 FE8-05에서 재검증.

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
- FE8-06 Toast·a11y subset은 본 Slice 범위 밖(후속 Slice).

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
- `frontend/src/App.tsx`
- `frontend/src/layouts/AdminShellLayout.tsx`
- `frontend/src/styles/theme.css`
- `frontend/tests/adminPolicyTableColumns.test.ts`
- `frontend/tests/adminLogMaintenance.test.ts`
- `frontend/tsconfig.test.json`

## 검증 결과

- `npm run test` (frontend): **150 passed** (admin observability·policy table·log maintenance 포함)
- `npm run lint`: passed
- `npm run build`: passed
- `python3 scripts/validate_docs.py`: passed
- `npm run test:e2e`: **미실행** (FE8-05 범위)

## 남은 작업

- FE8-05: Real API·Browser E2E (`feature/backend/admin-observability` merge 후)
- FE8-06: Admin data/log Toast·a11y subset
- W4-G0 Gate 승인 후 `docs/api/admin_observability.md`(또는 동등 API 문서) 추가

## 관련 문서

- [Integration 09 Admin Data and Log Console](../../develop_plan/integration/09_admin_data_log_console.md)
- [Frontend 03 CollectionRun Admin UI](../../develop_plan/frontend/03_collection_run_admin_ui.md)

# Frontend Admin Observability UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [Admin Observability UI Forest 개발 계획](../../develop_plan/frontend/08_admin_observability_ui.md)
- 현재 Slice: FE8-00 completed

## 목적

관리자 Policy 데이터·구조화 file log UI Forest(FE8)의 TypeScript DTO·Mock
handler 기준선(FE8-00)을 Integration 09 W4-G0 proposal에 맞춰 구현한다.

## Forest 범위

이 기록은 Frontend 08 Slice 구현·검증 결과를 누적한다. W4-G0 승인 전
admin policy·log API path·DTO는 proposal이며 표·로그 UI(FE8-01+)는 이
Slice에서 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE8-00 | completed | Policy·log DTO·Mock handlers·contract tests |
| FE8-01 | pending | AdminPolicyDataPage table |
| FE8-03 | pending | AdminLogsPage·event filter |

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

### 계약 정렬 메모 (Backend 미구현)

| 영역 | FE8-00 proposal | Backend 상태 |
| --- | --- | --- |
| Policy admin API | `/api/v1/admin/policies` | `feature/backend/admin-observability` 브랜치 없음 |
| Log admin API | `/api/v1/admin/log-files` | 동일 — AO1~AO3 미merge |
| List envelope | `page`·`size`·`pages`·`total` | Backend 05 CollectionRun 패턴 따름 |
| Error body | protected route `detail` | Backend 04·FE3와 동일 |

Real API 연동은 Integration 09 Backend merge 후 FE8-05에서 재검증.

## 설계 결정

- Admin policy projection은 공개 `PolicyDto` allowlist를 재사용하고
  `provenance`·Raw 필드는 DTO·Mock 모두에서 제외.
- Log list item은 `file_id`(opaque)와 basename `filename`만 노출; server path
  필드는 contract test에서 금지.
- Log event list item은 `message`를 detail 전용으로 두고 list 응답에서는 제외
  (Mock handler가 strip).
- Active log file direct delete는 Mock에서 HTTP 409로 거부(Integration 09
  rotate-first UX 선행).

## 주요 변경 파일

- `frontend/src/types/adminPolicyData.ts`
- `frontend/src/types/adminLog.ts`
- `frontend/src/mocks/adminObservabilityFixtures.ts`
- `frontend/src/mocks/adminObservabilityHandlers.ts`
- `frontend/src/mocks/adminObservabilityContract.ts`
- `frontend/tests/adminObservability.contract.test.ts`
- `frontend/tsconfig.test.json`

## 검증 결과

- `npm run test` (frontend): **98 passed** (admin observability contract 10건 포함)
- `npm run lint`: passed
- `npm run build`: passed
- `python scripts/validate_docs.py`: passed

## 남은 작업

- FE8-01: `AdminPolicyDataPage`·table UI
- FE8-03: log file·event UI
- FE8-05: Real API·Browser E2E (`feature/backend/admin-observability` merge 후)
- W4-G0 Gate 승인 후 `docs/api/admin_observability.md`(또는 동등 API 문서) 추가

## 관련 문서

- [Integration 09 Admin Data and Log Console](../../develop_plan/integration/09_admin_data_log_console.md)
- [Frontend 03 CollectionRun Admin UI](../../develop_plan/frontend/03_collection_run_admin_ui.md)

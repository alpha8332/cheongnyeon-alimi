# Frontend Admin Observability UI Forest 개발 계획

## 계획 정보

- 번호: Frontend 08
- 담당 영역: Frontend
- 상태: draft
- 계획일: `2026-08-11`
- 대상 Release: `v0.5.0`
- 공통 시작 커밋: `22118b8e618c3b15464865be3113157888197a02`
- 4주차 대응: `W4-FO1`, `W4-FL1`, Critical Path A (`week_04_v0_5_0.md`)
- 선행 Forest:
  [Backend 04 Admin Access Control](../backend/04_admin_access_control.md),
  [Integration 09 Admin Data and Log Console](../integration/09_admin_data_log_console.md),
  [Frontend 03 CollectionRun Admin UI](03_collection_run_admin_ui.md) (FE3-01 PIN·session 공유)
- 후속 Forest: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/frontend/admin-observability`
- 현재 Slice: FE8-00 draft (계획 수립)

## 목적

인증된 관리자가 승인 Policy projection을 CSV형 표로 조회하고, 구조화 file
log·event를 필터·상세·새로고침으로 확인하며, 회전 archive 삭제를 확인
절차와 함께 요청할 수 있는 UI를 제공한다. arbitrary SQL·데이터 수정 UI는
포함하지 않는다.

## 범위

- Integration 09 admin policy data·log DTO TypeScript 소비
- 정책 데이터 표: pagination·allowlist filter·sort·column show/hide
- row 상세(identity·Source·기간·품질·수집 시각 등 승인 컬럼만)
- 로그 파일 목록·event filter·상세·명시적 새로고침
- archive 삭제·현재 로그 rotate 정리 확인 dialog
- FE3-01과 공유하는 PIN session·protected `/admin/*` route
- loading·empty·error·401·403·404
- Mock-first → actual API·Browser E2E

## 범위 밖

- CollectionRun 실행 이력·수동 실행 (Frontend 03 FE3-03~05)
- Backend Repository·log handler·삭제 API 구현 (Integration 09 AO1~AO3)
- WebSocket 실시간 tail
- Raw payload·credential·SQL parameter 표시
- 정책 데이터 수정·삭제

## 선행 조건

- Backend 04 PIN session·token 보관 경계 (W4-G0)
- Integration 09 AO0 승인 Policy projection column allowlist
- Frontend 03 FE3-01 로그인 UI 또는 동일 session module 재사용 합의

## 공통 API 오류 Toast·접근성 (W4-F5·W4-F8)

관리자 데이터·로그(FE8)는 FE3·FE6와 동일 Toast contract를 사용한다.
전체 회귀는 [Frontend 09 FE9-02](09_integration_and_regression.md).

### API 오류 Toast

| HTTP | UX | 재시도 | 비고 |
| --- | --- | --- | --- |
| `401` | login redirect | no | FE3-01 session |
| `403` | 권한 없음 Toast | no | |
| `404` | row/file not found inline | no | |
| `409` | delete conflict Toast | no | archive delete |
| `422` | filter validation Toast | no | allowlist filter |
| `5xx` | retryable Toast | yes | list refresh action |

- log event detail: safe `error_type` only; stack·parameter 비노출.
- delete·rotate confirm 실패 시 Toast + dialog 유지.

### 키보드·모바일 접근성 (a11y)

- data table: sortable header keyboard, column toggle menu Esc dismiss.
- log table: filter form label, refresh button focus return.
- delete confirm: typed confirm input labeled; screen reader announces target file id.
- 모바일: table card fallback or scroll with `aria-describedby` caption.

## 공통 설계 원칙

- DTO에 없는 table·column·internal id를 UI type에 추가하지 않는다.
- 삭제·rotate는 이중 확인; 성공·실패는 Backend safe message만 표시.
- token·PIN을 URL·console·영구 localStorage에 남기지 않는다.
- 대량 row를 client-side 전체 load하지 않고 server pagination만 사용.

## Slice 계획

- DTO에 없는 table·column·internal id를 UI type에 추가하지 않는다.
- 삭제·rotate는 이중 확인; 성공·실패는 Backend safe message만 표시.
- token·PIN을 URL·console·영구 localStorage에 남기지 않는다.
- 대량 row를 client-side 전체 load하지 않고 server pagination만 사용.

## Slice 계획

4주차 `W4-FO1`·`W4-FL1`을 FE8-xx로 분해한다.

| 4주차 | FE8 Slice | 책임 |
| --- | --- | --- |
| FO1 기반 | FE8-00 | Policy·log DTO·Mock |
| FO1 | FE8-01 | Policy data table |
| FO1 | FE8-02 | Row detail |
| FL1 | FE8-03 | Log file·event list |
| FL1 | FE8-04 | Delete·rotate confirm UI |
| E2E | FE8-05 | Real API·auth·Browser |
| W4-F5·F8 | FE8-06 | Admin data/log Toast·a11y |

---

### FE8-00 — Admin data·log DTO·Mock — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | Policy admin list/detail·log file/event DTO와 Mock handlers |
| **예상 변경 파일** | `types/adminPolicyData.ts`, `types/adminLog.ts`, `mocks/adminObservabilityHandlers.ts` |
| **선행** | Integration 09 AO0, W4-G0 column allowlist |
| **검증** | contract test |
| **완료 기준** | pagination envelope·safe error DTO |

---

### FE8-01 — 정책 데이터 표 — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | CSV형 table·server pagination·allowlist filter·sort |
| **예상 변경 파일** | `AdminPolicyDataPage.tsx`, `AdminPolicyDataTable.tsx` |
| **선행** | FE8-00, FE3-01 (session) |
| **세부 작업** | column toggle; long cell expand |
| **검증** | Mock list; Browser |
| **완료 기준** | arbitrary column·SQL UI 없음 |

---

### FE8-02 — Policy row 상세 — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | 단일 row drill-down drawer 또는 `/admin/policies/:id` |
| **예상 변경 파일** | `AdminPolicyRowDetail.tsx` |
| **선행** | FE8-01 |
| **검증** | Mock detail 404 |
| **완료 기준** | 승인 projection field만 표시 |

---

### FE8-03 — 로그 파일·event UI — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | log file list·event filter(level·component·run id·time)·detail |
| **예상 변경 파일** | `AdminLogsPage.tsx`, `AdminLogEventTable.tsx` |
| **선행** | FE8-00, FE3-01 |
| **세부 작업** | explicit refresh; bounded page size |
| **검증** | Mock log fixtures |
| **완료 기준** | stack trace·secret field UI 비노출 |

---

### FE8-04 — Archive 삭제·rotate 확인 — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | archive delete·current log rotate cleanup confirm dialog |
| **예상 변경 파일** | `AdminLogMaintenanceActions.tsx` |
| **선행** | FE8-03, Integration 09 AO3 API |
| **세부 작업** | typed confirm; duplicate submit guard |
| **검증** | Mock 202/409; Browser |
| **완료 기준** | 활성 file 직접 delete UI 없음 |

---

### FE8-05 — Real API·Browser E2E — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | admin auth → data table → log view actual path |
| **예상 변경 파일** | API client, Playwright admin spec |
| **선행** | FE8-01~04, Integration 09 Backend merged |
| **검증** | `npm run test:e2e`; W4-I1 admin E2E checklist |
| **완료 기준** | Integration 09 Frontend 완료 기준 충족 |

---

### FE8-06 — Admin data/log Toast·접근성 — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | FE8 data table·log UI에 Toast·a11y 명세 적용 |
| **예상 변경 파일** | shared Toast, table a11y, delete dialog a11y |
| **선행** | FE8-01~04 |
| **세부 작업** | 본 문서 「공통 API 오류 Toast·접근성」표 준수 |
| **검증** | Browser 401/409/5xx; keyboard table navigation |
| **완료 기준** | W4-F5·F8 admin observability subset; [FE9-02](09_integration_and_regression.md) matrix A |

## 검증 계획

```powershell
Set-Location frontend
npm run test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
python scripts/validate_docs.py
```

## Forest 완료 기준

- 읽기 전용 policy 표·row 상세·log 조회·archive 삭제 confirm 제공
- FE3-01 session과 401·403 처리 일치
- 민감·internal field Browser 비노출
- W4-FO1·W4-FL1 요구 Browser 충족

## 위험과 미확정 사항

- PIN session module을 Frontend 03과 Frontend 08이 공유할지 duplicate할지
  W4-G0에서 확정 필요.
- Log UI polling 주기 vs manual refresh only — Integration 09 범위 밖 WebSocket
  미사용.
- Windows active log file delete 불가 → rotate-first UX 필수.

## 관련 문서

- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [Integration 09 Admin Data and Log](../integration/09_admin_data_log_console.md)
- [Frontend 03 CollectionRun Admin](03_collection_run_admin_ui.md)
- [Frontend 09 Integration and Regression](09_integration_and_regression.md)
- [Backend 04 Admin Access](../backend/04_admin_access_control.md)

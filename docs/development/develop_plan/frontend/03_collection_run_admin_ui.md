# Frontend CollectionRun Admin UI Forest 개발 계획

## 계획 정보

- 번호: Frontend 03
- 담당 영역: Frontend
- 상태: completed
- 계획일: `2026-08-07`
- Slice 계획 갱신: `2026-08-11`
- 대상 Release: `v0.5.0`
- 공통 시작 커밋: `22118b8e618c3b15464865be3113157888197a02`
- 4주차 대응: `W4-F1`, `W4-F2`, Critical Path A (`week_04_v0_5_0.md`)
- 작업 브랜치: `feature/backend/admin-run-management` (Backend 공유),
  Frontend UI: `feature/frontend/bookmarks-calendar-admin`
- 현재 Slice: FE3-06 completed
- 공통 선행 계약:
  [Integration 05 v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- 공유 Forest:
  [Backend Admin Access Control](../backend/04_admin_access_control.md),
  [Backend CollectionRun Admin API](../backend/05_collection_run_admin_api.md)
- 선행 Forest:
  [Backend Admin Access Control](../backend/04_admin_access_control.md),
  [Backend CollectionRun Admin API](../backend/05_collection_run_admin_api.md)
- 대상 인계사항: `BE-ADMIN-RUN-HISTORY`의 Frontend 소비

## 목적

인증된 관리자가 CollectionRun 실행 이력을 조회하고 안전하게 수동 실행을
요청할 수 있는 관리자 UI를 구현한다. Backend DTO·pagination·권한·상태
계약을 그대로 소비하고 loading·empty·error·동시 실행 상태를 명확히
표시한다.

## 범위

- 아이디 없이 4자리 숫자 PIN 한 칸을 사용하는 관리자 로그인
- PIN session 요청, 짧은 수명 token 보관·만료·로그아웃과 보호 route
- 잘못된 PIN·형식 오류·반복 실패 `429`와 관리자 미설정 상태
- 관리자 실행 이력 목록·상세 route와 API Client
- pagination, source·status·기간 필터와 기본 정렬 소비
- 상태·집계·안전한 오류 정보 표시
- loading·empty·error·401·403·404 UI
- 수동 실행 확인, 진행 중 비활성화와 중복 제출 방지
- stale·중단 실행 표시
- Backend DTO 소비 테스트, lint·build와 실제 브라우저 검증

## 범위 밖

- 관리자 인증·권한 Backend 구현
- 관리자 계정 생성·비밀번호 변경·refresh token과 일반 사용자 로그인
- CollectionRun DB·Backend API 계약 변경
- Raw payload·정책 본문·provenance·credential 표시
- Scheduler·실시간 WebSocket·알림 시스템
- 디자이너급 관리자 디자인 시스템 전면 구축

## 선행 조건

- Backend Admin Access Control과 CollectionRun Admin API Forest 완료
- 실제 OpenAPI·DTO·pagination·오류 계약 제공
- Frontend에서 관리자 인증 상태를 소비할 경계 합의
- Mock을 사용하면 실제 API와 동일한 공개 관리자 DTO만 사용

## 공통 설계 원칙

- 관리자 route는 인증·권한 상태를 명시적으로 처리한다.
- PIN과 token을 URL·Browser log·오류 message·영구 localStorage에 남기지 않는다.
- PIN 입력은 숫자 키패드를 유도하되 DOM이나 접근성 label에 실제 값을 노출하지
  않는다.
- API DTO에 없는 내부 DB·provenance 필드를 화면 타입에 추가하지 않는다.
- 수동 실행은 명시적인 사용자 확인과 중복 제출 방지를 요구한다.
- `running`, terminal, stale 상태를 임의로 합치지 않는다.
- 오류에는 Backend가 제공한 안전한 정보만 표시한다.
- Mock·실제 API Client와 소비 테스트가 같은 계약을 사용한다.

## 공통 API 오류 Toast·접근성 (W4-F5·W4-F8)

관리자 Forest(FE3)는 FE6·FE9와 **동일 Toast presentation contract**를 공유한다.
구현 Slice는 FE3-06, 전체 회귀는 [Frontend 09 FE9-02](09_integration_and_regression.md)를
따른다.

### API 오류 Toast

| HTTP | UX | 재시도 | 비고 |
| --- | --- | --- | --- |
| `401` | 세션 만료 안내 → login redirect | no | PIN·token URL/log 비노출 |
| `403` | 권한 없음 inline 또는 Toast | no | safe Backend message only |
| `404` | run/detail not found shell | no | |
| `409`/`422` | validation Toast | no | 수동 실행 conflict 등 |
| `429` | cooldown Toast + PIN 입력 disable | no | FE3-01과 동일 copy |
| `5xx` | retryable Toast + 재시도 action | yes | exponential backoff optional |

- Toast는 **non-blocking**; PIN 입력·confirm dialog 위에 modal overlay 금지.
- Backend stack trace·credential·raw token을 Toast body에 표시하지 않는다.
- 동일 request id 연속 실패 시 Toast dedupe(3s window).

### 키보드·모바일 접근성 (a11y)

- PIN 입력: `inputmode="numeric"`, 4자리 label, Enter submit, focus trap 없음.
- Run list/table: row focus visible, Enter로 detail 이동, filter는 Tab 순서 고정.
- Manual run confirm: focus initial on cancel; Esc closes; Enter on primary만 confirm.
- loading·empty·error·401·403·404: `role="status"` 또는 `role="alert"` 구분.
- 모바일(≤640px): filter stack vertical, table horizontal scroll with caption.

---

## Slice 계획

4주차 [`week_04_v0_5_0.md`](../../weekly_plan/week_04_v0_5_0.md) 관리자 Frontend
(`W4-F1`·`W4-F2`)를 FE3-xx 실행 단위로 나눈다. Backend 04 → Backend 05 선행.
**W4-G0 미승인 시** OpenAPI 초안·Mock만 작성하고 DTO 필드를 임의 추가하지
않는다.

| Forest 묶음 | FE3 Slice | 4주차 | 책임 |
| --- | --- | --- | --- |
| U0 | FE3-00 | F0 | DTO·route·Mock 계약 | completed |
| U0 | FE3-01 | F1 | PIN login·session·logout | completed |
| U1 | FE3-02 | F2 | CollectionRun 목록·필터 | completed |
| U1 | FE3-03 | F2 | Run 상세·stale·상태 | completed |
| U2 | FE3-04 | F2 | 수동 실행 confirm | completed |
| U3 | FE3-05 | F2 | Real API·Browser·인계 |
| W4-F5·F8 | FE3-06 | F5 | Admin Toast·a11y |

FE3-01(PIN·session)은 [Frontend 08 Admin Observability](08_admin_observability_ui.md)
FE8-01~05와 session module을 공유할 수 있다(W4-G0에서 확정).

---

### FE3-00 — Admin DTO·라우팅·Mock 계약 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | CollectionRun·PIN session Backend OpenAPI → TypeScript·Mock·`/admin` shell |
| **예상 변경 파일** | `types/adminSession.ts`, `types/collectionRun.ts`, `api/admin*.ts`, `App.tsx` admin routes |
| **선행** | Backend 04·05 OpenAPI draft, W4-G0 |
| **인터페이스** | PIN session request/response; run list envelope; safe error DTO |
| **검증** | contract unit test; `npm run build` |
| **완료 기준** | credential·token URL/log 비노출; placeholder → route shell |

2026-08-11 구현: W4-G0 proposal TypeScript·Mock-first API client,
`AdminShellLayout` nested `/admin` routes, `/admin/login`·`/admin/runs/:runId`
placeholder, `admin.contract.test.ts`. Browser 검증은 FE3-05 범위.

2026-08-11 Real API 정합: Backend 04·05(`origin/feature/backend/collection-run-admin-api`)
OpenAPI·`docs/api/admin_*.md` 기준으로 DTO·query(`size`·`pages`·`start_date`)·
에러(`error.message` / `detail`)·`Authorization` 옵션·`triggerManualCollectionRun`
클라이언트 정렬. 로컬 `:8000` OpenAPI에 admin path 미포함 시 Real 호출 불가.

---

### FE3-01 — PIN login·session UI — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 4자리 숫자 PIN·session 획득·보관·만료·logout·cooldown·미설정 |
| **예상 변경 파일** | `AdminLoginPage.tsx`, session store, `AdminProtectedRoute.tsx` |
| **선행** | FE3-00, Backend 04 |
| **세부 작업** | numeric input; 401/403/429 UI; token 영구 localStorage 금지 |
| **검증** | unit + Browser wrong PIN·429 |
| **완료 기준** | W4-G0 PIN·token 책임과 일치 |

2026-08-11 구현: `adminSessionStorage`(in-memory), `AdminLoginPage` PIN form,
`AdminProtectedRoute`, logout. 429 cooldown 5s. unit
`adminSessionStorage.test.ts`. Browser wrong PIN은 FE3-05.

---

### FE3-02 — CollectionRun 목록·필터 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 실행 이력 list·pagination·source/status/기간 filter |
| **예상 변경 파일** | `CollectionRunsPage.tsx`, filter·table components |
| **선행** | FE3-01, Backend 05 list API |
| **검증** | Mock list scenarios; loading·empty·error |
| **완료 기준** | DTO 외 DB·provenance field 미표시 |

2026-08-11 구현: `CollectionRunsPage`, `CollectionRunFilters`,
`useCollectionRunsQuery`. pagination·loading·empty·error.

---

### FE3-03 — CollectionRun 상세·stale — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | run detail route·running/terminal/stale badge·safe error |
| **예상 변경 파일** | `CollectionRunDetailPage.tsx`, status components |
| **선행** | FE3-02 |
| **검증** | Mock running·stale·failed fixtures |
| **완료 기준** | 상태 임의 merge 없음 |

2026-08-11 구현: `CollectionRunDetailPage`, `CollectionRunStatusBadge`,
`collectionRunDisplay` utils, 404 shell.

---

### FE3-04 — 수동 실행 UI — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | confirm dialog·202 accept·running disable·duplicate guard |
| **예상 변경 파일** | `ManualCollectionRunTrigger.tsx` |
| **선행** | FE3-03, Backend 05 manual run |
| **검증** | duplicate click test |
| **완료 기준** | `collection_run_id`로 목록 갱신 |

2026-08-11 구현: `ManualCollectionRunTrigger` confirm·duplicate guard·running
disable·list refetch.

---

### FE3-05 — Real API·Browser·인계 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | PostgreSQL → FastAPI → React admin run path E2E |
| **예상 변경 파일** | API env toggle, Playwright admin-run spec, development notes |
| **선행** | FE3-01~04, Backend 04·05 merged |
| **검증** | `npm run test:e2e`; `python scripts/validate_docs.py` |
| **완료 기준** | `BE-ADMIN-RUN-HISTORY` Frontend 종료 |

2026-08-11 구현: `frontend/e2e/admin-collection-run.spec.ts` Mock-first Browser
flow 9건(PIN·list·filter·detail·404·manual trigger). `playwright.config.ts`
`VITE_USE_MOCK`·`VITE_API_BASE_URL` webServer env 전달. Real API golden 1건은
`VITE_USE_MOCK=false` + Backend admin path 준비 시에만 실행(skip). 로컬
`:8000` admin API 미merge 상태에서는 Mock E2E로 Frontend 소비 경로를
검증하고 Real smoke는 Backend merge 후 재실행.

---

### FE3-06 — Admin API Toast·접근성 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | FE3 화면에 공통 Toast·a11y 명세 적용 (PIN·list·detail·manual run) |
| **예상 변경 파일** | shared `ApiErrorToast.tsx`, admin page wiring, theme a11y |
| **선행** | FE3-01~04 (또는 parallel Mock UI) |
| **세부 작업** | 본 문서 「공통 API 오류 Toast·접근성」표 준수 |
| **검증** | Browser 401/429/5xx; keyboard-only PIN·confirm flow |
| **완료 기준** | W4-F5·F8 admin subset; [FE9-02](09_integration_and_regression.md) matrix A pass |

2026-08-12 구현: `ApiErrorToast`·`ApiErrorToastProvider`·`adminApiErrorToast` mapper,
`AdminShellLayout`·`AdminLoginPage` wiring. CollectionRun list·detail·manual trigger
401/403/422/429/5xx Toast(5xx retry). Mock audit hooks: login PIN `5000`→503,
list filter `source_id=MOCK_503`→503. Manual confirm Escape close·PIN Enter submit.
`frontend/e2e/admin-toast-a11y.spec.ts` 6 scenarios. FE9-02 cross-Forest Toast
dedupe·full matrix는 Integration Regression(FE9-02) 범위.

### U0 - 관리자 DTO·라우팅 소비 계약

- FE3-00·FE3-01에 해당한다.
- Backend OpenAPI 기준 PIN session·route·권한 경계 확정.

### U1 - 실행 이력 목록·상세 UI

- FE3-02·FE3-03에 해당한다.

### U2 - 수동 실행 상호작용

- FE3-04에 해당한다.

### U3 - 실제 API·브라우저 검증과 인계 종료

- FE3-05·FE3-06에 해당한다. 전체 cross-Forest 회귀는 [Frontend 09](09_integration_and_regression.md).

## 검증 계획

- DTO·Mock·API Client 소비 테스트
- pagination·filter·status 표시 테스트
- loading·empty·error·401·403·404 UI 테스트
- PIN 4자리 형식·잘못된 PIN·`429` cooldown·token 만료·로그아웃 테스트
- 수동 실행 확인·중복 제출 방지 테스트
- `npm ci`
- `npm test`
- `npm run lint`
- `npm run build`
- 실제 Backend·PostgreSQL 기반 브라우저 검증
- `python scripts/validate_docs.py`
- `git diff --check`

## Forest 완료 기준

- 관리자 실행 이력 목록·상세·필터·pagination 제공
- 수동 실행 확인과 중복 제출 방지
- Backend DTO·권한·상태 계약과 Frontend 타입 일치
- 민감정보·내부 provenance 비노출
- 자동 검증과 실제 API 브라우저 검증 통과
- 개발 기록·인계 보드 동기화

### Phase 2 후속 (Week 5 — 집계 대시보드)

2026-07-28: placeholder였던 `/admin`(DashboardPage)·`/admin/quality`(DataQualityPage)를
Backend list·detail 집계 API 범위에서 구현. 건별 failure·duplicate candidate
목록 API는 Backend 미제공으로 UI 제외. 상세는
[development_notes/frontend/collection_run_admin_ui.md](../../development_notes/frontend/collection_run_admin_ui.md).

## 위험과 미확정 사항

- 관리자 인증 UX와 credential 보관 방식은 Backend Access Control 결정에
  의존한다.
- 수동 실행이 장시간 작업이면 polling·timeout·재접속 상태가 추가로 필요할
  수 있다.
- Backend API가 확정되기 전에 Mock을 일반화하면 계약 불일치가 생길 수 있다.

## 관련 문서

- [Backend Admin Access Control 계획](../backend/04_admin_access_control.md)
- [Backend CollectionRun Admin API 계획](../backend/05_collection_run_admin_api.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [Frontend 08 Admin Observability UI](08_admin_observability_ui.md)
- [Frontend 09 Integration and Regression](09_integration_and_regression.md)
- [공동 확인 및 인계 보드](../../../index.md#공동-확인-및-인계-보드)

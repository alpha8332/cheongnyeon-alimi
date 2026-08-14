# Frontend Integration Fix and Regression Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-12 (FE9-01 Frontend-only triage·수정; FE9-02 Mock-first 회귀)
- 담당 영역: Frontend
- 상태: completed
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [Integration Fix and Regression Forest 개발 계획](../../develop_plan/frontend/09_integration_and_regression.md)
- 현재 Slice: FE9-02 completed (Mock-first, W4-G4 `CONDITIONAL`)

## 목적

W4-F9 cross-Forest 연동 결함을 Forest·Slice 단위로 triage·수정하고, Backend
blocker는 W4-G4 판정 근거로 분류한다. W4-F10 전체 회귀(FE9-02)는 Mock-first
E2E 매트릭스로 closure.

## Forest 범위

Frontend 09 조율 Forest — owner Forest(FE3·5·6·7·8) 코드의 cross-cutting 수정과
blocker triage만 담당한다. Backend·Integration Forest 버그 수정은 범위 밖.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE9-01 | completed (CONDITIONAL) | Frontend-only W4-F9 수정·blocker triage |
| FE9-02 | completed (CONDITIONAL) | W4-F10 Mock-first 회귀 매트릭스·W4-I3 golden (Mock) |

## 구현 내용

### FE9-01 — actual 연동 통합 버그 수정 (Frontend-only)

**Baseline (작업 전):** `npm test` 168 passed, `npm run build` pass,
`npm run test:e2e` 87 passed·6 skipped, `npm run lint` 1 error
(`AdminLoginPage` `Date.now()` purity).

**W4-F9 triage:**

| ID | 범주 | Forest | 재현/판정 | 조치 |
| --- | --- | --- | --- | --- |
| F9-01 | 인증·세션 | FE3, FE8 | Mock 401→login redirect 중복 패턴 | `useAdminUnauthorizedRedirect` 추출 |
| F9-02 | 인증·세션 | FE3 | AdminLoginPage eslint purity | cooldown base를 `nowMs` state 사용 |
| F9-03 | localStorage | FE5 | corrupt reset 후 UI 무안내 | session notice + `UserLocalStorageRecoveryBanner` |
| F9-04 | 추천·조건 | FE5, FE6 | conditions localStorage vs API | **no defect** — `useSavedConditions` 공유 |
| F9-05 | 자격요건 | FE7 | Real API DTO drift | **BLOCKED** — Backend `eligibility_summary` 미merge |
| F9-06 | admin observability | FE8 | Real API policy·log | **BLOCKED** — Integration 09 AO1~AO3 미merge |
| F9-07 | 날짜·KST | FE5 | boundary triage | **no defect** — 기존 unit/E2E pass |
| F9-08 | 공통 Toast | FE3~8 | duplicate·422 | **closed (prior)** — FE3-06·FE6-04·FE7-06·FE8-06 |

**코드 변경:**

- `frontend/src/hooks/useAdminUnauthorizedRedirect.ts` — Admin API error Toast +
  401 login redirect 공통 hook
- `frontend/src/pages/admin/AdminPolicyDataPage.tsx`
- `frontend/src/pages/admin/AdminLogsPage.tsx`
- `frontend/src/pages/admin/CollectionRunsPage.tsx`
- `frontend/src/pages/admin/CollectionRunDetailPage.tsx` — hook 적용
- `frontend/src/pages/admin/AdminLoginPage.tsx` — cooldown lint fix
- `frontend/src/utils/userLocalStorageRecoveryNotice.ts` — session-scoped recovery notice
- `frontend/src/utils/userLocalStorage.ts` — recovery 시 notice 기록
- `frontend/src/components/user/UserLocalStorageRecoveryBanner.tsx`
- `frontend/src/components/common/LayoutErrorBoundary.tsx`
- `frontend/src/components/common/RootErrorFallback.tsx`
- `frontend/src/App.tsx`
- `frontend/src/layouts/AppShellLayout.tsx` — user shell banner mount
- `frontend/src/styles/theme.css` — `.user-local-recovery-banner*`
- `frontend/tests/userLocalStorageRecoveryNotice.test.ts`

**W4-G4 blocker (Frontend-only FE9-01 범위 밖):**

| Blocker | 영향 | 후속 |
| --- | --- | --- |
| Integration 09 AO1~AO3 admin policy·log API 미merge | FE8 Real API golden E2E skip | Backend/Integration Forest |
| `eligibility_summary` Real API 미merge | FE7 Real API golden skip | Backend Forest |
| W4-G3 actual PostgreSQL E2E 미실행 (로컬 환경) | actual 연동 결함 추가 triage 불가 | Team Leader W4-G3 실행 |

계획상 Backend blocker가 남으면 FE9-01 Frontend-only 완료가 제한된다 — 본 Slice는
Frontend 수정 가능 항목 closure + `CONDITIONAL` 근거 기록으로 마감한다.

### FE9-01 hotfix — `/` white screen (2026-08-12)

- **증상**: 브라우저 접속 시 React UI 미렌더(white screen).
- **점검**: FE9-01 `UserLocalStorageRecoveryBanner`·`userLocalStorage` recovery notice·
  `useSyncExternalStore` snapshot module init 경로. Playwright `/` E2E는 통과하나
  storage 예외·provider 누락 시 전역 crash 가능성 확인.
- **수정**:
  - `UserLocalStorageRecoveryBanner` — sessionStorage read를 mount `useEffect`로 이동,
    peek/dismiss/message build try/catch
  - `userLocalStorage.ts` — recovery notice 기록 try/catch (reset 차단 방지)
  - `userConditionsStorage.ts`·`userFavoritesStorage.ts` — module init·sync try/catch
  - `LayoutErrorBoundary` — banner·Outlet 격리
  - `RootErrorFallback` — route `errorElement` (404·runtime error fallback UI)
  - `useAdminUnauthorizedRedirect` — optional Toast context (provider 밖 throw 방지)

### FE9-02 — 4주차 Frontend 전체 회귀 (Mock-first)

**목표:** W4-F10 + W4-I3 Release 2 Frontend midpoint 회귀 매트릭스 E2E.

**산출물:** `frontend/e2e/week4-regression.spec.ts` — 5 Mock path + 1 Real API conditional skip.

**회귀 매트릭스 실행 결과 (2026-08-12):**

| Path | W4 | 시나리오 | 결과 | 비고 |
| --- | --- | --- | --- | --- |
| A | W4-I1 | PIN → runs → manual run → policies → logs | pass | Mock admin flow |
| B | W4-IE1 | detail → eligibility card → evidence → 원문 | pass | seed policy id 1, 승인 DTO |
| C | W4-I2 | conditions → recommend → favorite → calendar → notify → `.ics` | pass | ICS disabled — seed id 1 `application_status: closed` |
| Release 1 | W4-I3 | home → `/search?q=` → detail `include_partial` | pass | M4 partial golden |
| Cross | W4-F5 | mobile viewport·keyboard favorite·search | pass | mobile sidebar hidden — `/search` direct navigation |
| Real API | W4-I3 | week4 golden search | skip | `VITE_USE_MOCK=false` + Backend 필요 |

**Mock-first triage (FE9-02 범위 밖·기록만):**

- Mock seed에 `application_status: open` + `application_end` 조합 정책 없음 → ICS
  enabled Browser golden은 Real API 또는 seed 확장 후 별도 Slice.
- mobile(`max-width: 640px`)에서 sidebar `display: none` — 회귀 spec은 홈 layout·
  direct route navigation으로 spot check.

## 설계 결정

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| Admin 401 handling | `useAdminUnauthorizedRedirect` hook | W4-F9 session 범주; 4 admin page DRY |
| Recovery UX | sessionStorage notice + AppShell banner | localStorage reset 후 one-shot 안내; persist 금지 |
| FE9-01 completion | `CONDITIONAL` | Backend actual merge·W4-G3 E2E pending |
| FE9-02 completion | `CONDITIONAL` | Mock-first 회귀 pass; Real API golden·W4-G3 E2E pending |
| Week4 regression spec | 단일 `week4-regression.spec.ts` | W4-F10 matrix를 Forest E2E helper 패턴으로 재사용 |

## 주요 변경 파일

- `frontend/src/hooks/useAdminUnauthorizedRedirect.ts`
- `frontend/src/pages/admin/AdminLoginPage.tsx`
- `frontend/src/pages/admin/AdminPolicyDataPage.tsx`
- `frontend/src/pages/admin/AdminLogsPage.tsx`
- `frontend/src/pages/admin/CollectionRunsPage.tsx`
- `frontend/src/pages/admin/CollectionRunDetailPage.tsx`
- `frontend/src/utils/userLocalStorageRecoveryNotice.ts`
- `frontend/src/utils/userLocalStorage.ts`
- `frontend/src/components/user/UserLocalStorageRecoveryBanner.tsx`
- `frontend/src/components/common/LayoutErrorBoundary.tsx`
- `frontend/src/components/common/RootErrorFallback.tsx`
- `frontend/src/App.tsx`
- `frontend/src/layouts/AppShellLayout.tsx`
- `frontend/src/styles/theme.css`
- `frontend/tests/userLocalStorageRecoveryNotice.test.ts`
- `frontend/e2e/week4-regression.spec.ts`
- `frontend/tsconfig.test.json`
- `docs/development/develop_plan/frontend/09_integration_and_regression.md`
- `docs/development/development_notes/frontend/integration_and_regression.md`
- `docs/index.md`, `docs/development/development_notes/README.md`, `CHANGELOG.md`

## 검증 결과

```text
cd frontend && npm test              — 171 passed
cd frontend && npm run lint          — passed
cd frontend && npm run build         — passed
cd frontend && npm run test:e2e      — 92 passed, 7 skipped (Real API golden)
cd frontend && npm run test:e2e -- e2e/week4-regression.spec.ts — 5 passed, 1 skipped
python3 scripts/validate_docs.py     — passed
```

Real API golden E2E(`VITE_USE_MOCK=false`)와 W4-G3 PostgreSQL E2E는 본 Forest에서
실행하지 않았다.

## 남은 작업

- Backend merge 후 W4-F9 Real API 항목(F9-05·F9-06) 재triage·closure
- `VITE_USE_MOCK=false` 환경에서 week4 Real API golden 및 Forest별 Real API skip 해소
- [Real API 수동 테스트 가이드](../../frontend_real_api_manual_testing_guide.md)로 Browser 검증 후 E2E 재실행
- W4-G3 actual PostgreSQL E2E 실행 후 Frontend 결함 routing

## 관련 문서

- [Integration Fix and Regression Forest 계획](../../develop_plan/frontend/09_integration_and_regression.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [CollectionRun Admin UI 개발 기록](collection_run_admin_ui.md)
- [User Service Features 개발 기록](user_service_features.md)
- [Admin Observability UI 개발 기록](admin_observability_ui.md)

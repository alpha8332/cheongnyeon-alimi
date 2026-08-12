# Frontend Integration Fix and Regression Forest 개발 계획

## 계획 정보

- 번호: Frontend 09
- 담당 영역: Frontend
- 상태: draft
- 계획일: `2026-08-11`
- 대상 Release: `v0.5.0`
- 공통 시작 커밋: `22118b8e618c3b15464865be3113157888197a02`
- 4주차 대응: `W4-F9`, `W4-F10`, `W4-I3` (`week_04_v0_5_0.md`)
- 선행 Forest:
  Frontend 03·05·06·07·08 actual 연결 Slice(FE3-05, FE5-07, FE6-05, FE7-05,
  FE8-05) 및 Backend·Integration Phase 2~3 머지
- 후속 Forest: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/frontend/week4-integration-regression`
- 현재 Slice: FE9-01 completed (Frontend-only, W4-G4 `CONDITIONAL`)

## 목적

4주차 Phase 3~4에서 Backend·Data actual API와 Frontend Forest를 연결한 뒤
발생하는 **cross-Forest 연동 버그**를 한 곳에서 수정·추적하고, 관리자·
자격요건·추천·사용자·Release 1 검색 golden flow를 포함한 **Frontend 전체
회귀**를 W4-G3·W4-G4 판정 전에 실행한다.

## 범위

- W4-F9: 인증 상태·핵심 조건·추천·localStorage·날짜·공통 오류 UI 통합 수정
- W4-F10: Frontend 03·05·06·07·08·04(Release 1) Browser·E2E 회귀 정리
- W4-I3: Release 1 golden 검색·상세 non-regression 확인
- W4-I1·I2·IE1 E2E checklist와의 gap 분류·blocker 기록
- `python scripts/validate_docs.py` 및 Forest 개발 기록 동기화

## 범위 밖

- Backend·Data·Integration Forest 자체 버그 수정 (해당 Forest로 인계)
- 5주차 QA·사용성 리뷰·보고서 담당 독립 검증 (Integration 07 A2)
- Production Docker·CI·`v0.5.0` tag
- 신규 기능 Slice (각 담당 Forest 계획으로 분류)

## 선행 조건

- Frontend 03·05·06·07·08의 Mock-first Slice와 actual 연결 Slice 1차 완료
- W4-G2 영역별 준비 또는 W4-G3 actual E2E 1차 실행으로 결함 목록 존재
- Release 1 golden query·control acceptance 기준 문서 접근 가능
- Integration 07 midpoint 판정(W4-G4) 전 Team Leader blocker 분류 합의

## 공통 설계 원칙

- 연동 버그는 **재현 시나리오·영향 Forest·blocker 여부**를 development notes에
  남기고 임의 hotfix without trace 금지.
- cross-Forest 수정은 **최소 diff** — 해당 Forest Slice owner와 충돌 시 인계
  보드에 등록.
- 회귀 실패는 성공으로 기록하지 않고 W4-G4 `BLOCKED` 또는 `CONDITIONAL` 근거로
  남긴다.
- Release 1 golden flow(홈 → `/search?q=` → 상세)는 모든 회귀 실행의 필수
  subset이다.

## Slice 계획

| 4주차 | FE9 Slice | 책임 |
| --- | --- | --- |
| W4-F9 | FE9-01 | actual 연동 후 통합 버그 수정 |
| W4-F10, W4-I3 | FE9-02 | 4주차 Frontend 전체 회귀·golden 검색 |

**선행:** FE3-05, FE5-07, FE6-05, FE7-05, FE8-05 (각 Forest actual E2E 1차)
또는 W4-G3 E2E에서 수집된 결함 목록.

---

### FE9-01 — actual 연동 통합 버그 수정 — completed (Frontend-only, W4-G4 CONDITIONAL)

| 항목 | 내용 |
| --- | --- |
| **목표** | W4-F9: Backend/Data 머지 후 Frontend cross-Forest 연동 결함 수정 |
| **대상 영역** | 관리자 PIN·token 만료(FE3), eligibility card(FE7), 추천·조건(FE6·FE5), localStorage 손상·날짜(FE5), 공통 Toast(FE3·7·8·6), admin data/log(FE8) |
| **예상 변경 파일** | 영역별 owner Forest 파일; 공통 `ApiErrorToast`·session refresh hook |
| **선행** | W4-G3 1차 E2E 또는 각 Forest FE*-05 actual Slice |
| **세부 작업** | 결함 ticket을 Forest·Slice ID에 매핑; PIN 401→login redirect; detail+summary DTO drift; recommendation conditions sync; corrupt localStorage recovery UX |
| **검증** | 재현 시나리오 Browser; affected Forest unit test |
| **완료 기준** | W4-F9 checklist 항목 closure; blocker 미해결 시 W4-G4 `BLOCKED` 근거 명시 |
| **상태** | Frontend-only 수정·triage 완료. Backend actual 연동 blocker는 development notes에 `BLOCKED` 분류. W4-G4 Frontend 판정은 `CONDITIONAL`. |

**W4-F9 Frontend-only closure (2026-08-12):**

| 범주 | 결과 | 비고 |
| --- | --- | --- |
| 인증·세션 | closed (Mock) | `useAdminUnauthorizedRedirect` 공통 hook, AdminLoginPage cooldown lint |
| localStorage | closed | corrupt recovery session banner (`UserLocalStorageRecoveryBanner`) |
| 추천·조건 | no defect | `useSavedConditions` 공유 — mismatch 재현 없음 |
| 공통 Toast | closed (prior FE3/6/7/8) | dedupe·401/5xx wiring 기존 Slice에서 완료 |
| 자격요건 UI | **BLOCKED** | `eligibility_summary` Real API 미merge |
| admin data/log Real API | **BLOCKED** | Integration 09 AO1~AO3 미merge |
| 날짜·알림 KST | no defect | FE5 unit/E2E 기존 pass, triage 재현 없음 |

**W4-F9 대표 수정 범주 (non-exhaustive):**

| 범주 | 예시 | 연계 Slice |
| --- | --- | --- |
| 인증·세션 | token 만료·429 cooldown·401 redirect | FE3-01, FE8-05 |
| 자격요건 UI | partial·unknown·evidence drift | FE7-01~05 |
| 추천·조건 | localStorage conditions vs API request mismatch | FE6-01, FE5-02 |
| localStorage | version mismatch·corrupt reset 후 UI state | FE5-00, FE5-08 |
| 날짜·알림 | KST boundary·null deadline | FE5-03~04 |
| 공통 오류 UX | Toast duplicate·non-retryable 422 | FE3·6·7·8 Toast 명세 |

---

### FE9-02 — 4주차 Frontend 전체 회귀 — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | W4-F10 + W4-I3: Release 2 Frontend midpoint 회귀 및 golden flow |
| **예상 변경 파일** | Playwright week4 regression spec, regression checklist doc in development notes |
| **선행** | FE9-01 (또는 known blocker 목록 확정), FE3~8 actual Slice |
| **세부 작업** | 아래 회귀 매트릭스 실행; 실패 시 FE9-01 또는 owner Forest로 routing |
| **검증** | `npm run test`, `npm run lint`, `npm run build`, `npm run test:e2e` |
| **완료 기준** | W4-F10 산출; W4-I3 golden pass; W4-G3·G4 Frontend 항목 evidence |

**회귀 매트릭스 (FE9-02):**

| Critical Path | E2E 시나리오 | 연계 week_04 | Forest |
| --- | --- | --- | --- |
| A 관리자 | PIN login → run list → manual run → data table → log view | W4-I1 | FE3, FE8 |
| B 자격요건 | detail → 핵심 신청 조건 → evidence → 원문 | W4-IE1 | FE7 |
| C 사용자 | conditions → recommend → favorite → D-Day → notify → `.ics` | W4-I2 | FE5, FE6 |
| Release 1 | home → `/search?q=` golden → detail `include_partial` | W4-I3 | FE4, FE5~7 |
| Cross | loading·empty·error·partial·keyboard·mobile spot checks | W4-F5 | FE3~8 |

## 검증 계획

```powershell
Set-Location frontend
npm run test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
python scripts/validate_docs.py
git diff --check
```

실행하지 않은 E2E·Browser 항목은 development notes에 `pending` 또는 `blocked`
로만 기록한다.

## Forest 완료 기준

- W4-F9 연동 결함이 Slice·Forest 단위로 추적·해결 또는 blocker 분류됨
- W4-F10 Frontend 전체 회귀 checklist 실행 결과가 development notes에 기록됨
- W4-I3 Release 1 golden 검색·상세 회귀 pass (또는 blocker 명시)
- W4-G3·W4-G4 Frontend 판정에 필요한 evidence 링크 제공
- `python scripts/validate_docs.py` pass

## 위험과 미확정 사항

- FE9는 **조율 Forest**이므로 owner Forest와 수정 범위 충돌 시 인계 보드
  escalation이 필요하다.
- Backend blocker가 남으면 FE9-01을 Frontend-only로 완료할 수 없다.
- Playwright spec 범위가 커지면 CI runtime 증가 — smoke vs full suite 분리
  W4-G4 전 합의 필요.

## 관련 문서

- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [CollectionRun Admin UI (FE3)](03_collection_run_admin_ui.md)
- [User Service Features (FE5)](05_user_service_features.md)
- [Recommendation UI (FE6)](06_recommendation_ui.md)
- [Eligibility Summary UI (FE7)](07_eligibility_summary_ui.md)
- [Admin Observability UI (FE8)](08_admin_observability_ui.md)
- [Policy Search (FE4)](04_policy_search.md)
- [Release 2 Feature Acceptance](../integration/07_release_2_feature_acceptance.md)

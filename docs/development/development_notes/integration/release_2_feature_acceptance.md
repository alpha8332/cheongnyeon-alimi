# Integration 07 Release 2 Feature Acceptance 개발 기록

## 작업 정보

- 상태: completed
- 완료 판정: `W5-G2_CONDITIONAL`
- 작업일: `2026-08-17`~`2026-08-23`
- 담당 영역: Data, Team Leader - Integration
- 현재 브랜치: `feature/integration/week-05-acceptance`
- 시작 SHA: `29b2dd5ef596286ec2df1ede48398d94c0d010d7`
- DTL5-4 코드 검증 SHA: `1019fda6d55744f4d146b7abab96715a730f8705`
- DTL5-6 조건부 후보 SHA: `3066acb272dc3f40f9d8684bd2e46e6d69169f71`
- 계획: [Integration 07 Release 2 Feature Acceptance](../../develop_plan/integration/07_release_2_feature_acceptance.md)
- 주차 계획: [5주차 Data·Team Leader 실행 계획](../../weekly_plan/week_05_data_team_leader.md)
- 현재 판정: `W5-G2_CONDITIONAL` (6주차 착수 가능, main/tag 후보 승격 보류)

## 목적

4주차 결과와 5주차 계획 문서가 병합된 최신 `develop`을 Release 2 공통
시작점으로 고정하고, Data 06·Backend·Frontend 병렬 작업을 열기 전에 Git,
Migration, 실제 DB, Runtime, API, Browser와 테스트 실행 환경을 재검증한다.

## Forest 범위

- A0 / DTL5-0 공통 시작 SHA·Migration·DB 기준·actual API mode 고정
- A2 / DTL5-1~5 Data 06, 전체 actual E2E, 독립 사용성·QA와 결함 수정
- A3 / DTL5-6 수정본 독립 재검증과 Release 2 Gate

이 기록은 A0 기준선부터 Data 06, Backend·Frontend 통합, 역할 격리 대체
사용성·QA, 결함 수정과 DTL5-6 Release 2 조건부 판정까지 다룬다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| A0 / DTL5-0 | completed | `develop@29b2dd5`, Migration `20260810_0006`, 실제 DB 3,269건·지역정책 109건, Runtime·API·Browser·테스트 환경 확인과 `W5-G0_PASS` |
| A2 / DTL5-1~3 | completed | Data 06 승인 Source 5개 actual·KOSAF DB/API/Browser 인수·`SOP-G5_PASS` |
| A2 / DTL5-4 | completed | Backend `W5-B1`·Frontend `W5-F1`·Data 06 통합, 전체 PostgreSQL·Browser 회귀와 `W5-G1_PASS` |
| A2 / DTL5-5 | completed | 역할 격리 대체 사용성·QA, high 결함 `DTL5-5-FE-01` 수정 `3066acb` |
| A3 / DTL5-6 | completed | 새 SHA·독립 Volume 전체 회귀, 자격증명 교체·비추적 확인, `W5-G2_CONDITIONAL` |

## 구현 내용

### Git과 5주차 시작점

- `develop`과 `origin/develop`은
  `29b2dd5ef596286ec2df1ede48398d94c0d010d7`에서 일치했다.
- 이 커밋은 4주차 병합 `f0d3dd3` 위에 5주차 계획 구체화 커밋을 포함한다.
- DTL5-0 시작 시 worktree는 clean이었고 미추적 Runtime 산출물은 없었다.
- 4주차 기능 기준은 `W4-G4_MIDPOINT_PASS`를 유지하며 5주차 최종 Release
  판정으로 소급하지 않았다.

### Migration과 실제 DB 기준

- repository Alembic head와 실제 DB `alembic_version`은 모두
  `20260810_0006`이었다.
- 실제 `cheongnyeon_alimi` DB의 정책은 3,269건이었다.
- `regional-` Source 12개의 정책 합계는 109건이었다. Source별 합계는 부산
  16, 대구 33, 대전 1, 강원 2, 광주 10, 경북 2, 경남 7, 인천 15, 제주 1,
  전북 16, 서울 1, 울산 5건으로 기존 4주차 기준과 일치했다.
- `cheongnyeon_alimi_test` 전용 DB 존재와 `_test` 이름 안전 경계를 확인했다.
- 이 조회는 read-only였으며 실제 서비스 DB의 row·Schema를 변경하지 않았다.

### Runtime·API·Frontend·Browser 준비

- 시스템 PATH에는 Node가 없지만 `run_local.ps1`이 지원하는 Codex 번들 Node
  `v24.19.0` fallback을 확인했다.
- `run.bat -NoBrowser -ExitAfterReady`로 실제 PostgreSQL을 연결해 FastAPI
  `http://127.0.0.1:8000/health` 200과 Vite
  `http://127.0.0.1:3000/` readiness를 확인했다.
- actual API mode는 `run_local.ps1`이 Frontend에
  `VITE_API_BASE_URL=http://127.0.0.1:8000`을 주입하는 로컬 FastAPI 연결이다.
- readiness 확인 뒤 Backend와 Frontend 프로세스가 정상 종료돼 8000·3000
  listener가 남지 않았다.
- 저장소의 `@playwright/test`로 Chromium headless launch·close를 확인했다.

### DTL5-4 통합 전 사전 회귀

- 실제 DB는 Migration `20260810_0006`, 정책 3,270건, 지역 Source 109건,
  `kosaf-scholarship-web` 1건이다. Data 06 전 기준 3,269건에서 accepted KOSAF
  1건만 증가했다.
- `국가근로장학금` 검색과 상세 `15095`는 `education`·`open`·한국장학재단
  원문을 반환했고, 인앱 Browser도 한국장학재단·교육·접수 중과 KOSAF 원문
  연결을 다시 확인했다.
- 관리자 actual은 PIN session, Policy·CollectionRun, 구조화 log, rotate·archive
  감사와 인증 경계를 통과했다. 사용자 actual은 검색·자격 근거·추천·북마크·
  달력·알림·`.ics`와 손상 localStorage 복구를 통과했다.
- 실제 DB에서 eligibility `14984`, 부산 지역 `14985`, open deadline `15003`을
  조건으로 다시 선정했다. 정책 ID는 적재·prune에 따라 변할 수 있으므로 독립
  QA도 역사 ID가 아니라 Source·상태·필수 필드로 표본을 선정한다.
- 이 결과는 Data 06 브랜치에서 현재 `develop` 기능과 Data 변경을 함께 검사한
  사전 회귀다. 원격 Frontend `style-and-ux-fixes` 8개 커밋과 Backend W5-B1
  담당 결과를 포함하지 않으므로 DTL5-4 완료나 `W5-G1_PASS`로 판정하지 않는다.

### DTL5-4 담당 산출물 통합과 W5-G1

- Backend 최종 제출 `da20d9c`의 tree를 검토해 Integration 커밋 `babb432`로
  squash 반영했다. 담당 브랜치의 비밀 포함 과거 커밋은 ancestry에 넣지 않았고,
  Data 06 canonical identity·실제 검증 수치를 문서에 바로잡았다.
- Frontend 최종 제출 `d19fd02`는 merge 커밋 `792320c`로 반영했다. 첫 actual
  회귀에서 드러난 고정 숫자 ID, Mock 전용 pagination, 이전 화면 문구 assertion은
  Integration 수정 `1019fda`에서 현재 계약에 맞췄다.
- KOSAF 표본은 변동 가능한 DB 숫자 ID 대신
  `kosaf-scholarship-web / scholarship05_04_01` Source identity로 찾는다.
  현재 실제 DB에서는 정책 `15095`, `application_end=null`, eligibility
  `coverage=unknown`이며 상세·모바일·`.ics` 비활성 경계를 통과했다.
- 통합본은 Data `334 passed`·172 subtests, Backend PostgreSQL `187 passed`,
  Frontend unit `216 passed`·lint·build, Mock Browser `80 passed / 14 skipped`,
  actual 4-spec `36 passed / 8 skipped`, actual acceptance `3 passed`를 통과했다.
- 관리자 actual acceptance는 Policy·CollectionRun·구조화 로그·rotate·archive
  감사·401·429 경계를, 사용자 acceptance는 검색·자격 비확정·추천·북마크·
  달력·알림 화면·D-7 실제 정책 `4148`의 `.ics`·손상 저장소 복구를 확인했다.
- 위 결과와 Data 06 `SOP-G5_PASS`, 실제 정책 3,270건·지역 109건·KOSAF 1건을
  대조해 `W5-G1_PASS`로 판정했다. 이는 DTL5-5 독립 검증 시작 승인이지
  `W5-G2` Release 2 승인이나 `develop` 병합 승인이 아니다.

### 첫 실패와 보정

- 첫 DB 건수 조회는 repository root에서 Backend `app` 모듈을 import해
  `ModuleNotFoundError`가 발생했다. 설정을 추정하지 않고 동일한 process
  `DATABASE_URL`을 SQLAlchemy에 직접 전달해 read-only 조회를 재실행했다.
- 첫 Browser launch는 설치되지 않은 `playwright` package 이름을 사용해
  실패했다. repository manifest의 실제 package인 `@playwright/test`로
  재실행해 통과했다.
- app 실행용 번들 Node에는 `npm.cmd`가 없었다. 새 패키지를 설치하지 않고
  설치된 Codex CUA Node/npm `v24.19.0`을 명시해 Frontend 검증을 실행했다.
- DTL5-4 Frontend 첫 test·lint·build는 하위 명령이 `node.exe`를 PATH에서 찾지
  못해 실패했다. 번들 Node `bin`을 PATH에 명시한 동일 명령은 모두 통과했다.
- actual Vite에 전체 Browser suite를 바로 실행하면 Mock 전용 시나리오가 실제
  API를 소비해 연쇄 실패했다. 실행을 중단하고 actual 서버는 유지한 채 별도
  `3001` Mock Vite에서 79건을 실행하고, 실제 API 조건부 14건은 actual
  `3000`에서 분리 실행했다.
- 첫 Real API 실행은 역사 정책 ID `167`·`1566`이 현재 DB에서 404라 3건이
  실패했다. 현재 조건을 만족하는 `14984`·`14985`·`15003`으로 재선정해
  11건 전체를 통과했고, 나머지 ES3 조건부 3건도 별도 통과했다.
- 담당 Frontend 통합 직후 actual 4-spec은 고정 ID `160`·`3`, actual DB에 없는
  Mock pagination 가정 때문에 4건이 실패했다. Data 06 stable Source identity를
  조회하고 Mock 전용 pagination을 actual에서 제외해 `36 passed, 8 skipped`로
  재실행했다.
- Mock 전체 첫 실행은 Playwright `webServer`가 현재 번들 환경에 없는
  `npm.cmd`를 요구해 테스트 시작 전에 중단됐다. 같은 `VITE_USE_MOCK=true`로
  설치된 Vite를 직접 실행한 뒤 `80 passed, 14 skipped`로 통과했다.
- actual acceptance 첫 실행은 FE 화면 변경 뒤 strict locator 1건과 홈에서
  제거된 이전 문구 1건이 stale해 2건 실패했다. 역할 기반 heading·원문 URL
  link와 storage recovery status·schema 2 payload를 검증하도록 수정했다. 두
  번째 실행의 남은 원문 버튼 명칭 1건도 URL link 계약으로 정렬한 뒤 전체
  `3 passed`를 재확인했다.

## 주요 변경 파일

- `docs/development/development_notes/integration/release_2_feature_acceptance.md`
- `docs/development/develop_plan/integration/07_release_2_feature_acceptance.md`
- `docs/development/weekly_plan/week_05_data_team_leader.md`
- `docs/development/weekly_plan/week_05_release_2.md`
- `frontend/e2e/helpers/e2eMode.ts`
- `frontend/e2e/dtl4-7-actual.spec.ts`
- `frontend/e2e/eligibility-summary-ui.spec.ts`
- `frontend/e2e/policy-search-audit.spec.ts`
- `frontend/e2e/user-service-features.spec.ts`
- 관련 계획·개발 기록 색인

Integration 수정은 테스트 계약과 문서에 한정했다. 제품 Schema·Migration·실제
DB Policy row는 변경하지 않았다.

## 설계 결정

- 5주차 공통 시작 SHA는 4주차 병합 커밋 `f0d3dd3`이 아니라 5주차 계획까지
  `develop`·`origin/develop`에 동기화된 `29b2dd5`로 고정한다.
- 정책 3,269건과 지역정책 109건은 Data 06 적재 전 회귀 기준이다. DTL5-4의
  실제 3,270건은 accepted KOSAF 1건 증가와 일치하며, 나머지
  duplicate·review·closed·failed는 새 Policy row를 만들지 않았다.
- Node/npm PATH 부재는 app·테스트 실행에 사용할 검증된 명시 경로가 있고 새
  설치 없이 재현됐으므로 W5-G0 blocker로 보지 않는다. 일반 개발자 환경의
  Node 설치 기준은 기존 README 계약을 유지한다.
- 사용성 리뷰어·QA·보고서의 책임, 독립 시나리오와 증거 양식은 5주차 계획에
  고정해 W5-G1 인계를 완료했다. 실제 독립 수행 결과는 DTL5-5에서만 기록한다.
- 담당 Backend 브랜치의 비밀 포함 과거 이력은 Integration ancestry에서
  제외했다. 노출된 실제 로컬 DB 자격증명은 교체 대상으로 유지하며, 교체
  확인 전에는 `W5-G2` Release 후보로 승격하지 않는다.
- 실제 DB 숫자 ID는 적재·prune에 따라 달라질 수 있으므로 Data 06 actual
  fixture는 stable `(source_id, external_id)`를 먼저 찾고 반환된 ID를 사용한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Git 기준선 | `develop`=`origin/develop`=`29b2dd5`, 시작 worktree clean |
| Alembic repository/actual | `20260810_0006 (head)` 일치 |
| 실제 DB read-only 기준 | 정책 3,269건, 지역 Source 12개·109건 |
| 전용 PostgreSQL DB | `cheongnyeon_alimi_test` 존재 |
| Migration·PostgreSQL 집중 pytest | 7건 통과, 기존 Starlette deprecation warning 1건 |
| local app readiness | Backend health 200, Frontend readiness, 두 process 정상 종료 |
| Browser runtime | Playwright Chromium headless launch·close 통과 |
| DTL5-0 Frontend unit | 162건 통과, skip 0 |
| DTL5-0 Frontend lint·build | 통과, Vite native config·500 kB chunk 비차단 warning |
| Git 비추적 | `.env`·Runtime·로그·DB·pgpass 추적 0건 |
| Data 전체 pytest | 전용 PostgreSQL 포함 `334 passed`, 1 warning, 172 subtests |
| Backend 전체 pytest | 전용 PostgreSQL 포함 `187 passed`, 1 warning |
| 테스트 DB 정리 | 전체 회귀 뒤 public table은 `alembic_version`만 유지 |
| 담당 산출물 통합 | Backend `da20d9c` tree → `babb432` squash, Frontend `d19fd02` → `792320c` merge |
| 비밀 이력 경계 | 비밀 포함 Backend 과거 commit은 Integration ancestry 제외, 실제 자격증명 교체는 W5-G2 선행 조치 |
| Frontend W5 unit·lint·build | `216 passed`, lint·production build 통과 |
| Frontend Mock Browser | `80 passed`, actual 조건부 14건은 의도대로 skip |
| Frontend actual Browser | 4-spec `36 passed / 8 skipped`, DTL4-7 actual acceptance `3 passed` |
| 실제 DB·API | Migration `20260810_0006`, 정책 3,270·지역 109·KOSAF 1, health 200 |
| Data 06 인앱 Browser | 정책 `15095`, 한국장학재단·교육·접수 중·공식 원문 연결 통과 |
| 문서·diff | `Documentation validation passed.`, `git diff --check` 통과 |
| DTL5-4 Gate | `W5-G1_PASS`, DTL5-5 독립 사용성·QA 시작 가능 |
| DTL5-5 격리 실제 UI | 검색·상세·추천·북마크·달력·알림·`.ics`, 관리자 PIN·정책·실행·로그·품질·로그아웃 통과 |
| DTL5-5 결함 | `DTL5-5-FE-01` high: unknown 자격의 `제한 없음 해당없음` 확정 노출을 `3066acb`에서 미확정 안내로 보정 |
| DTL5-5 Frontend | unit `222 passed`, lint·production build 통과; actual Browser `39 passed / 11 skipped` |
| DTL5-5 DB·API | Migration `20260810_0006`, 정책 3,273·CollectionRun 61, health 200·무인증 admin 401, 추천 5회 중앙값 `1,563.5 ms` |
| DTL5-6 Data | unittest `323 passed` |
| DTL5-6 Backend·PostgreSQL | `202 passed / 2 skipped`; RA manifest·scratch opt-in 전용 skip, 테스트 DB는 `alembic_version`만 유지 |
| DTL5-6 Frontend | unit `222 passed`, lint·build, Mock `80 passed / 14 skipped`, actual `39 passed / 11 skipped` |
| DTL5-6 Docker | `3066acb` image·새 project/Volume, snapshot hash·3,273/61 복원과 재시작 보존·health 200 통과 |
| DTL5-6 비밀 경계 | 현재 비추적 DB 비밀번호가 과거 노출 후보와 다르고 비기본·충분한 길이임을 값 출력 없이 확인 |
| DTL5-6 Gate | 기능 blocker/high 0건, 팀 외 독립 인력 미수행 절차 제약으로 `W5-G2_CONDITIONAL` |

DTL5-0·Data 브랜치 사전 회귀는 비교 기준으로만 사용했고, Gate 판정은
Integration 코드 검증 SHA `1019fda`의 재실행 결과를 사용했다.
Starlette/httpx deprecation과 Vite native config·500 kB chunk 경고는 기존
비차단 경고다.

## 남은 작업

1. 팀 외 독립 인력 검증을 추가로 수행하면 같은 `3066acb` 시나리오와 snapshot
   기준으로 결과를 연결하고 `W5-G2_PASS` 승격 여부를 재판정한다.
2. `PASS` 전에는 `main` PR·`v0.5.0` tag 후보로 지정하지 않는다.
3. 6주차 production 배포구조·최신화 파이프라인 작업은 조건부 제약을 유지한 채
   별도 Forest로 시작한다.

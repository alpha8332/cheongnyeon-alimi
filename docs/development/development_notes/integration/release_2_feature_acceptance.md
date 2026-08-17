# Integration 07 Release 2 Feature Acceptance 개발 기록

## 작업 정보

- 상태: in-progress
- 작업일: `2026-08-17`
- 담당 영역: Data, Team Leader - Integration
- 현재 브랜치: `develop`
- 시작 SHA: `29b2dd5ef596286ec2df1ede48398d94c0d010d7`
- 계획: [Integration 07 Release 2 Feature Acceptance](../../develop_plan/integration/07_release_2_feature_acceptance.md)
- 주차 계획: [5주차 Data·Team Leader 실행 계획](../../weekly_plan/week_05_data_team_leader.md)
- 현재 판정: `W5-G0_PASS`

## 목적

4주차 결과와 5주차 계획 문서가 병합된 최신 `develop`을 Release 2 공통
시작점으로 고정하고, Data 06·Backend·Frontend 병렬 작업을 열기 전에 Git,
Migration, 실제 DB, Runtime, API, Browser와 테스트 실행 환경을 재검증한다.

## Forest 범위

- A0 / DTL5-0 공통 시작 SHA·Migration·DB 기준·actual API mode 고정
- A2 / DTL5-1~5 Data 06, 전체 actual E2E, 독립 사용성·QA와 결함 수정
- A3 / DTL5-6 수정본 독립 재검증과 Release 2 Gate

이번 기록은 A0 결과만 다룬다. Data 06 수집·적재, 전체 W5-G1 E2E와 독립
검증은 아직 수행하지 않았다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| A0 / DTL5-0 | completed | `develop@29b2dd5`, Migration `20260810_0006`, 실제 DB 3,269건·지역정책 109건, Runtime·API·Browser·테스트 환경 확인과 `W5-G0_PASS` |
| A2 / DTL5-1~3 | pending | Data 06 SOP0~SOP5 |
| A2 / DTL5-4 | pending | Data 06 포함 전체 actual E2E와 W5-G1 |
| A2 / DTL5-5 | pending | 독립 사용성·QA, 결함 triage·수정·재검증 |
| A3 / DTL5-6 | pending | 문서·전체 회귀와 W5-G2 Release 2 판정 |

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

### 첫 실패와 보정

- 첫 DB 건수 조회는 repository root에서 Backend `app` 모듈을 import해
  `ModuleNotFoundError`가 발생했다. 설정을 추정하지 않고 동일한 process
  `DATABASE_URL`을 SQLAlchemy에 직접 전달해 read-only 조회를 재실행했다.
- 첫 Browser launch는 설치되지 않은 `playwright` package 이름을 사용해
  실패했다. repository manifest의 실제 package인 `@playwright/test`로
  재실행해 통과했다.
- app 실행용 번들 Node에는 `npm.cmd`가 없었다. 새 패키지를 설치하지 않고
  설치된 Codex CUA Node/npm `v24.19.0`을 명시해 Frontend 검증을 실행했다.

## 주요 변경 파일

- `docs/development/development_notes/integration/release_2_feature_acceptance.md`
- `docs/development/develop_plan/integration/07_release_2_feature_acceptance.md`
- `docs/development/weekly_plan/week_05_data_team_leader.md`
- `docs/development/weekly_plan/week_05_release_2.md`
- 관련 계획·개발 기록 색인

코드·Schema·Migration·DB row는 변경하지 않았다.

## 설계 결정

- 5주차 공통 시작 SHA는 4주차 병합 커밋 `f0d3dd3`이 아니라 5주차 계획까지
  `develop`·`origin/develop`에 동기화된 `29b2dd5`로 고정한다.
- 정책 3,269건과 지역정책 109건은 Data 06 적재 전 회귀 기준이다. Data 06의
  목표 row 수를 만들지 않고 accepted·duplicate·review·closed·failed 실제
  판정으로 후속 수치를 결정한다.
- Node/npm PATH 부재는 app·테스트 실행에 사용할 검증된 명시 경로가 있고 새
  설치 없이 재현됐으므로 W5-G0 blocker로 보지 않는다. 일반 개발자 환경의
  Node 설치 기준은 기존 README 계약을 유지한다.
- 사용성 리뷰어·QA·보고서의 책임과 증거 양식은 5주차 계획에 고정했다. 실제
  독립 수행과 담당 확정은 W5-G1 인계 전 필수이며 아직 완료로 기록하지 않는다.

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
| Frontend unit | 162건 통과, skip 0 |
| Frontend lint | 통과 |
| Frontend build | 통과, Vite native config·500 kB chunk 비차단 warning |
| Git 비추적 | `.env`·Runtime·로그·DB·pgpass 추적 0건 |

정확한 전체 Backend·Data 회귀와 actual Browser E2E는 각각 W5-B1·W5-D1~3·
W5-I1 범위이며 DTL5-0 결과로 소급하지 않는다.

## 남은 작업

1. Data 06 development note를 만들고 DTL5-1 / SOP0 후보 정제를 시작한다.
2. Backend W5-B1과 Frontend W5-F1 안정화 회귀를 병렬로 인수한다.
3. Data 06 SOP-G5 뒤 실제 DB → API → Browser 전체 W5-G1을 판정한다.
4. 독립 사용성 리뷰·QA·보고서 담당과 실행 환경을 W5-G1 인계 전에 확정한다.
5. Integration 07 변경 브랜치의 `integration` domain과 거버넌스 문서 불일치를
   사용자 결정에 따라 정리한다.

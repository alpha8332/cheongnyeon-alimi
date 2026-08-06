# Integration 04 Release 1 Acceptance 개발 기록

## 작업 정보

- 상태: in-progress
- 작업일: `2026-08-06`
- 영역: Team Leader - Integration, DT5 Gate G2·G3
- 브랜치: `feature/data/release-dataset-bootstrap`
- 계획: [Integration 04 Release 1 Acceptance](../../develop_plan/integration/04_release_1_acceptance.md)
- 병합 대상: Frontend `b37752a1bb8bfe0043e9de8908de6529309c36ee`,
  Backend `01035da76f09a186409e516d5f030f0af4fdd85f`

## 목적

다른 PC에서 완료한 DT3·DT4의 Git 제외 Runtime 상태를 이 PC에 복구하고,
병합한 Backend 검색 API와 Frontend 검색 UI를 실제 snapshot으로 연결한다.

## Forest 범위

- IA0 FE·BE 비커밋 병합과 로컬 환경 차이 확인
- IA1 snapshot 복구, PostgreSQL 적재, HTTP·Browser 통합과 결함 수정
- IA2 golden query·Release 1 판정은 후속

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| IA0 | completed | FE fast-forward, BE `--no-commit` 병합과 로컬 Runtime 부재 확인 |
| IA1 / DT5 | completed | Gate G2·G3 실제 DB → API → UI 검증 통과 |
| IA2 / DT6 | pending | QA·리뷰어·보고서와 golden query 판정 대기 |

## 구현 내용

### 병합과 로컬 snapshot 복구

Frontend는 현재 Data HEAD의 후손이어서 fast-forward했고 Backend는
`--no-commit --no-ff`로 병합했다. 새 merge commit은 만들지 않았다.

이 PC에는 DT1 표본 Raw만 있고 Runtime DB row는 0건이었다. `runtime/raw`와
PostgreSQL이 Git 제외라는 다른 PC 작업 특성과 일치했다. 저장소 밖 키 파일의
두 레이블을 process 환경변수로만 주입해 기존 승인 예산으로 다시 수집했다.
인증값·query·payload는 출력하거나 기록하지 않았다.

| Source | snapshot ID | 요청 | 수집·수용 | 품질 |
| --- | --- | ---: | ---: | --- |
| 온통청년 | `6add34f7aad9456ab0abb19175b7621c` | 6 | 2,695 | valid 1,459·partial 1,236·invalid 0 |
| 복지로 | `ffa74ef47e6048109f11bf40d1ac5e15` | 6 | 461 | valid 0·partial 461·invalid 0 |

합계 3,156건으로 DT4의 3,159건보다 온통청년이 3건 줄었다. 같은 수치로
조작하지 않고 `2026-08-06` Source 시점 차이로 보존했다.

두 Source 모두 dry-run 후 전건 inserted했고, 동일 snapshot 재실행은
온통청년 2,695건·복지로 461건 전부 unchanged였다. 검색 요청 중 외부 API는
호출하지 않았다.

### 통합 중 수정한 결함

- Backend 신규 PostgreSQL 검색 통합 test fixture가 Alembic의
  `config.attributes["database_url"]`을 사용하지 않아 Runtime 기본 URL로
  접속하던 격리 오류를 수정했다.
- 같은 fixture가 `_test` public schema를 종료 시 정리하지 않아 후속 Migration
  테스트를 오염하던 문제를 수정했다.
- status 조건이 없는 query의 verdict를 `match`로 기대하던 테스트를 승인
  계약의 `null`로 수정했다.
- Frontend 검색어 지우기가 input만 비우고 URL `q`를 남기던 문제를 수정했다.
- E2E의 기본 `page=1` URL 강제 기대를 serializer의 기본값 생략 계약에 맞추고,
  실제 Backend가 Source stopword를 제거한 뒤 남기는 `생활` 미해석 term을
  검증하도록 수정했다.
- Playwright 결과 파일을 Git 추적 대상에서 제거하고 ignore에 추가했다.

## 주요 변경 파일

- `backend/tests/test_postgresql_policy_search_integration.py`
- `frontend/src/pages/user/PolicySearchPage.tsx`
- `frontend/e2e/policy-search-audit.spec.ts`
- `frontend/.gitignore`
- `docs/development/develop_plan/integration/04_release_1_acceptance.md`
- `docs/development/development_notes/integration/release_1_acceptance.md`

## 설계 결정

- 다른 PC의 Runtime 상태는 문서만으로 존재한다고 간주하지 않고 이 PC에서
  manifest와 DB row를 재검증한다.
- 새 snapshot 수치가 이전과 다르면 최신 인수 시점 수치를 사용하되 DT4의
  역사적 기록을 덮어쓰지 않는다.
- 검색 term 결합·score는 API 의미 변경이므로 DT5에서 임의 수정하지 않고
  DT6 결정 대상으로 남긴다.
- 실제 API Browser 통과는 QA·리뷰어·보고서 승인이나 Release 판정을 대신하지
  않는다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Data unittest | 113건 통과 |
| Backend 최초 비-DB 실행 | 99건 통과·15건 skip, warning 2건 |
| Backend 실제 PostgreSQL 첫 실행 | 111건 통과·신규 fixture 3건 오류 |
| Backend fixture 1차 수정 | 112건 통과·기대값/격리 2건 실패 |
| Backend 최종 PostgreSQL 전체 | 114건 통과, warning 2건 |
| Frontend unit | 43건 통과 |
| Frontend build·lint | 통과 |
| Playwright 최초 실행 | 로컬 Chromium 부재로 10건 시작 전 실패 |
| Playwright 설치 후 실제 API 1차 | 7건 통과·3건 실패 |
| E2E 수정 후 2차 | 9건 통과·strict locator 1건 실패 |
| E2E 최종 | 10건 통과 |
| 실제 검색 HTTP | health 200, 빈 q 422, 미일치 term 0건, pagination 확인 |
| 인앱 Browser | 검색·지우기·빈 결과·pagination·partial 상세 통과, console warning/error 0건 |

golden query `27세 천안 청년 월세 지원`은 실제 API에서 46건의 후보를
반환했다. 첫 후보 `청년월세 지원사업`은 연령·지역 unknown으로 표시됐고,
Profile의 confirmed match는 0건이다. 실제 적용 가능성을 단정하지 않는다.

`npm ci`는 실행 중 Vite가 native binding을 잡아 첫 시도에 `EPERM`으로
실패했다. 이 작업에서 시작한 Vite process를 종료한 뒤 lockfile 기준 201개
package 설치가 성공했다. `npm audit`은 high 3건을 보고했으며 자동 수정은
범위 밖이라 실행하지 않았다.

## 남은 작업

- IA2에서 일반 term의 OR 후보 확대와 score 의미를 Backend·Frontend·Data
  계약으로 결정하고 실제 검색 정확도를 재검증한다.
- confirmed golden 정책 부재를 유지할지 Source 범위를 바꿀지 결정한다.
- QA smoke, 사용성 리뷰어와 보고서 근거를 확보한 뒤 Gate G4를 판정한다.
- 기존 Starlette deprecation warning 2건과 npm audit high 3건은 별도
  의존성 검토가 필요하다.

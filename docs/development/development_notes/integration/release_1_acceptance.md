# Integration 04 Release 1 Acceptance 개발 기록

## 작업 정보

- 상태: in-progress
- 작업일: `2026-08-06`
- 영역: Team Leader - Integration, DT5 Gate G2·G3와 DT6 Gate G4
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
- IA2 golden query·Release 1 판정과 차단사항·재개 조건 기록

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| IA0 | completed | FE fast-forward, BE `--no-commit` 병합과 로컬 Runtime 부재 확인 |
| IA1 / DT5 | completed | Gate G2·G3 실제 DB → API → UI 검증 통과 |
| IA2 / DT6 | completed | exact golden query 검증, Gate G4 `blocked` |

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

### DT6 golden query와 Gate G4 판정

동일한 PostgreSQL snapshot 3,156건에 세 가지 요청을 실제 검색 endpoint로
실행했다. 검색 중 외부 Source API는 호출하지 않았다.

| 요청 | 결과 | 판정 |
| --- | ---: | --- |
| `천안 사는 27살 청년 월세 지원 받을 수 있나?` | 48건 | 천안·27세·주거 해석 성공, 첫 후보 지역·연령 unknown |
| `27세 천안 청년 월세 지원` | 46건 | 일반 `지원` term의 OR 일치로 비월세 후보 포함 |
| `월세` + 천안·27세·주거 명시 | 3건 | 전부 복지로 partial, 지역·연령 unknown, confirmed 0건 |

exact query의 첫 후보 `청년월세 지원사업` 상세에는 월 최대 20만원 지원과
`2026-03-30 09:00 ~ 2026-05-29 16:00` 신규 신청기간이 텍스트로 존재한다.
그러나 구조화 지역·연령·신청 기간·접수 상태는 미정이다. 현재 날짜
`2026-08-06`에 신청 가능하다고 단정할 수 없으며, 검색 상위 48건 중에는
장애인 자립지원·한부모가족시설 등 월세와 직접 관련 없는 후보도 포함됐다.

실제 API 모드 Browser에서 exact 문장을 홈 검색으로 입력해 URL 원문 보존,
연령 27세·카테고리 주거·충청남도 천안시 Chip, 48건·3페이지, partial·unknown
경고와 첫 후보 상세·원문 링크를 확인했다. 기존 DTO의 `source_name`과
`collected_at`이 상세 화면에 없던 Release 1 소비 누락은 데이터 출처와
`KST` 수집 시각 표시로 보완했다.

Gate G4 판정은 `blocked`다. confirmed 정책 부재는 DT6 기준의 필수 차단
조건이며, QA smoke·사용성 리뷰·보고서 대조의 독립 증거도 저장소에 없다.
Team Leader의 Browser·E2E 결과로 이 세 역할의 승인을 대신하지 않았다.

## 주요 변경 파일

- `backend/tests/test_postgresql_policy_search_integration.py`
- `frontend/src/pages/user/PolicySearchPage.tsx`
- `frontend/e2e/policy-search-audit.spec.ts`
- `frontend/.gitignore`
- `frontend/src/pages/user/ProgramDetailPage.tsx`
- `frontend/src/utils/policyDisplay.ts`
- `frontend/tests/policyDisplay.test.ts`
- `frontend/tsconfig.test.json`
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
| DT6 exact golden API | 48건, 첫 후보 지역·연령 unknown |
| DT6 월세 단일어+명시 조건 | 3건, partial 3·confirmed 0 |
| DT6 Frontend unit 1·2차 | test 전용 alias 미해석으로 compile 실패 |
| DT6 Frontend 최종 unit | 45건 통과 |
| DT6 Frontend build·lint | 통과 |
| DT6 실제 API Playwright | 10건 통과 |
| DT6 인앱 Browser | exact query 48건·Chip·경고·상세 출처·수집 시각 확인 |

golden query `27세 천안 청년 월세 지원`은 실제 API에서 46건의 후보를
반환했다. 첫 후보 `청년월세 지원사업`은 연령·지역 unknown으로 표시됐고,
Profile의 confirmed match는 0건이다. 실제 적용 가능성을 단정하지 않는다.

`npm ci`는 실행 중 Vite가 native binding을 잡아 첫 시도에 `EPERM`으로
실패했다. 이 작업에서 시작한 Vite process를 종료한 뒤 lockfile 기준 201개
package 설치가 성공했다. `npm audit`은 high 3건을 보고했으며 자동 수정은
범위 밖이라 실행하지 않았다.

## 남은 작업

### Gate G4 차단사항과 재개 조건

- Backend·Team Leader가 일반 term OR 후보 확대와 score 의미를 결정하고 actual
  snapshot 정확도를 재검증한다.
- Data·Team Leader가 confirmed golden 정책 부재를 허용할지, Source 범위를
  추가할지 결정한다. 현재 계획상 결정 전까지 릴리스 차단이다.
- 복지로 지원 내용의 신청기간 텍스트를 구조화 기간·상태로 안전하게 승격할
  수 있는지 Data Source mapping 범위에서 검토한다.
- QA smoke, 사용성 리뷰와 보고서 근거를 독립적으로 확보한 뒤 같은 snapshot과
  exact query로 Gate G4를 다시 판정한다.
- 기존 Starlette deprecation warning 2건과 npm audit high 3건은 별도
  의존성 검토가 필요하다.

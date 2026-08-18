# 5주차 Data·Team Leader 실행 계획

## 계획 정보

- 상태: in-progress (`DTL5-0`~`DTL5-4`, `W5-G1_PASS`; Integration 10
  review admission → Deploy 01 Docker Acceptance 뒤 DTL5-5)
- 대상 Release: `v0.5.0`
- 권장 실행 창: `2026-08-17`~`2026-08-21`
- 실제 시작 SHA: `develop`·`origin/develop`
  `29b2dd5ef596286ec2df1ede48398d94c0d010d7`
- Data Forest: [Data 06 Supplemental Official Policy Ingestion](../develop_plan/data/06_supplemental_official_policy_ingestion.md)
- Integration Forest: [Integration 07 Release 2 Feature Acceptance](../develop_plan/integration/07_release_2_feature_acceptance.md)
- 선행 데이터 Forest: [Integration 10 Review Admission](../develop_plan/integration/10_review_admission_docker_acceptance.md)
- 선행 배포 Forest: [Deploy 01 Docker Acceptance](../develop_plan/deploy/01_docker_acceptance_environment.md)
- 공통 주차 계획: [5주차 Release 2 실행 계획](week_05_release_2.md)
- 현재 Slice: Integration 10 최신 review 재판정·`W5-G1_REVALIDATED`;
  이어서 Deploy 01 동일 snapshot `DOCKER_ACCEPTANCE_PASS`, 그 뒤 DTL5-5

이 문서는 Data 구현과 Team Leader Gate 주관 순서를 정한다. 실제 구현·수집·
테스트 결과는 Data 06과 Integration 07 development note에 기록하며, 계획에
실행하지 않은 결과를 소급해 쓰지 않는다.

## 현재 기준선과 착수 판단

- 4주차는 `W4-G4_MIDPOINT_PASS`이며 `develop` 병합이 완료됐다.
- Migration 기준은 `20260810_0006`, 4주차 실제 DB 기준은 정책 3,269건과
  Data 05 지역정책 109건이다.
- Data 05 `RYP0`~`RYP9`·`RYP-G6`는 completed다.
- Data 06은 `SOP-G5_PASS`로 완료됐으며 승인 Source 5개 actual과 KOSAF 신규
  정책 1건의 DB·API·Browser 인수를 통과했다.
- 독립 사용성 리뷰·QA·보고서 근거 대조는 아직 수행하지 않았다.
- `DTL5-0`에서 같은 기준과 실행 환경을 재검증해 `W5-G0_PASS`로 판정했다.
  `2026-08-18` Backend·Frontend 담당 산출물과 Data 06을 Integration 브랜치에
  통합하고 전체 PostgreSQL·Browser 회귀를 통과해 `W5-G1_PASS`로 판정했다.

## 담당 목표

1. Data 06 후보를 원문·중복·이용 조건 기준으로 정제하고 승인 Source 5개를
   제한 actual한다. 중복 제외 신규 정책 1개 이상을 DB → API → Browser로 인수한다.
2. Backend·Frontend 안정화 결과와 Data 06을 실제 PostgreSQL 기반 하나의
   Release 2 후보로 묶는다.
3. 구현자 자체 테스트와 독립 사용성·QA를 분리하고, 차단 결함을 같은
   시나리오로 재검증한다.
4. 근거가 완전한 `develop`만 `main` PR과 `v0.5.0` tag 후보로 판정한다.

## 담당 Forest와 변경 경계

| 영역 | 담당 범위 | 직접 수정 경계 |
| --- | --- | --- |
| Data 06 | inventory·중복·Source preflight·Adapter·Raw replay·actual 적재 | Data·Collector·fixture·Data 문서 |
| Backend | PostgreSQL·Migration·API·권한·transaction 안정화 | Backend 담당 결과를 인수하고 계약 충돌만 조정 |
| Frontend | actual API·오류 UX·접근성·반응형 안정화 | Frontend 담당 결과를 인수하고 소비 계약만 조정 |
| Integration 07 | 기준선·전체 E2E·결함 triage·W5-G1/G2 | 둘 이상 영역의 검증·문서·Gate |

Data 06 구현 브랜치는 계획된
`feature/data/supplemental-official-policy-ingestion` 한 개를 사용하며 Source별
브랜치를 늘리지 않는다. Integration 07용 `integration` domain은 실제 4주차
브랜치 선례와 현재 거버넌스 문서가 일치하지 않으므로, 통합 브랜치 생성은
사용자 승인 뒤 별도로 수행한다.

## 전체 실행 순서

```text
DTL5-0 W5-G0 기준선·환경·증거 계약
  ├→ DTL5-1 Data 06 SOP0~SOP2
  ├→ Backend W5-B1 안정화 회귀
  └→ Frontend W5-F1 안정화 회귀
  → DTL5-2 Data 06 SOP3 Adapter·offline replay
  → DTL5-3 Data 06 SOP4~SOP5 actual·SOP-G5
  → DTL5-4 Data 06 포함 전체 actual E2E·W5-G1
  → Integration 10 review admission·DB 재인수·W5-G1_REVALIDATED
  → Deploy 01 동일 snapshot·Docker Acceptance
  → DTL5-5 독립 사용성·QA와 결함 triage
  → 영역별 수정·자체 재검증
  → DTL5-6 독립 재검증·문서 대조·W5-G2
```

DTL5-1과 Backend·Frontend 안정화는 W5-G0 뒤 병렬로 진행한다. 독립 리뷰와
QA는 DTL5-4에서 W5-G1을 통과하고 Integration 10 `W5-G1_REVALIDATED`와
Deploy 01 `DOCKER_ACCEPTANCE_PASS`를 통과하기 전에는 시작하지 않는다. 기존
`W5-G1_PASS`는 당시 인수 기록으로 유지하며 새 DB 수치를 의미하지 않는다.

## Slice DTL5-0 - W5-G0 기준선 고정

상태: completed (`2026-08-17`, `W5-G0_PASS`). 실제 수치와 첫 실패·보정은
[Integration 07 개발 기록](../development_notes/integration/release_2_feature_acceptance.md)에
둔다.

### 목적

4주차 병합 결과를 5주차가 재현할 공통 입력으로 고정한다.

### 수행 작업

- `develop`·`origin/develop` SHA와 clean worktree 확인
- Migration 단일 head `20260810_0006` 확인
- 실제 DB 기준 정책 3,269건·지역정책 109건과 Source별 기준 수치 확인
- local Runtime·FastAPI·React actual API mode와 지원 Browser 확인
- Data·Backend·Frontend 테스트 명령과 PostgreSQL `_test` DB 경계 확인
- 사용성 리뷰어·QA·보고서 역할과 증거·결함 양식 확정
- 비밀·Runtime Raw·로그·DB 파일 Git 비추적 확인

### 완료 기준

- 위 값이 재확인되고 기본 기능 미완료가 0건이면 `W5-G0_PASS`
- 값 차이는 데이터 drift, 환경 차이, 회귀로 분류하고 원인 확인 전에는 차단
- 시작 SHA와 실제 실행 결과는 Integration 07 development note에 기록

## Slice DTL5-1 - Data 06 SOP0~SOP2

상태: completed (`2026-08-17`, `SOP-G0_PASS`~`SOP-G2_PASS`). 후보 60개 중
exact duplicate 26·review 11·잠정 신규 19·비교 제외 4로 판정했고, 공식
Source 5개를 승인·1개를 robots 차단·9개를 제외했다. 다섯 번째 모두의카드는
보완 preflight에서 승인했지만 actual 중복 review로 DB 적재하지 않았다. 상세 근거는
[Data 06 개발 기록](../development_notes/data/supplemental_official_policy_ingestion.md)에
둔다.

### 목적

구현 비용을 쓰기 전에 후보 오류·기존 정책 중복·수집 불가 Source를 제거한다.

### Data 수행 작업

- XLSX URL 후보 64행의 exact 반복·제목/URL 충돌·문구 불일치 격리
- 온통청년·복지로 직접 URL 11행과 기존 DB·snapshot 선행 중복 감사
- 독립 도메인 후보를 Source군과 정책 후보로 분리
- 운영 주체·robots·약관·라이선스·목록/상세·identity·요청 예산 preflight
- Source별 `approved`·`blocked`·`rejected`와 재개 조건 기록

### Team Leader Gate

- 근거 없는 필요서류·신청 상태는 accepted 후보로 승격하지 않음
- 목록·상세 allowlist와 요청 예산이 없는 Source는 Adapter 구현 금지
- `SOP-G0`~`SOP-G2` 통과 뒤에만 DTL5-2 해제

## Slice DTL5-2 - Data 06 SOP3 Adapter·판정 fixture

상태: 완료 (`SOP-G3_PASS`, 2026-08-17). 승인 5개 Source의 stable identity·
Source별 locator·offline Raw replay를 구현했고, accepted 이후에도 기존 aggregator
중복 기준선이 없으면 Policy row를 만들지 않는 경계를 확인했다.

### 목적

승인 Source를 기존 공통 파이프라인에 Source별 경계를 유지해 연결한다.

### 수행 작업

- stable `(source_id, external_id)`·canonical URL·pagination 종료 조건
- 목록·상세·누락·drift·HTTP 실패 최소 fixture
- 청년 대상·현재 신청·기관·조건·서류 evidence mapping
- exact duplicate·fingerprint review·마감·근거 부족 판정
- 외부 요청 없는 동일 Raw offline replay와 결정성 검증

### 완료 기준

- Source별 locator가 공통 Normalizer에 누출되지 않음
- duplicate·review·closed·failed가 accepted Policy row를 만들지 않음
- 단위·계약 회귀와 `SOP-G3` 통과

## Slice DTL5-3 - Data 06 SOP4~SOP5 actual

상태: completed (`SOP-G4_PASS`·`SOP-G5_PASS`, 2026-08-17). 모두의카드까지
다섯 Source의 제한 actual을 완료했고, 재승인 기준에 따라 한국장학재단 신규
정책 1개를 DB·API·Browser에 연결했다. 비accepted 결과는 무적재이며 전체
Data·Backend 회귀와 문서 대조를 통과해 DTL5-4로 인계한다.

### 목적

승인 Source 5개를 실제 제한 수집하고, 중복 제외 신규 정책 1개 이상을 안전하게
적재·재실행한다.

### 수행 작업

- 우선 Source별 제한 목록·상세 요청과 원문 수동 대조
- accepted·duplicate·review·closed·failed 수치와 lineage 확인
- 최초 insert와 동일 snapshot `unchanged`, 변경 `updated`, prune 안전성 확인
- 모든 계획 Source군의 `implemented`·`blocked`·`rejected` 최종 상태 확정
- Data 05·온통청년·복지로·Release 1 golden 회귀

### 완료 기준

- 승인 Source 5개 제한 actual·offline replay 완료
- 중복 제외 신규 정책 1개 이상이 DB·API·actual Browser에 연결됨
- duplicate·review·closed·failed Policy row 0건
- 모든 승인 Source의 제한 actual·replay·`SOP-G5` 통과
- 최소 기준 미달이면 범위를 조용히 줄이지 않고 `W5-G1_BLOCKED` 또는 계획
  재승인 요청

## Slice DTL5-4 - 전체 actual E2E와 W5-G1

### E2E 흐름

1. Data 06 공식 원문 → Raw·판정 → PostgreSQL → 검색·상세 → Browser
2. 관리자 PIN → CollectionRun → 수동 실행 → 정책 데이터 → 로그·archive 감사
3. 사용자 조건 → 추천 이유·미확정 → 상세 근거 → 즐겨찾기·D-Day·알림·`.ics`
4. Data 05 지역 검색과 Release 1 golden 검색·상세 회귀

### 완료 기준

- Data·Backend·Frontend 담당자 전체 회귀 통과
- Data 05·06 lineage와 사용자 검색 노출 대조
- 실제 PostgreSQL·FastAPI·React 핵심 흐름 통과
- 알려진 제약·환경·독립 시나리오 인계가 완전하면 `W5-G1_PASS`

상태: completed (`2026-08-18`, `W5-G1_PASS`). Backend `da20d9c`의 최종
tree는 비밀 포함 과거 이력을 제외한 `babb432` squash로, Frontend `d19fd02`는
`792320c` merge로 통합했다. actual fixture·stale assertion 보정 `1019fda` 뒤
Data `334`·172 subtests, Backend PostgreSQL `187`, Frontend unit `216`·lint·
build, Mock Browser `80 passed / 14 skipped`, actual 4-spec `36 passed / 8 skipped`,
종단 actual acceptance `3 passed`를 확인했다. 실제 정책은 3,270건·지역 109건·
KOSAF 1건이다. 노출된 로컬 DB 자격증명 교체 확인은 `W5-G2` 선행 조치로
유지한다.

## Slice DTL5-5 - 독립 사용성·QA와 결함 triage

### 독립 검증

- 사용성 리뷰어는 검색·상세·추천·저장·알림·캘린더와 관리자 흐름을 수행
- QA는 기능·통합·회귀·경계·권한·실패·접근성·반응형을 탐색
- 보고서 담당은 화면·테스트·DB 통계·미실행 항목의 출처를 대조

### 결함 판정

| 등급 | 예시 | Release 처리 |
| --- | --- | --- |
| blocker | 인증 우회, 비밀 노출, 데이터 손실, Migration 실패, 핵심 E2E 실패, Data 06 최소 기준 미달 | 수정·독립 재검증 전 W5-G2 금지 |
| high | 주요 흐름을 우회 없이는 완료 불가, 잘못된 정책·추천·자격 표시 | 원칙적으로 수정 후 재검증 |
| low | 기능을 막지 않는 문구·레이아웃·낮은 위험 UX | 근거와 영향이 있을 때만 알려진 제약 후보 |

각 결함은 재현 조건·기대/실제·담당·수정 SHA·자체/독립 재검증을 가진다.

## Slice DTL5-6 - 수정본 재검증과 W5-G2

### 수행 작업

- blocker·승인 high 결함을 최초 시나리오와 같은 환경에서 독립 재검증
- Data·Backend·Frontend 핵심 회귀와 actual Browser 재실행
- Release 2 완료 조건, development notes, API·데이터·운영 문서 대조
- CHANGELOG와 알려진 제약을 실제 기능·검증 결과에 맞게 갱신
- 비밀·Runtime·로그·DB·Browser 산출물 비추적과 문서 링크 검사

### 판정

- 모든 완료 조건 충족: `W5-G2_PASS`
- 낮은 위험 제약만 남고 Release 조건을 충족: `W5-G2_CONDITIONAL`
- blocker 또는 필수 검증 미수행: `W5-G2_BLOCKED`

`PASS`인 검증 SHA만 `main` PR과 `v0.5.0` tag 후보로 지정한다. 이 Slice에서
직접 merge·tag·push하지 않으며 사용자의 별도 요청을 따른다.

## 다른 담당자에게 요청할 산출물

### Backend

- Migration head·upgrade/rollback·데이터 유지와 transaction 실패 복구
- PIN session·권한·rate limit, CollectionRun·수동 실행·stale 회귀
- 정책 검색·상세·추천·관리자 정책·구조화 로그 API 회귀
- `401`·`403`·`404`·`409`·`422`·`500`, 보안·성능 결과

### Frontend

- actual API 검색·상세·추천과 지역·Data 06 신규 정책 Browser 결과
- 로그인·만료·로그아웃, 관리자 정책·CollectionRun·로그 UI 결과
- 즐겨찾기·D-Day·알림·`.ics`, loading·empty·partial·error 결과
- unit·lint·build·Mock·actual Browser·접근성·모바일 결과

### 독립 역할

- 사용성 리뷰어: 관찰 기록과 동일 시나리오 재확인
- QA: 전체 요구사항 추적과 결함·수정본 독립 재검증
- 보고서: 근거 출처, 미실행 검증, Release 2 결과 대조

## 테스트와 검증 명령

실제 Forest의 최신 명령을 우선하며 실행하지 않은 명령을 통과로 기록하지 않는다.

### Data·Backend·PostgreSQL

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
$env:TEST_DATABASE_URL = '<dedicated-postgresql-test-url>'
.\.venv\Scripts\python.exe -B -m pytest backend/tests tests/integration -q
```

`TEST_DATABASE_URL`은 `_test` 전용 DB만 사용하고 비밀은 임시 `PGPASSFILE`로
전달한다. 실제 서비스 DB를 테스트 정리 대상으로 사용하지 않는다.

### Frontend

```powershell
Set-Location frontend
npm run test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
```

Mock과 actual API 결과를 분리하고 actual 전용 skip을 통과로 세지 않는다.

### 문서·비추적

```powershell
.\.venv\Scripts\python.exe -B scripts\validate_docs.py
git diff --check
git status --short
```

## 완료 체크리스트

- [x] DTL5-0·`W5-G0_PASS`
- [x] DTL5-1 Data 06 `SOP-G0`~`SOP-G2`
- [x] DTL5-2 Data 06 `SOP-G3`
- [x] DTL5-3 Data 06 actual과 `SOP-G4_PASS`·`SOP-G5_PASS`
- [x] Backend·Frontend 담당자 산출물과 전체 안정화 회귀 인수
- [x] DTL5-4 Backend·Frontend·Data 06 통합 actual E2E·`W5-G1_PASS`
- [ ] Integration 10 `REVIEW_ADMISSION_PASS`·`W5-G1_REVALIDATED`
- [ ] Deploy 01 `DOCKER_ACCEPTANCE_PASS`·동일 snapshot 인계
- [ ] DTL5-5 독립 사용성·QA와 결함 triage
- [ ] 승인 결함 수정·자체 및 독립 재검증
- [ ] 보고서 근거·미실행 검증 대조
- [ ] DTL5-6 문서·비추적·전체 회귀와 `W5-G2` 판정
- [ ] `PASS`일 때만 `main` PR·`v0.5.0` tag 후보 지정

## 관련 문서

- [5주차 Release 2 실행 계획](week_05_release_2.md)
- [4주차 Data·Team Leader 실행 결과](week_04_data_team_leader.md)
- [Data 06 계획](../develop_plan/data/06_supplemental_official_policy_ingestion.md)
- [Review Admission](../develop_plan/integration/10_review_admission_docker_acceptance.md)
- [Docker Acceptance](../develop_plan/deploy/01_docker_acceptance_environment.md)
- [Integration 07 계획](../develop_plan/integration/07_release_2_feature_acceptance.md)
- [Release와 Milestone 계획](../develop_plan/release_roadmap.md)
- [역할과 책임](../../governance/role_assignment.md)

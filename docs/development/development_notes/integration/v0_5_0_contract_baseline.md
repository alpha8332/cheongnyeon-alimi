# Integration 05 v0.5.0 Contract Baseline

## 작업 정보

- 기간: `2026-08-10`
- 상태: completed
- 담당 영역: Data, Team Leader - Integration
- 현재 작업 브랜치: `docs/docs/v0-5-contract-baseline`
- 권장 Forest 브랜치: `docs/docs/v0-5-contract-baseline`
- merge target: `develop`
- 시작 SHA: `e5ff8c81e0e902723c5b79dee1267be7e5e2e66c`
- 계획: [Integration 05 개발 계획](../../develop_plan/integration/05_v0_5_0_contract_baseline.md)
- 주차 계획: [4주차 Data·Team Leader 실행 계획](../../weekly_plan/week_04_data_team_leader.md)

## 목적

4주차 구현 전에 실제 Release 1 기준선과 로컬 실행 환경을 확인하고, 각 Forest의
구현·소비 검토·actual E2E 책임과 merge 경계를 고정하고 Team Leader가
`W4-G0_APPROVED`를 판정한 근거를 남긴다.

## Forest 범위

- 사용자 저장·관리자 인증·웹 Source·자격요건·추천·날짜·수동 실행·품질·
  관리자 데이터·로그 계약의 공동 기준선
- Data·Backend·Frontend 소비 초안 대조와 `W4-G0` 판정
- 승인된 계약의 실제 기능 구현은 후속 Forest 범위

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| DTL4-0 | 완료 | 시작 SHA·환경·Forest 소유·merge target과 비추적 경계 확인 |
| DTL4-1 / C0~C4 | 완료 | Data inventory·Backend 대조·웹 Source 경계 승인, `W4-G0_APPROVED` |

## 구현 내용

### DTL4-0 시작 기준

- 작업 시작 시 `develop`은 `origin/develop`과 같은
  `e5ff8c81e0e902723c5b79dee1267be7e5e2e66c`였고 작업 트리는 깨끗했다.
- `main`·`origin/main`·`v0.1.0`은
  `2b33ed7d8d4e281487b5734bd88cfd73b6d60175`로 일치해 Release 1 publication을
  확인했다.
- 브랜치는 사용자 지시대로 생성하지 않았다. Integration 05의 독립 목표와
  완료 기준에는 계획의 `docs/docs/v0-5-contract-baseline`을 사용하고
  `develop`로 병합한다.
- API key 파일은 저장소 밖 `C:\git\APIkey.txt`에 존재하고 현재 사용자에게
  읽기 권한이 있음을 파일 open만으로 확인했다. 값은 읽거나 출력하지 않았다.
- 기본 `pgpass.conf`, `PGPASSFILE`, `DATABASE_URL`, `TEST_DATABASE_URL`은 현재
  환경에 없다. 따라서 PostgreSQL 서비스 readiness와 인증 가능한 전용 test
  DB 실행 가능 여부를 구분한다.

### 실행 환경과 Release 1 재사용성

| 항목 | 확인 결과 | DTL4-1 이후 사용 경계 |
| --- | --- | --- |
| PostgreSQL | `127.0.0.1:5432` TCP와 PostgreSQL 18 `pg_isready` 응답 성공 | 인증과 `_test` 전용 DB는 별도 credential 주입 뒤 검증 |
| Python | `.venv` Python `3.11.9` 실행, `uv` 없음 | 기존 `.venv` 사용, 새 설치 없음 |
| Node | Node `v24.18.0`, npm `11.16.0` 실행 | Frontend 기존 scripts 사용 |
| Browser | 설치된 Playwright Chromium headless launch 성공 | actual E2E는 해당 Slice에서 별도 실행 |
| API 자료 | `opensource_plan/api_info` 3개 자료와 외부 API key 파일 존재 | Source 요청 전 사용법·keyword와 호출 예산 확인 |
| Release Raw | 승인 manifest 2개와 Runtime Raw 존재 | 외부 API·DB 없이 고정 snapshot replay 가능 |
| 비추적 경계 | `runtime/raw`, DB 파일 제외 확인; 누락된 `runtime/html`, `runtime/logs` 제외 규칙 추가 | Raw·HTML·로그·DB 산출물 커밋 금지 |

고정 snapshot strict offline profile은 3,156건을 수용하고 invalid 0건,
신청기간 safety `passed=true`를 반환했다. Source별 결과는 온통청년 2,695건,
복지로 461건으로 Release 1 기준선과 일치했다. 따라서 Data 02 Raw·profile
기준선은 DTL4-1 inventory에 재사용할 수 있다. PostgreSQL Runtime DB의 현재
row는 credential 미주입으로 조회하지 않았으며 재사용 가능으로 단정하지 않는다.

### Forest 책임과 병합 경계

| Forest | 구현 주 담당 | 소비 검토 | 브랜치와 merge target | 완료 기준 |
| --- | --- | --- | --- | --- |
| Integration 05 | Team Leader, Data 근거 | Backend·Frontend | `docs/docs/v0-5-contract-baseline` → `develop` | `W4-G0_APPROVED` |
| Data 03 | Data | Backend 05·Team Leader | `feature/data/recurrent-quality-operations` → `develop` | 반복·변경·중복·실패·품질 통계 검증 |
| Data 04 | Data | Backend·Frontend·Integration 08 | `feature/data/public-web-policy-source` → `develop` | 공식 Source actual 수집·DB 적재 |
| Integration 08 | Data·Backend·Frontend 영역별 구현 | 상호 소비 검토·Team Leader | Data 04 기반 뒤 영역별 브랜치 → `develop` | evidence → 상세 API → UI E2E |
| Backend 04·05 | Backend | Frontend·Data·Team Leader | Backend Forest 브랜치 → `develop` | 인증·CollectionRun 계약과 PostgreSQL 검증 |
| Frontend 03 | Frontend | Backend·Team Leader | 관리자 Forest 브랜치 → `develop` | PIN·관리자 actual API 소비 |
| Integration 09 | Backend·Frontend | Data 의미·Team Leader 보안 | 영역별 observability 브랜치 → `develop` | 읽기 전용 데이터·로그·감사 E2E |
| Integration 06 | Backend·Frontend | Data·Team Leader | 영역별 recommendation 브랜치 → `develop` | 결정적 추천·이유·미확정 E2E |
| Frontend 05 | Frontend | Team Leader | `feature/frontend/user-service-features` → `develop` | 저장·D-Day·알림·`.ics` Browser 검증 |
| Integration 07 | Team Leader | 전 담당 | cross-area domain 합의 전 생성 금지 | W4-G1~G4와 midpoint 근거 |

Schema·Migration·Adapter 겹침은 Data 03이 CollectionRun 품질 집계 의미를,
Data 04가 웹 Source Adapter·Raw HTML·공통 정규화 연결을 소유한다. Integration
08의 Data evidence 구조는 DTL4-1에서 계약을 승인한 뒤 Data 04 기반 위에서
추가하며, 같은 Schema나 Migration을 병렬 브랜치에서 동시에 수정하지 않는다.
OpenAPI는 Backend, TypeScript·Mock은 Frontend가 소유하고 Data는 field 의미와
provenance를 검토한다.

### Backend 선행 구현 처리

Backend 담당 결과는 별도 원격 브랜치
`origin/feature/backend/admin-access-control`의
`f7ffca4254a52cc94666a575567cbf73b7cb92de`까지 진행돼 있다. 여기에는 PIN
session·token·rate limit·관리자 dependency와 계약·테스트가 포함되지만,
Integration 05 승인 전에는 실제 OpenAPI 후보로만 대조했다. Team Leader의
W4-G0 승인 뒤에도 해당 구현을 완료 기능으로 소급하지 않으며 승인 계약과의
적합성은 W4-G1에서 확인한다.

Backend에는 이 구현과 함께 CollectionRun·관리자 데이터·로그·자격요건·추천
OpenAPI를, Frontend에는 PIN·관리자·핵심 조건·추천·로컬 기능 TypeScript·Mock을
W4-G1 소비 검토 입력으로 요구한다. FE 미착수 상태를 승인 증거로 기록하지
않았으며, 구현 차이는 계약 변경 없이 임의 수용하지 않는다.

### DTL4-1 Data inventory

- 현재 Policy upsert는 identity·immutable field 외 모든 write field를 mutable로
  비교한다. `collected_at`과 provenance도 포함돼 재수집 metadata만 달라진
  동일 policy가 `updated`로 집계될 수 있다.
- CollectionRun은 requested·Raw·extracted·accepted·partial·invalid·inserted·
  updated·unchanged·skipped·failed count를 저장하지만 duplicate·rejected 전용
  count는 없다.
- 현재 Normalized Schema는 `eligibility_text`와 required·preferred·excluded
  string 배열을 제공하지만 항목별 evidence·제출서류·coverage 구조가 없다.
- Release 1 offline replay에서 온통청년 2,695건 중 `eligibility_text` 1,024건,
  복지로 461건 중 5건만 존재했다. 두 Source 모두 required·preferred·excluded,
  education·employment 구조화 배열은 0건이었다.
- 기존 field를 제거하거나 의미를 바꾸지 않고 `eligibility_summary` 호환 확장
  후보와 business 비교 field 분리를 Integration 05 계획에 기록했다.

### DTL4-1 Backend 소비 대조

`f7ffca4254a52cc94666a575567cbf73b7cb92de`의 실제 문서·Schema·service·endpoint·
dependency를 정적으로 대조했다. 4자리 PIN, session 응답, 60분 token, role,
오류 상태와 progressive cooldown은 계획 후보와 일치한다.

다음 차이는 Backend action item으로 분류했다.

- 기본 `0000` 허용이 localhost host·bind가 아니라 `ENVIRONMENT` 문자열에만
  의존한다.
- production에서도 `ADMIN_TOKEN_SECRET`이 없으면 기본값이 있는 `SECRET_KEY`로
  fallback할 수 있다.
- process-local rate limit은 단일 process 로컬·시연 기준으로만 유효하고
  다중 worker·reverse proxy 보장은 하지 않는다.

Backend 브랜치명이나 W4-G0 전 구현 시작 자체는 계약 차이로 분류하지 않았다.

### DTL4-1 공식 웹 Source preflight

`2026-08-10`에 [천안청년센터 이음 공지 674번](https://www.ch2030youth.kr/bbs/board.php?bo_table=notice&wr_id=674)을
익명 공개 화면으로 확인했다.

- Source ID `cheonan-youthcenter-web`, identity `notice:674`로 확정
- 제목·게시일·대상·지원 내용·제출서류·유의사항이 공개 정적 본문에 존재
- 신청 링크는 회원가입·로그인이 필요하므로 crawler 추적 대상에서 제외
- 첨부·이미지·이메일·전화번호·개인정보를 추출·저장하지 않음
- 목록 1회·승인 상세 1건, 동시 요청 1개·최소 2초 간격만 승인
- `/robots.txt`는 directive가 아닌 404 페이지를 반환하고 별도 이용약관은
  찾지 못했으며 footer는 `all rights reserved`를 표시
- actual HTML은 Runtime 전용, Git에는 합성·최소 구조 Fixture만 허용

게시일은 `2026-07-24`지만 본문 신청기간은
`2026-04-22`~`2026-05-06 23:00`이고 제목에는 “곧 마감”이 있어 충돌한다.
표본은 `data_quality_status=partial`, 신청 상태 `unknown`으로 승인했으며
Extractor가 현재 신청 가능 여부를 추정하거나 원문을 덮어쓰지 않도록 했다.

### DTL4-1 Gate 상태

Team Leader가 `W4-G0_APPROVED`로 판정했다. FE TypeScript·Mock 미착수와 Backend
localhost `0000`·별도 token secret 차이는 승인 계약의 미확정이 아니라
`W4-G1` 구현 적합성 항목으로 이관했다. 이에 DTL4-2A·3A·4A 기반 구현을
해제하며 실제 Schema·Migration·actual 구현은 각 후속 Forest에서 수행한다.

## 주요 변경 파일

- `.gitignore`
- `docs/development/develop_plan/integration/05_v0_5_0_contract_baseline.md`
- `docs/development/weekly_plan/week_04_data_team_leader.md`
- `docs/development/development_notes/integration/v0_5_0_contract_baseline.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`
- `docs/data/data_sources.md`
- `docs/data/collection_policy.md`
- `docs/data/source_profiles.md`
- `docs/development/develop_plan/data/04_public_https_policy_ingestion.md`
- `CHANGELOG.md`

## 설계 결정

- DTL4-0은 환경·책임 경계만 완료하고 계약 승인이나 기능 구현을 선행하지 않는다.
- Release 1 offline snapshot은 재사용하되 인증하지 않은 Runtime PostgreSQL의
  현재 상태를 추정하지 않는다.
- 외부 API key·pgpass 값은 문서·명령 출력·Git에 포함하지 않는다.
- BE 선행 구현은 되돌리거나 완료 기능으로 소급하지 않고 W4-G1에서 적합성을
  검토한다.
- FE 사전 구현 없이 Team Leader가 W4-G0을 승인하고 FE TypeScript·Mock parity는
  W4-G1 완료 조건으로 이관한다.
- 천안청년센터 원문 HTML·이미지는 Git에 재배포하지 않고 공개 사실과 최소
  합성 Fixture만 사용한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Git Release·branch·worktree 대조 | 통과: Release refs 일치, 시작 worktree 변경 0건 |
| PostgreSQL readiness | 통과: `127.0.0.1:5432` accepting connections |
| PostgreSQL 인증·전용 test DB | 미실행: `pgpass`·`TEST_DATABASE_URL` 미주입 |
| Release 1 strict offline profile | 통과: accepted 3,156, invalid 0, period safety pass |
| Python·Node 실행 | 통과: Python 3.11.9, Node 24.18.0, npm 11.16.0 |
| Browser 실행 | 통과: Playwright Chromium headless launch·close |
| API key·자료 경계 | 통과: 존재·read access만 확인, 값 미열람 |
| Release profile 집중 단위 테스트 | 11건 통과 |
| Data Integration pytest | 4건 skip: `TEST_DATABASE_URL` 미주입, 기존 warning 1건 |
| 문서 검증 | 통과: `scripts/validate_docs.py` |
| diff 검사 | 통과: `git diff --check` |
| DTL4-1 Release snapshot coverage replay | 통과: 3,156건 offline, eligibility field 존재 건수 집계 |
| DTL4-1 runtime replay·release profile 집중 unittest | 16건 통과 |
| DTL4-1 Data Integration pytest | 4건 skip: `TEST_DATABASE_URL` 미주입, 기존 warning 1건 |
| DTL4-1 Backend contract static review | 완료: BE commit의 문서·Schema·service·endpoint·dependency 대조 |
| DTL4-1 공식 웹 Source preflight | 완료: 공지 674번 공개 사실·robots 404·이용 조건·요청/보존 경계 확인 |
| DTL4-1 Frontend 소비 검토 | 미실행: FE 미착수, W4-G1 적합성 확인으로 이관 |
| DTL4-1 Gate 판정 | `W4-G0_APPROVED`: Team Leader 승인 |

## 남은 작업

- W4-G1에서 FE TypeScript·Mock을 전달받아 승인 계약과 대조한다.
- Backend localhost `0000`·production 별도 token secret action item을
  W4-G1 Backend 결과와 다시 대조한다.
- Data 04는 천안청년센터 승인 경계 안에서 합성 Fixture·Adapter·제한 actual
  수집을 구현하고 착수 시 DOM·이용 조건을 재확인한다.
- PostgreSQL 통합 검증 전에 별도 `_test` DB용 credential과 `TEST_DATABASE_URL`
  을 명시적으로 주입한다. 준비 전 skip을 성공으로 간주하지 않는다.

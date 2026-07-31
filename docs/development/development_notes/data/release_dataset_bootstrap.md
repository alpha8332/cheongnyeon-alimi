# Release Dataset Bootstrap Forest 개발 기록

## 작업 정보

- 작업일: 2026-07-31
- 담당 영역: Data, Team Leader 시작 조정
- 상태: in-progress
- 브랜치: `feature/data/release-dataset-bootstrap`
- 기준 `develop` SHA: `fb6402d1793dbd9b4999d1a004fddf695f2d8bde`
- 관련 계획:
  [Release Dataset Bootstrap Forest](../../develop_plan/data/02_release_dataset_bootstrap.md)
- 현재 Slice: DT1 completed, next DT2

## 목적

3주차 실데이터 작업을 시작하기 전에 2주차 병합 기준, Source 파이프라인,
비밀 주입, Runtime Raw와 PostgreSQL 실행 경계를 실제 저장소와 로컬
환경에서 확인한다.

## Forest 범위

이 기록은 Data 02의 DT0부터 DT4까지 실제 구현·검증 결과를 누적한다.
Backend 검색 구현, Frontend UI와 Integration 03 종단 인수 결과는 각 담당
Forest 기록에 남긴다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| DT0 | completed | Git·Source·비밀·Runtime·PostgreSQL 인증·Migration과 테스트 확인 |
| DT1 | completed | 두 Source 실호출·분포·partial 원인·릴리스 범위 초안 확인 |
| DT2 | pending | 지역·연령·상태·partial 계약과 Backend·Frontend 초안 대기 |
| DT3 | pending | 승인 수집 범위와 인증 가능한 Runtime DB 대기 |
| DT4 | pending | 실제 snapshot 적재와 G1 대기 |

## 구현 내용

### DT0 - Git과 2주차 기준선

- 작업 시작 시 브랜치는 `feature/data/release-dataset-bootstrap`이고 작업
  트리는 clean이었다.
- `HEAD`, 로컬 `develop`과 `origin/develop`은 모두
  `fb6402d1793dbd9b4999d1a004fddf695f2d8bde`였다.
- `2fe6918`에서 2주차 hardening 결과가 `develop`에 병합됐고 Backend 03,
  Frontend 02, Data 01과 Integration 02의 완료 계획·개발 기록을 확인했다.
- 현재 브랜치는 최신 `develop`에서 시작했고, Data domain을 실데이터
  bootstrap·품질 관리 범위로 명시한 브랜치 정책과 일치한다.

### DT0 - Data 실행 경계

- 등록 Source는 `youthcenter-api`와
  `bokjiro-central-welfare-api`다.
- 두 Source는 Collector → Runtime Raw → Source Extractor → 공통
  Normalizer·Validator 경계를 사용한다.
- 저장된 Runtime Raw의 PostgreSQL 재처리는
  `scripts/import_runtime_data.py`가 담당하고 기본 root는 `runtime/raw`다.
- `runtime/raw`는 Git 제외 대상이며 작업 시점에는 아직 존재하지 않았다.
  DT0 확인만을 위해 빈 디렉터리를 만들지 않았다.

### DT0 - 비밀 주입

- `C:\git\APIkey.txt`가 저장소 밖의 일반 파일로 존재함을 확인했다.
- 파일에는 온통청년과 복지로·공공데이터 Source에 대응하는 두 개의
  레이블된 항목이 있다. 값·길이·query와 payload는 출력하거나 기록하지
  않았다.
- 각 항목을 현재 process의 `YOUTHCENTER_API_KEY`와 `BOKJIRO_API_KEY`로
  매핑하고 `collectors.config.required_secret()` 검증을 통과했다.
- 검증 후 두 환경변수를 즉시 제거했다. 외부 API는 호출하지 않았다.
- 로컬 `.env`는 없고 작업 시작 process에도 두 API 환경변수는 설정되어
  있지 않았다. DT1 실제 호출은 같은 process에 명시적으로 주입해야 한다.

### DT0 - PostgreSQL과 Python 환경

- Windows `.venv`는 Python 3.11.9이며 저장소가 요구하는 SQLAlchemy,
  Alembic, `psycopg2-binary`와 pytest가 설치되어 있다.
- 저장소는 `psycopg`가 아니라 `psycopg2-binary`를 사용한다. 추가 패키지를
  설치하지 않았다.
- PostgreSQL 18 서비스 `postgresql-x64-18`은 실행 중이고
  `localhost:5432`에서 연결을 받고 있다.
- 코드의 Alembic head는 `20260730_0003`이다.
- 작업 시작 시 로컬 `.env`, `DATABASE_URL`, `TEST_DATABASE_URL`과
  `PGPASSFILE`이 없었으며 `pg_hba.conf`는 local·loopback 접속에
  `scram-sha-256` 인증을 요구했다.
- 비밀번호 없는 `psql` 인증은 예상대로 `no password supplied`로 실패했다.
  이후 사용자가 현재 Windows 사용자만 읽을 수 있는 임시 pgpass를 준비했고,
  비밀번호 없는 URL로 Runtime·테스트 DB 직접 인증에 성공했다.
- 기본 예시 `DATABASE_URL` 접속도 인증되지 않았으며 Windows의 로캘된
  PostgreSQL 오류를 psycopg2가 해석하는 과정에서 `UnicodeDecodeError`가
  발생했다. 포트 수신 성공을 DB 준비 완료로 기록하지 않는다.
- Runtime DB `cheongnyeon_alimi`는 빈 DB에서 Alembic
  `20260730_0003` head까지 upgrade했다. 적용 직후와 테스트 후 정책 row는
  모두 0건이어서 테스트 데이터가 Runtime DB에 들어가지 않았다.
- 전용 테스트 DB `cheongnyeon_alimi_test`를
  `TEST_DATABASE_URL`로 사용했다. 첫 테스트 시작 전에는 이전 검증의
  `20260730_0002`와 Seed 4건이 남아 있었다.

### DT0 - 담당 Forest와 증거 위치

| 책임 | 계획·기록 위치 | DT0 판정 |
| --- | --- | --- |
| Data 02 | `develop_plan/data/02_release_dataset_bootstrap.md`, 이 기록 | 생성·진행 중 |
| Backend 06 | `develop_plan/backend/06_policy_search.md`, 대응 Backend 개발 기록 | Backend 담당이 구현 전 생성 필요 |
| Frontend 04 | `develop_plan/frontend/04_policy_search.md`, 대응 Frontend 개발 기록 | Frontend 담당이 구현 전 생성 필요 |
| Integration 03 | `develop_plan/integration/03_release_1_acceptance.md`, 대응 Integration 개발 기록 | Team Leader가 DT5 전 생성 필요 |
| 보고서 | `docs/contest/`의 Release 1 제출 근거 | 실제 증거가 생길 때 작성 |
| 사용성 리뷰·QA | Integration 03 개발 기록의 독립 검증 절 | 시나리오·결함이 생길 때 기록 |

Backend는 자연어 해석·검색 계약과 테스트 골격, Frontend는 Backend 해석
조건·검색 이유 UI prototype을 DT1과 병렬로 준비할 수 있다. 각 담당자의
실제 착수와 완료를 이 Data 기록에서 대신 승인하지 않는다.

### DT1 - 호출 예산과 실제 수집

2026-07-31 실제 preflight는 재시도 없이 다음 예산으로 실행했다.
인증키는 저장소 밖 파일에서 현재 process의 Source별 환경변수로만
주입했고 실행 직후 제거했다. 요청 URI, query와 Raw payload는 출력하지
않았다.

| Source | page·limit | 목록 요청 | 상세 요청 | 총 요청 |
| --- | --- | ---: | ---: | ---: |
| 온통청년 | 1·10 | 1 | 0 | 1 |
| 복지로 | 1·10 | 1 | 3 | 4 |
| 합계 | - | 2 | 3 | 5 |

timeout은 20초, 재시도는 0회, 요청 간격은 1초로 제한했다. 두 Source 모두
정상 응답했고 수집 실패나 재시도는 없었다. Runtime Raw는
`runtime/raw`에 저장했으며 Git ignore 적용을 다시 확인했다.

| Source | 목록 응답 | 목록 항목 | 상세 응답 | Raw 합계 | 추출·수용 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 온통청년 | 1 | 10 | 0 | 11 | 10 |
| 복지로 | 1 | 10 | 3 | 14 | 10 |

온통청년은 `total_count=2696`, 복지로는 `total_count=461`을 보고했다.
이 값은 수집 시점의 Source 메타데이터이며 Release DB 적재 건수가 아니다.

### DT1 - 품질과 검색 필드 분포

| 항목 | 온통청년 10건 | 복지로 10건 |
| --- | ---: | ---: |
| `valid` / `partial` / `invalid` | 0 / 10 / 0 | 0 / 10 / 0 |
| 지역 원문 존재 | 10 | 0 |
| 정규화 지역 존재 | 0 | 0 |
| 최소·최대 연령 모두 존재 | 9 | 0 |
| 연령 조건 원문 존재 | 10 | 0 |
| 카테고리 원문 존재 | 10 | 9 |
| 신청 상태 산출 | open 6, closed 3, scheduled 1 | 0 |
| 신청기간 형태 | fixed 5, always 2, 미상 3 | 전부 미상 |
| 자격 조건 text 존재 | 4 | 3 |
| 지원 내용 text 존재 | 10 | 10 |
| 외부 ID 누락·표본 내 중복 | 0 | 0 |
| 제목의 표본 내 중복 | 0 | 0 |
| 주거·월세 직접 표현 탐지 | 0 | 0 |

온통청년 연령 범위는 10건 중 9건에 숫자 범위가 있었고 나머지 1건은
숫자 범위가 없었다. 카테고리는 정규화됐지만 2건에서 미매핑 원문 때문에
`other`와 `unmapped_category` 경고가 추가됐다.

온통청년 전건 `partial`의 직접 원인은 `zipCd` 5자리 코드 목록을 이름으로
바꾸는 승인된 code-to-name 표가 없다는 점이다. 10건 모두
`unmapped_region_code`와 후속 `missing_regions` 경고가 있었다. 읽기 전용
로컬 `온통청년 API코드정보.xlsx`를 확인했지만 정책 제공·승인·기간·자격과
대·중분류·키워드 정의만 있고 행정구역 코드표는 없었다. 실제 표본에는
집계·과거 코드와 현재 세부 코드가 함께 나타날 수 있어 앞자리만으로
시·군·구를 임의 추정하지 않는다.

복지로 전건 `partial`의 직접 원인은 현재 목록·상세 매핑에서 지역, 연령과
신청기간 근거가 없다는 점이다. 10건 모두 `missing_regions`,
`missing_age_condition`, `missing_application_period` 경고가 있었고
1건에는 카테고리도 없었다. 상세 3건에서 자격 text는 보강됐지만 이 세
검색 조건은 보강되지 않았다.

표본에 주거·월세 직접 표현이 없다는 결과는 전체 Source에 해당 정책이
없다는 뜻이 아니다. 전체 릴리스 범위를 수집하기 전에는 golden query
정책의 존재나 부재를 판정하지 않는다.

### DT1 - 릴리스 수집 범위 초안

한 페이지를 Release 데이터로 고정하지 않고 다음 범위를 DT2·Gate G1
검토안으로 제시한다.

#### 온통청년

- 수집 시작 시점의 전체 목록을 범위로 하며 첫 응답의 `total_count`와
  page metadata를 기록한다.
- 공개 자료에서 `pageSize=500` 수용 여부가 확인되지 않았으므로 DT3 시작
  전에 1회만 확인한다. 수용되면 현재 2,696건 기준 최대 6회, 거부되면
  승인된 작은 page size와 예상 호출 수를 다시 기록한다.
- 누적 고유 외부 ID가 기준 `total_count`에 도달하고 마지막 page가
  요청 크기보다 작을 때 종료한다. 수집 중 `total_count`가 변하면 시작·종료
  수와 변동을 기록하고, 빈 page 또는 짧은 page를 보조 종료 조건으로 쓴다.
- Source가 snapshot cursor를 제공하지 않으므로 여러 page 사이의 변경
  가능성을 숨기지 않고 수집 회차와 시작·종료 시각을 보존한다.

#### 복지로

- 명세상 `numOfRows` 최대 500이므로 현재 461건 전체 목록은 한 요청을
  우선 범위로 한다. 반환 건수와 `total_count`가 다르면 다음 page를
  순회하고 빈 page 또는 짧은 page에서 종료한다.
- 공개 페이지의 개발계정 트래픽 100은 기간 단위가 불명확하므로 461건
  전부의 상세 호출은 범위에서 제외한다.
- 상세는 DT2에서 합의한 사용자 검색 가치와 누락 보강 효과를 기준으로
  목록에서 결정론적으로 고른 후보에만 수행하고, 최대 호출 수와 제외
  영향을 실행 전에 기록한다.
- 상세 제외 정책은 제목·요약·카테고리 수준 검색은 가능하지만 자격·지원
  설명이 제한될 수 있다. 지역·연령·신청기간은 현재 상세를 호출해도
  해결되지 않는다.

이 초안은 DT1 완료 산출물이며 실제 전체 호출 승인은 아니다. 큰 page size,
복지로 상세 선택, 지역 코드 기준과 `partial` 사용자 노출은 DT2와 Gate G1
검토 후 확정한다.

### DT1 - DT2 공동 결정 질문

- 온통청년 행정구역 코드표의 권위 출처와 버전을 무엇으로 고정할 것인가?
- 집계·폐지·분할 코드를 현재 행정구역으로 변환할 때 원문과 검색용 별칭을
  어떻게 함께 보존할 것인가?
- 복지로처럼 지역·연령·신청기간이 없는 정책을 기본 검색 결과에 포함할
  것인가, 미확인 조건으로만 opt-in할 것인가?
- 신청 상태를 Source 코드·기간·수집 시각 중 무엇을 우선해 판정할 것인가?
- 복지로 상세 후보와 호출 상한을 어떤 결정론적 규칙으로 고를 것인가?
- 검색 text에 제목·요약·지원·자격·신청 방법 중 어느 필드를 포함하고
  사용자가 확인할 검색 이유를 어떻게 연결할 것인가?
- `partial` 기본 노출 규칙을 유지하거나 바꾸면 Backend 필터와 Frontend
  미확인 조건 표시가 어떻게 동기화되는가?

## 주요 변경 파일

- `tests/test_runtime_replay.py`
- `docs/development/develop_plan/data/02_release_dataset_bootstrap.md`
- `docs/development/development_notes/data/release_dataset_bootstrap.md`
- `docs/data/source_profiles.md`
- `docs/development/weekly_plan/week_03_data_team_leader.md`
- 관련 계획·개발 기록 README와 `docs/index.md`
- `docs/development/develop_plan/forest_roadmap.md`

## 설계 결정

- DT0에서 외부 API를 호출하거나 Runtime Raw 디렉터리를 미리 만들지 않는다.
- 키 파일은 Source별 환경변수로 process에만 주입하고 값은 문서·로그·명령
  인자에 남기지 않는다.
- PostgreSQL 서비스·포트 확인과 인증 가능한 DB·Migration 확인을 서로 다른
  완료 조건으로 취급한다.
- Runtime DB credential을 추정하지 않고, `_test` DB가 준비되기 전에는
  PostgreSQL 통합 테스트를 성공으로 기록하지 않는다.
- Data 02는 실데이터 기준선까지만 담당하고 Backend·Frontend 구현과
  Integration 인수 범위를 가져오지 않는다.
- DT1 대표 표본은 실제 Source 계약을 확인하는 용도이며 Release snapshot
  또는 Runtime DB 적재 완료로 취급하지 않는다.
- 지역 코드와 복지로 누락 조건은 실제 근거 없이 보정하지 않고 DT2 공동
  계약으로 넘긴다.
- 릴리스 범위는 전체 목록을 기준으로 하되, 상세 호출은 확인된 할당량과
  사용자 영향 안에서 별도로 승인한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| 브랜치·작업 트리와 `develop` SHA | 통과 |
| 2주차 병합과 완료 Forest 문서 | 통과 |
| 두 Source 비밀 환경변수 주입 계약 | 통과, 외부 호출 없음 |
| `runtime/raw` Git 제외 | 통과, 디렉터리는 아직 없음 |
| PostgreSQL 서비스·5432 readiness | 통과 |
| PostgreSQL Runtime·테스트 DB 직접 인증 | 통과 |
| Runtime DB Alembic | 빈 DB → `20260730_0003` head 적용 성공 |
| Runtime DB 데이터 격리 | 테스트 전·후 Policy 0건 |
| Data 단위 테스트 | 90건 통과 |
| 최초 Backend·Integration PostgreSQL 테스트 | 75건 통과, 1건 실패 |
| 깨끗한 `_test` DB 재검증 | 76건 통과 |
| 테스트 DB 정리 | Policy 테이블 제거, 빈 Alembic 테이블만 유지 |
| 문서 검증 | 최초 실행에서 개발 기록 상태 누락 1건 발견, 수정 후 통과 |
| `git diff --check` | 통과 |

### DT1 검증

| 검증 | 결과 |
| --- | --- |
| 온통청년 실제 목록 호출 | 1회 성공, 10건, `total_count=2696` |
| 복지로 실제 목록·상세 호출 | 목록 1회·상세 3회 성공, 10건, `total_count=461` |
| Runtime Raw 재로드·추출·정규화 | 25개 Raw, 정책 20건 수용 |
| 품질 집계 | 두 Source 모두 partial 10건, invalid 0건 |
| 비밀·요청 query 출력 | 없음 |
| Runtime Raw Git 제외 | 통과 |
| 최초 전체 단위 테스트 | 89건 통과, 1건 실패 |
| 테스트 격리 수정 후 전체 단위 테스트 | 90건 통과 |

최초 단위 테스트 실패는 `test_missing_source_raw_fails_safely`가 저장소의
`runtime/raw`가 항상 비어 있다고 가정했기 때문이다. DT1의 정식 Raw가
생기면서 기대한 `RuntimeReplayError`가 발생하지 않았다. 실데이터를
삭제하지 않고 테스트가 자체 임시 빈 디렉터리를 사용하도록 격리한 뒤 전체
90건을 다시 실행해 통과했다.

최초 PostgreSQL 실패는 테스트 DB에 남아 있던 Seed 4건 때문에 첫 import가
`inserted=4` 대신 `unchanged=4`를 반환한 결과다. 실패 테스트의 `finally`
정리가 DB를 base로 되돌린 뒤 동일한 전체 명령을 다시 실행했고 76건이
통과했다. 첫 실패를 삭제하거나 최종 성공으로 덮어 기록하지 않는다.

## 남은 작업

- DT2에서 Backend·Frontend 초안과 함께 지역·연령·상태·partial·검색 text
  계약을 공동 검토한다.
- 온통청년의 권위 있는 행정구역 코드표를 확보하고 집계·과거 코드 처리
  원칙을 승인한다.
- DT3 전체 호출 전 온통청년 큰 page size 1회 확인과 복지로 상세 후보·호출
  상한을 승인한다.
- Backend 06·Frontend 04 담당자는 구현 전 개별 Forest 계획과 개발 기록
  위치를 생성한다.
- Team Leader는 DT5 전 Integration 03 계획과 개발 기록을 생성한다.
- 현재 테스트에서 발생한 Starlette의 `httpx` 사용 deprecation warning은
  DT0 범위 밖이며 별도 의존성 검토에서 처리한다.

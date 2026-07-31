# Release Dataset Bootstrap Forest 개발 기록

## 작업 정보

- 작업일: 2026-07-31
- 담당 영역: Data, Team Leader 시작 조정
- 상태: in-progress
- 브랜치: `feature/data/release-dataset-bootstrap`
- 기준 `develop` SHA: `fb6402d1793dbd9b4999d1a004fddf695f2d8bde`
- 관련 계획:
  [Release Dataset Bootstrap Forest](../../develop_plan/data/02_release_dataset_bootstrap.md)
- 현재 Slice: DT0 completed, next DT1

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
| DT1 | pending | DT0 완료 후 Source preflight |
| DT2 | pending | 실제 표본과 Backend·Frontend 초안 대기 |
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

## 주요 변경 파일

- `docs/development/develop_plan/data/02_release_dataset_bootstrap.md`
- `docs/development/development_notes/data/release_dataset_bootstrap.md`
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

최초 PostgreSQL 실패는 테스트 DB에 남아 있던 Seed 4건 때문에 첫 import가
`inserted=4` 대신 `unchanged=4`를 반환한 결과다. 실패 테스트의 `finally`
정리가 DB를 base로 되돌린 뒤 동일한 전체 명령을 다시 실행했고 76건이
통과했다. 첫 실패를 삭제하거나 최종 성공으로 덮어 기록하지 않는다.

## 남은 작업

- DT1에서 두 Source preflight와 호출 예산을 확정한다.
- Backend 06·Frontend 04 담당자는 구현 전 개별 Forest 계획과 개발 기록
  위치를 생성한다.
- Team Leader는 DT5 전 Integration 03 계획과 개발 기록을 생성한다.
- 현재 테스트에서 발생한 Starlette의 `httpx` 사용 deprecation warning은
  DT0 범위 밖이며 별도 의존성 검토에서 처리한다.

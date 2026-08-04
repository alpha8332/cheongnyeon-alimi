# Release Dataset Bootstrap Forest 개발 기록

## 작업 정보

- 작업일: 2026-07-31, 2026-08-03, 2026-08-04
- 담당 영역: Data, Team Leader 시작 조정
- 상태: in-progress
- 브랜치: `feature/data/release-dataset-bootstrap`
- 기준 `develop` SHA: `fb6402d1793dbd9b4999d1a004fddf695f2d8bde`
- 관련 계획:
  [Release Dataset Bootstrap Forest](../../develop_plan/data/02_release_dataset_bootstrap.md)
- 현재 Slice: DT4 pending, DT3 completed

## 목적

3주차 실데이터 작업을 시작하기 전에 2주차 병합 기준, Source 파이프라인,
비밀 주입, Runtime Raw와 PostgreSQL 실행 경계를 실제 저장소와 로컬
환경에서 확인한다.

## Forest 범위

이 기록은 Data 02의 DT0부터 DT4까지 실제 구현·검증 결과를 누적한다.
Integration 03 검색 데이터 기반, Backend 검색 구현, Frontend UI와
Integration 04 종단 인수 결과는 각 담당 Forest 기록에 남긴다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| DT0 | completed | Git·Source·비밀·Runtime·PostgreSQL 인증·Migration과 테스트 확인 |
| DT1 | completed | 두 Source 실호출·분포·partial 원인·릴리스 범위 초안 확인 |
| DT2 | completed | DT2A~DT2D 완료, `G1_APPROVED` 기록과 세 영역 후속 Slice 해제 |
| DT3 | completed | 전체 snapshot 3,159건 수집·Runtime DB 적재·재실행 검증 완료 |
| DT4 | pending | 적재된 실제 정책 3,159건의 품질·검색 사례 판정 대기 |

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
| Integration 03 | `develop_plan/integration/03_policy_search_data_foundation.md`, 대응 Integration 개발 기록 | PSF0~PSF8 구현·전체 Gate 완료, 기반 브랜치 병합 대기 |
| Integration 04 | Release 1 Acceptance 계획과 대응 Integration 개발 기록 | Team Leader가 DT5 전 생성 필요 |
| 보고서 | `docs/contest/`의 Release 1 제출 근거 | 실제 증거가 생길 때 작성 |
| 사용성 리뷰·QA | Integration 04 개발 기록의 독립 검증 절 | 시나리오·결함이 생길 때 기록 |

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

### DT2 - PSF 이후 actual profile

Integration 03이 병합된 현재 코드로 DT1 Runtime Raw를 외부 API 호출 없이
각 Source 10건씩 다시 재생했다. 정책 제목·원문·식별자는 출력하지 않고 계약
판정에 필요한 집계만 확인했다.

| 항목 | 온통청년 10건 | 복지로 10건 |
| --- | ---: | ---: |
| `valid` / `partial` / `invalid` | 8 / 2 / 0 | 0 / 10 / 0 |
| `coverage_scope` | regional 10 | unknown 10 |
| 정규화 지역·region rule 존재 | 10 / 10 | 0 / 0 |
| 최소·최대 연령 모두 존재 | 9 | 0 |
| 신청 상태 | open 6, closed 3, scheduled 1 | null 10 |
| 신청 일정 | fixed 5, always 2, null 3 | null 10 |
| category·keyword 존재 | 10 / 10 | 9 / 9 |
| summary·support text 존재 | 10 / 10 | 10 / 10 |
| eligibility·신청 방법 존재 | 4 / 9 | 3 / 0 |

PSF 이전 DT1에서는 권위 있는 지역 crosswalk가 없어 온통청년 10건 모두
`partial`이었지만, `kr-bjd-20260803` exact crosswalk 적용 뒤 10건 모두 지역
규칙이 연결되고 8건이 `valid`가 됐다. 남은 2건의 warning은
`unmapped_category`다. 복지로 10건은 지역·연령·신청기간 근거가 없어서
`missing_regions`, `missing_age_condition`, `missing_application_period`를
유지하며, category가 없는 1건에는 `missing_categories`도 있다.

### DT2 - Data 권고안

아래는 현재 실행 계약과 실제 표본에 근거한 G1 검토 입력이다. Backend API와
Frontend 표시 계약으로 확정된 내용은 아니며 두 담당자의 소비 검토가 필요하다.

| 결정 항목 | Data 권고 | 실제 근거와 소비 영향 |
| --- | --- | --- |
| 지역 | `match`는 포함, `mismatch`는 제외하고 `unknown`은 추정 없이 미확인 후보로 보존 | 온통청년은 exact regional 10건, 복지로는 unknown 10건이다. unknown을 모두 제외하면 복지로가 검색에서 사라지므로 Backend는 점수 감점·미확인 조건 반환, Frontend는 지역 미확인 표시 여부를 결정해야 한다. |
| 전국·상위 지역 | nationwide는 지역 query에 match, regional은 exact·ancestor·exclude 규칙을 그대로 사용 | PSF6 primitive가 천안·충남·전국·타 지역과 exclude를 구분한다. alias가 ambiguous·unmapped이면 임의 지역으로 고르지 않는다. |
| 연령 | 확인된 범위의 `match`·`mismatch`를 사용하고 경계가 없으면 `unknown` 후보로 보존 | 온통청년 9건만 숫자 범위가 있고 복지로 10건은 모두 미상이다. 27세 검색에서 확정 불일치는 제외하되 미상은 자격 확인 필요로 반환하는 안을 제안한다. |
| 신청 상태 | 명시적 상태 query는 같은 값만 `match`, null은 `unknown`; 기본 검색은 open 우선, scheduled·unknown의 별도 표시, closed 기본 제외를 제안 | 실제 표본은 open 6·closed 3·scheduled 1·null 10이다. 최종 기본값과 정렬은 Backend·Frontend가 함께 승인해야 한다. |
| 품질 | invalid는 항상 제외하고, 검색 endpoint는 valid와 partial을 후보로 삼되 partial·누락 조건을 응답과 화면에서 명시하는 안을 제안 | 복지로 실제 표본 전부가 partial이다. 기존 목록·상세 API의 `include_partial=false` 기본값은 유지하고 새 검색 계약에서 별도 승인한다. |
| 검색 text | Source Raw key를 직접 조회하지 않고 title, category·keyword, summary, eligibility, support projection을 사용 | 두 Source 모두 title·summary·support가 10건에 있고 eligibility는 4·3건이다. 신청 방법은 정책 의도 검색의 기본 projection에서 제외하고 필요 시 후속 저가중치 필드로 검토한다. |
| 관련도·정렬 | Data는 field별 근거와 3값 판정만 제공하고 최종 가중치·pagination은 Backend 06이 결정 | 검색 이유에는 일치 field와 미확인 조건을 분리해야 한다. 같은 점수의 결정적 tie-breaker도 API 초안에서 확정해야 한다. |

### DT2 - Schema·Fixture·Seed 영향 판정

- `NormalizedProgram` 1.1.0의 필드와 enum으로 현재 Data 권고를 표현할 수 있다.
- 선택 단일 값의 `null`, 반복 값의 `[]`, `coverage_scope=unknown` 규칙을
  변경하지 않는다.
- `valid|partial|invalid`, 신청 상태와 지역·관계 enum을 추가하거나 바꾸지
  않는다.
- canonical Fixture·Seed와 PostgreSQL Migration 변경은 필요하지 않다.
- 새 자연어 검색 request·해석 조건·검색 이유·미확인 조건은 NormalizedProgram
  필드가 아니라 Backend 06 API 응답 계약과 Frontend 04 타입에서 정의한다.

### DT2A - 병합 계약 정합성 보완

Backend `74bc87a0ffe40d36464f1f2f4236247e9be45bac`와 Frontend
`ed3fca6121203354da3dcf5d621ff0207555c679` 병합 뒤 W3-B0·W3-F0의 전체
request·response를 다시 대조했다. 본 구현은 시작하지 않고 계획과 Frontend
draft type의 잔여 불일치만 수정했다.

| 계약 영역 | 승인 후보 경계 | DT2A 보완 |
| --- | --- | --- |
| request | 필수 `q`, flat optional filter, `include_partial=true`, `page=1`, `limit=20` | Backend·Frontend 필드·기본값 유지 |
| interpreted condition | dimension, string·integer value, source, resolution, candidates | Backend `SearchDimension`과 Frontend union의 nullability 일치 |
| override | 검색 dimension 배열 | Backend `list[str]`을 제한된 dimension 배열로 좁힘 |
| verdict | region·age·status·category의 `match|mismatch|unknown|null` | 변경 없음 |
| result item | policy, score, verdicts, `unknown_count`, reason codes, message, row-level unconfirmed | Frontend에서 누락된 `unknown_count` 복구 |
| query 경고 | `interpreted_conditions.conditions[]` resolution·candidates | 존재하지 않는 top-level unconfirmed 참조 제거 |
| row 미확인 | `items[].unconfirmed_conditions[]` | 정책별 근거 부족에만 사용한다고 명시 |
| 상태 정렬 | open, scheduled, null unknown bucket, closed | `unknown`을 새 ApplicationStatus·DB enum으로 해석하지 않도록 고정 |
| 기존 모델 import | `app.schemas.policy` | 계획의 잘못된 `app.models.policy` import 수정 |

`NormalizedProgram` 1.1.0, Fixture, Seed, Migration, DB enum, 기존 Policy API와
운영 데이터는 변경하지 않았다. Frontend production import·UI·Mock·API Client,
Backend parser·Repository·endpoint도 구현하지 않았다.

#### DT2A 검증 결과

| 검증 | 결과 |
| --- | --- |
| Backend·Frontend request·response 정적 parity | 통과, 필드·타입·nullability·기본값 잔여 불일치 0건 |
| 실제 Backend Schema import·ApplicationStatus 대조 | 통과, `app.schemas.policy`, `open|closed|scheduled` 유지 |
| 폐기된 Frontend Slice 참조 | `FE4-05`·`FE4-09` 잔존 0건 |
| 문서 검증 테스트 | 10건 통과 |
| `python scripts/validate_docs.py` | 통과 |
| `git diff --check` | 통과 |
| Frontend build·lint | 미실행, DT2C 범위 |

DT2A 검증은 API·UI 본 구현 테스트가 아니다. G1 승인 전 draft 계약의 정적
정합성과 문서 실행 가능성만 확인했다.

### DT2B - Data 근거 기반 G1 결정 동결

Backend·Frontend가 제출한 소비 초안과 PSF 이후 actual profile을 공동
인수인계 결정표에서 대조했다. 복지로 표본 10건이 모두 partial이며 지역·연령·
상태 근거가 없다는 사실 때문에 unknown·partial을 기본 제외하지 않는다.
확정 mismatch와 invalid만 제외하고, unknown은 hard cutoff 없이 후보로 남겨
`unknown_count`로 감점하고 정책별 미확인 이유를 표시한다.

결정된 검색 계약은 필수 자연어 `q`, flat explicit override, 검색 API의
`include_partial=true`, open·scheduled·null 기본 상태, Backend 4단계 정렬,
사용자 입력만 저장하는 URL state와 400·422·200 empty·404·500 오류 분리다.
기존 `/api/v1/policies` 목록·상세와 NormalizedProgram·Fixture·Seed·Migration·
DB enum은 변경하지 않는다.

| 위험 | DT2B 판정 | 근거·다음 검증 |
| --- | --- | --- |
| reason code copy | resolved | 확장 string과 Backend message fallback, FE4-19 |
| unknown 포함·감점 | resolved | 복지로 보존, `unknown_count ASC`, FE4-18·19 |
| `/search`·`/programs` 경계 | resolved | 자연어와 기존 목록 route 병행, FE4-20 |
| Frontend rebase | resolved | Backend·Frontend HEAD 병합 완료 |
| category 다중 선택 | non-blocking | v0.1.0 단일 값, 후속 검토 |
| 지역 ambiguous 정확도 | implementation-risk | 임의 선택 금지, Backend B1·B4와 Frontend FE4-17·19 검증 |

Release 1 본 구현을 막는 미확정 검색 의미는 0건이다. 이 판정은 구현 정확도나
Browser 인수를 통과시킨 것이 아니며, 각 후속 Slice 검증이 실패하면 해당
항목을 다시 blocker로 전환한다.

#### DT2B 검증 결과

| 검증 | 결과 |
| --- | --- |
| G1 결정 필수 항목 정적 검사 | 통과, endpoint·partial·unknown·정렬·위험 분류 확인 |
| 문서 검증 테스트 | 10건 통과 |
| 최초 `python scripts/validate_docs.py` | 실패 2건, Backend·Frontend 계획의 필수 위험 제목 변경 감지 |
| 제목 복원 후 `python scripts/validate_docs.py` | 통과 |
| `git diff --check` | 통과 |
| PostgreSQL·외부 API | 미사용, DT2B 결정 동결에 불필요 |

### DT2C - 소비 계약 검증과 증거 기록

호스트에 Node/npm이 설치되어 있지 않아 Docker Desktop을 시작하고
`node:22.22.0-bookworm-slim` 컨테이너를 사용했다. 저장소는 read-only로
마운트했으며 Frontend와 canonical Seed를 컨테이너 임시 경로로 복사했다.
따라서 저장소에 `node_modules`, `dist` 또는 임시 산출물을 만들지 않았다.

| 검증 | 실제 결과 |
| --- | --- |
| 최초 Frontend build | 실패, 격리 경로에 `data/seeds`를 복사하지 않아 `@seed/initial_programs.json`을 찾지 못함 |
| 수정된 Frontend build | 통과, Node `22.22.0`, Vite `8.1.5`, 210 modules transformed |
| Frontend lint | 통과 |
| Frontend 계약 테스트 | 7건 통과 |
| 전체 npm dependency audit | 개발 의존성 high 1건 보고 |
| production dependency audit | `npm audit --omit=dev --audit-level=high`, 취약점 0건 |
| 문서 검증 테스트 | 10건 통과 |
| `python scripts/validate_docs.py` | 통과 |
| `git diff --check` | 통과 |
| 비밀·Raw·DB 추적 후보 | 0건 |
| PostgreSQL·외부 API·pgpass | 미사용, DT2C 범위에 불필요 |

첫 Frontend 계약 테스트·audit wrapper는 PowerShell에서 전달한 shell quote가
닫히지 않아 테스트 시작 전에 실패했다. 인자를 수정한 재실행에서 계약 테스트
7건과 production audit이 모두 통과했다. 최초 비밀 경계 검사도 의도적으로
추적하는 `.env.example`을 실제 비밀로 오탐했으며, 허용 예외를 분리한
재검사에서 추적 후보가 없음을 확인했다. 실패한 시도는 저장소 코드나 계약의
실패로 간주하지 않되 실행 기록에서 숨기지 않는다.

`.gitignore`에는 `.pgpass`, `*.db`, `*.sqlite`, `*.sqlite3`, `*.dump`,
`*.backup`을 추가했다. 기존 `.env`·`APIkey.txt`·`runtime/raw/` 경계와 함께
가상 probe에 `git check-ignore --no-index`를 적용해 모두 제외됨을 확인했다.
`.env.example`은 예제 계약이므로 계속 추적한다. npm의 개발 의존성 high 1건은
DT2C에서 lockfile을 임의 변경하지 않고 Frontend 의존성 관리 위험으로 남긴다.

### DT2D - Gate G1 승인과 후속 해제

DT2A~DT2C 증거와 Backend `74bc87a0ffe40d36464f1f2f4236247e9be45bac`,
Frontend `ed3fca6121203354da3dcf5d621ff0207555c679`가 현재 Data HEAD의 조상임을
확인했다. 이전 보완 커밋 `139d9c096c37bfc7be21cfd04e0636fa663918ea`와
`7a232da47eb1a6f1724aaf06c50f6ce33d52db4a`도 포함되어 있다.

| 승인 조건 | 결과 |
| --- | --- |
| 실제 Data 표본과 검색 결정 연결 | 충족, 온통청년·복지로 각 10건 actual profile 사용 |
| Backend·Frontend request·response parity | 충족, DT2A 불일치 0건 |
| Schema·Fixture·Seed·DB 영향 | 변경 없음 |
| Release 1 차단 미확정 항목 | 0건 |
| 소비 환경 실행 | DT2C Frontend build·lint·계약 테스트와 문서 검증 통과 |
| Git 비밀·Raw·DB 경계 | 추적 후보 0건 |

따라서 Gate G1을 `approved`로 판정하고 `G1_APPROVED` 신호를 인수인계 문서에
기록했다. Data DT3, Backend 06 B1과 Frontend 04 FE4-11을 시작할 수 있다.
Frontend 실제 API 연결은 Backend endpoint가 준비된 뒤 수행한다. 공동 인계
보드는 계약 결정 항목을 종료하고 구현 후속 인계로 전환했다.

남은 non-blocking 위험은 category 다중 선택, 지역 ambiguous 후보 정확도와
Frontend 개발 의존성 high 1건이다. 이 항목들은 각각 Backend·Frontend 본
구현 및 의존성 관리에서 검증하며 현재 계약이나 Schema를 변경하지 않는다.

DT2D 첫 문서 검증은 Frontend 계획의 `- 상태: approved` 뒤에 날짜 설명을 같은
줄에 넣어 검증기가 상태를 인식하지 못해 1건 실패했다. Forest 상태와 승인
일자를 별도 줄로 분리한 뒤 문서 검증 테스트 10건, `validate_docs.py`와
`git diff --check`를 다시 실행해 모두 통과했다.

### DT3A~DT3B - 완료 snapshot과 다중 page 재생

기존 Collector는 한 번의 목록 응답만 저장했고 Runtime replay도 가장 최신
`list_response` 하나만 선택했다. 이 경계로 온통청년 전체 목록을 page별로
수집하면 마지막 page만 DB에 적재되는 구조적 누락이 생긴다. 이를 해결하기
위해 단일 page Collector 책임은 유지하고 여러 결과를 다음 완료 manifest로
묶었다.

```text
runtime/raw/_snapshots/<source_id>/<snapshot_id>.json
```

manifest는 payload나 URL 대신 시작·완료 시각, page size, 호출 예산·실제
호출 수, total·item 수와 기여 Raw document ID를 저장한다. Source가 보고한
total만큼 고유 external ID를 확인한 뒤에만 원자적으로 생성한다. 수집 중
total 변경, 중복 ID, 조기 종료, 예산 부족 또는 metadata 불일치는 실패하며
중간 Raw가 있더라도 완료 snapshot으로 선택하지 않는다.

Runtime replay와 import CLI는 최신 또는 `--snapshot-id`로 고정한 manifest의
여러 목록 응답을 한 batch로 처리한다. 전체 항목을 수용하도록 item limit을
5,000으로 확장했고 manifest가 없는 합성 Fixture와 과거 Raw의 단일 응답
호환은 유지했다. Schema·Fixture·Seed·DB enum과 `null`·빈 배열 규칙은
변경하지 않았다.

### DT3C - 실제 전체 목록 수집과 오프라인 replay

인증값은 키 파일의 Source별 token을 현재 process 환경변수에만 주입했고
실행 후 제거했다. URI, query, key와 Raw payload는 출력하지 않았다. 첫
온통청년 시도에서는 로컬 키 파일의 라벨을 포함한 전체 행을 값으로 잘못
주입해 HTTP 403 인증 실패 1회가 발생했다. Raw와 manifest는 생성되지 않았고,
키 값은 출력하지 않았다. 마지막 token만 안전하게 분리한 뒤 승인 호출을
재실행했다.

| Source | page size | 목록 성공 | 상세 성공 | 성공 요청 | 항목 | Raw | snapshot ID |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 온통청년 | 500 | 6 | 0 | 6 | 2,698 | 2,704 | `4580234be1df46cbbe4a700fc4e02630` |
| 복지로 | 500 | 1 | 5 | 6 | 461 | 467 | `2e0b8100348544b3b023b27017025218` |

실제 Source 요청은 실패 1회와 성공 12회, 합계 13회다. 재시도는 없었다.
온통청년은 모든 page에서 `total_count=2698`, 복지로는 `total_count=461`을
보고했고 각 snapshot의 고유 ID 수와 일치했다. 복지로 전체 상세 461건은
승인 범위가 아니므로 호출하지 않았다.

| Source | Raw replay | extracted | valid | partial | invalid | accepted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 온통청년 | 2,704 | 2,698 | 1,938 | 760 | 0 | 2,698 |
| 복지로 | 467 | 461 | 0 | 461 | 0 | 461 |

첫 온통청년 오프라인 replay에서는 3건이 `source_url` Schema pattern 위반으로
invalid였다. Source 응답의 URL 후보에 literal 공백이 있었고 Extractor는
scheme·host만 확인한 반면 Normalized validator와 JSON Schema는 공백을
거부한 계약 불일치였다. Extractor가 공백 URL을 public URL 후보로 사용하지
않고 query 없는 공식 Raw endpoint로 fallback하도록 수정했다. 원문 URL은
Raw와 `extra.source_fields`에 그대로 보존한다. 수정 후 2,698건 모두
valid 또는 partial로 수용됐다.

DT3C까지는 외부 호출 없는 replay 검증이며 PostgreSQL `--dry-run`이나 실제
적재 성공으로 기록하지 않는다. DT3D에서 Runtime DB credential을 process에만
주입해 Migration·지역 Seed·dry-run·실적재·동일 snapshot 재실행을 검증한다.

### DT3D - Runtime PostgreSQL bootstrap과 재실행

첫 실행은 `PGPASSWORD`를 사용한 Alembic 연결에서 Windows의 지역화된
PostgreSQL 오류를 psycopg2가 UTF-8로 해석하지 못해 `UnicodeDecodeError`로
중단됐다. Migration이나 DB write 전이었다. 임시 `PGPASSFILE`과 `psql`
preflight를 추가한 두 번째 실행에서 현재 PostgreSQL 18 cluster에 DT0 당시
사용한 `cheongnyeon_alimi` DB가 없다는 실제 원인을 확인했다. 사용자가 빈
Runtime DB를 생성한 뒤 같은 절차를 처음부터 재실행했다.

현재 cluster의 빈 Runtime DB에 Alembic `20260803_0004` head를 적용하고
versioned 지역 기준정보 `kr-bjd-20260803`의 region 538건과 alias 1,080건을
신규 적재했다. `_test` DB는 사용하지 않았다.

| 실행 | 온통청년 | 복지로 |
| --- | --- | --- |
| dry-run | inserted 2,698, rollback | inserted 461, rollback |
| 첫 실제 import | inserted 2,698 | inserted 461 |
| 동일 snapshot 재실행 | unchanged 2,698 | unchanged 461 |
| 최종 DB row / distinct identity | 2,698 / 2,698 | 461 / 461 |

dry-run 후 첫 실제 import가 전건 inserted였으므로 dry-run에서 Policy write와
실행 이력이 rollback된 경계를 확인했다. 실제 실행 4건은 다음 CollectionRun
ID로 기록됐다.

- 온통청년 최초: `54d7efd7-a511-4200-be49-5140a912ec00`
- 복지로 최초: `cc1c4fba-443b-4114-8e79-8636a39f43a5`
- 온통청년 재실행: `e7ff445a-59a8-453d-937d-9c6438fe61f9`
- 복지로 재실행: `b14851ba-25e8-4e64-ae09-1709604c02bc`

모든 실행에서 skipped·rejected·failed는 0이다. 최종 Policy 3,159건은
`(source_id, external_id)` 기준 identity 3,159개와 일치해 중복 row가 없다.
이 결과로 DT3의 실제 Raw → Normalized → PostgreSQL과 idempotent 재실행
완료 조건을 충족했다.

## 주요 변경 파일

- `collectors/snapshot.py`
- `scripts/collect_release_snapshot.py`
- `collectors/runtime.py`
- `scripts/import_runtime_data.py`
- `tests/test_snapshot_collection.py`
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
- DT2 Data 권고는 현재 1.1.0의 3값 판정과 projection을 사용하며 Schema·
  Fixture·Seed·`null`·빈 배열·enum 변경을 제안하지 않는다.
- unknown·partial 후보의 기본 노출과 정렬은 Data가 단독 확정하지 않고
  Backend 06·Frontend 04 소비 초안과 Gate G1에서 승인한다.
- 여러 page의 전체 목록은 마지막 응답 한 건으로 대표하지 않고, total과
  고유 ID 완전성을 확인한 immutable manifest를 재처리 경계로 사용한다.
- 호출 예산을 목록과 상세 요청의 합으로 제한하고 manifest 생성 전에
  부족함을 확인한다. 실패 중간 Raw는 원문 보존하되 릴리스 회차로 승인하지
  않는다.

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

### DT2 Data 근거 준비 검증 (`2026-08-03`)

| 검증 | 결과 |
| --- | --- |
| 실제 API 호출 | 없음, 저장된 DT1 Runtime Raw만 오프라인 재생 |
| 온통청년 actual replay | 10건 수용, valid 8·partial 2·invalid 0, regional·region rule 10건 |
| 복지로 actual replay | 10건 수용, valid 0·partial 10·invalid 0, coverage unknown 10건 |
| Data 전체 단위 테스트 | 102건 통과 |
| 검색 계약·PostgreSQL 집중 pytest | 11건 통과, 기존 warning 1건 |
| Frontend 기존 계약 테스트 | 7건 통과 |
| Schema·Fixture·Seed·DB·API 변경 | 없음 |

검색 계약 집중 검증 후 `_test` DB는 `alembic_version` 외 public table이 없는
상태로 정리됐음을 확인했다. Browser UI는 변경하지 않았고 Frontend 04
초안도 아직 없으므로 이번 DT2 Data 근거 준비에서 화면 검증을 수행하지 않는다.

### DT3 검증 (`2026-08-04`)

| 검증 | 결과 |
| --- | --- |
| snapshot·Collector·replay 집중 pytest | 32건·subtest 10건 통과 |
| 실제 온통청년 전체 목록 | 6회 성공, 2,698건, 완료 manifest 생성 |
| 실제 복지로 전체 목록·제한 상세 | 목록 1회·상세 5회 성공, 461건, 완료 manifest 생성 |
| 실제 호출 실패 | 온통청년 키 행 parsing 오류로 403 1회, Raw·manifest 없음 |
| 완료 snapshot 오프라인 replay | 온통청년 2,698·복지로 461 전건 수용, invalid 0 |
| 최초 전체 Data 단위 테스트 | 107건 중 1건 실패, 합성 Raw 1파일 working-tree CRLF |
| Fixture 결정론적 재생성 후 전체 Data 단위 테스트 | 107건 통과 |
| 첫 Runtime DB 연결 | 실패, 지역화된 DB 오류가 psycopg2 `UnicodeDecodeError`로 표시됨 |
| `psql` preflight | 실패, 현재 cluster에 Runtime DB가 없음을 확인 |
| 빈 Runtime DB 복구 | 생성 후 Alembic `20260803_0004`, region 538·alias 1,080 적용 |
| PostgreSQL dry-run | 온통청년 2,698·복지로 461 insert projection 후 rollback |
| 첫 실적재 | 3,159건 inserted, skipped·rejected·failed 0 |
| 동일 snapshot 재실행 | 3,159건 unchanged, inserted·updated 0 |
| 최종 identity | Source별 row와 distinct external ID 일치, 합계 3,159 |
| 최종 Data 단위 테스트 | 108건 통과 |
| Runtime importer·Integration pytest | 5건 통과, PostgreSQL 환경변수 미주입 4건 skip |
| Python compile·문서 검증·`git diff --check` | 통과 |

합성 Raw 실패는 JSON 내용이나 Fixture 계약 변경이 아니라 `.gitattributes`가
LF로 고정한 파일 하나가 작업 트리에서 CRLF로 checkout된 byte 차이였다.
결정론적 생성기로 13개 산출물을 다시 기록했고 의미 변경 없이 전체 검증이
통과했다.

skip 4건은 `TEST_DATABASE_URL`이 없는 현재 process에서 테스트 전용 DB를
요구한 결과이므로 PostgreSQL 테스트 통과로 기록하지 않는다. DT3D 자체의
Runtime DB 검증은 별도로 dry-run·실적재·재실행과 최종 SQL identity 집계까지
성공했다.

## 남은 작업

- DT4에서 전체 실제 데이터의 검색 품질·경계 사례와 golden
  query 후보를 판정해 Backend·Frontend에 인계한다.
- Team Leader는 DT5 전 Integration 04 계획과 개발 기록을 생성한다.
- 현재 테스트에서 발생한 Starlette의 `httpx` 사용 deprecation warning은
  DT0 범위 밖이며 별도 의존성 검토에서 처리한다.

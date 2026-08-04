# Release Dataset Bootstrap Forest 개발 계획

## 계획 정보

- 담당 영역: Data
- 상태: completed
- 대상 기간: 3주차 Release 1 실데이터 기준선
- 관련 브랜치: `feature/data/release-dataset-bootstrap`
- 현재 Slice: DT4 completed
- 개발 기록:
  [Release Dataset Bootstrap 개발 기록](../../development_notes/data/release_dataset_bootstrap.md)

현재 브랜치는 Data domain의 실데이터 bootstrap·품질 관리 범위와 일치한다.
이 Forest 안에서 Slice별 브랜치를 추가하지 않는다.

## 목적

온통청년과 복지로의 문서화된 릴리스 수집 범위에서 실제 정책 snapshot을
수집하고, 기존 Raw → Extracted → Normalized → PostgreSQL 경계를 사용해
재현 가능한 `v0.1.0` 검색 데이터 기준선을 만든다.

사용자 검색 요청은 PostgreSQL만 조회한다. 외부 API 호출은 명시적인
수집·적재 절차에서만 수행한다.

## 범위

- 2주차 완료 기준과 로컬 실행 환경 확인
- 두 Source의 endpoint·pagination·할당량·종료 조건 preflight
- 대표 실데이터의 지역·연령·카테고리·신청 상태·품질 분포 확인
- 승인된 릴리스 범위의 Runtime Raw 수집
- 기존 Normalizer·Validator를 사용한 재처리와 PostgreSQL bootstrap
- 재실행 idempotency, transaction과 중복 방지 검증
- Backend·Frontend에 전달할 실제 데이터 경계 사례와 golden query 후보
- Source별 건수·품질·실패와 적재 결과 기록

## 범위 밖

- Backend 자연어 해석·검색 API 구현
- Frontend 검색 UI 구현
- 실제 DB → API → UI Browser 인수 검증과 `v0.1.0` 최종 판정
- Scheduler와 정기 운영 수집
- 새로운 Source 추가
- LLM·벡터 검색
- 합의되지 않은 Schema, `null`, 빈 배열 또는 enum 변경

Backend·Frontend 구현은 각각 Backend 06과 Frontend 04가 담당한다.
Source 중립 검색 필드·지역·DB 기반은 Integration 03이 담당하고, 실제 종단
인수와 릴리스 판정은 Integration 04가 담당한다.

## 선행 조건

- Backend 03·Frontend 02를 포함한 2주차 결과가 `develop`에 병합됨
- Windows `.venv`에서 저장소 의존성을 사용할 수 있음
- 두 API 키를 저장소 밖에서 환경변수로 안전하게 주입할 수 있음
- PostgreSQL 5432 서비스뿐 아니라 인증 가능한 Runtime DB가 준비됨
- PostgreSQL 통합 테스트는 Runtime DB와 분리된 `_test` DB를 사용함
- `runtime/raw`가 Git 제외 대상임
- Source별 실제 호출량은 DT1에서 승인한 범위를 넘지 않음

## 공통 설계 원칙

- 비밀값, 인증 query, Raw payload와 DB credential을 출력하거나 Git에
  기록하지 않는다.
- 외부 응답을 수정하지 않고 Runtime Raw에 원문과 수집 metadata를 보존한다.
- Source별 Extractor와 기존 Normalizer·Validator 책임을 유지한다.
- 실제 데이터에 없는 지역·연령·자격 조건을 추정하지 않는다.
- Schema·Fixture·Seed·`null`·빈 배열·enum 변경은 Data가 단독 확정하지
  않고 Backend·Frontend 소비 영향과 기준 문서를 함께 검토한다.
- 실제 진행 중 정책이 없으면 golden query 결과를 만들지 않는다.
- Runtime DB와 `_test` DB를 구분하고 테스트를 Runtime DB에서 실행하지 않는다.

## Slice 계획

### DT0 - 시작 기준과 실행 경계

- 목적: 2주차 기준선, 비밀 주입, Runtime 경로와 PostgreSQL 환경을 확인한다.
- 산출물: 기준 SHA, Source·Importer 경계, 환경 준비 상태와 Forest별 기록 위치
- 완료 기준:
  - 최신 `develop` 기준과 작업 브랜치 범위 확인
  - 두 Source 비밀 주입과 `runtime/raw` Git 제외 확인
  - 인증 가능한 Runtime DB와 Migration 적용 대상 확인
  - Data 02·Integration 03·Backend 06·Frontend 04·Integration 04의 책임과
    기록 위치 확인

### DT1 - Source preflight와 대표 실데이터

- 목적: 전체 수집 구현 전에 Source별 실제 호출 제약과 검색 필드 분포를
  확인한다.
- 선행 조건: DT0 완료와 Source별 호출 예산 승인
- 산출물: Source별 preflight, 대표 표본 분포, 릴리스 범위·호출 예산 초안
- 완료 기준: 두 Source의 종료 조건과 검색 계약 결정에 필요한 실제 근거 확보
- 완료 결과:
  - 온통청년 목록 10건 1회와 복지로 목록 10건·상세 3건을 실제 수집함
  - 두 Source 모두 10건 전부 `partial`인 원인과 검색 필드 누락 비율을 확인함
  - 전체 목록을 기준으로 한 종료 조건과 호출량 보호가 포함된 릴리스 범위
    초안을 작성함
  - 지역 코드, 복지로 상세 범위와 partial 노출 의미는 DT2·Gate G1 승인
    전까지 구현하지 않음

### DT2 - 검색 계약 Data 근거와 Gate G1 지원

- 상태: completed (`2026-08-04`)
- 목적: 실제 표본을 바탕으로 지역·연령·상태·품질 의미를 제안하고
  Backend·Frontend 공동 계약 검토를 지원한다.
- 선행 조건: DT1, Integration 03 PSF0~PSF8, Backend 06·Frontend 04 초안
- 산출물: Data 권고안, 경계 사례, Schema 변경 영향 판정과 G1 승인 기록
- 완료 기준: DT2A~DT2D를 순서대로 완료하고 Data·Backend·Frontend 소비
  관점의 G1 검토 증거를 확보함

Integration 03 병합 후 저장된 DT1 Runtime Raw를 외부 호출 없이 다시 재생해
Data 근거와 Schema 영향 판정을 준비했다. 현재 1.1.0 계약으로 지역·연령·상태·
품질의 `match|mismatch|unknown`을 표현할 수 있어 Data Schema, Fixture, Seed,
`null`, 빈 배열과 enum 변경은 제안하지 않는다. Backend 06·Frontend 04 초안을
현재 브랜치에 병합한 뒤 response parity와 `null`·경고 위치 표현을 DT2A에서
보완했으며, DT2B~DT2D 결정·소비 검증을 거쳐 Gate G1을 승인했다.

#### DT2A - 병합 계약 정합성 보완

- 상태: completed (`2026-08-04`)
- 목적: 병합된 W3-B0·W3-F0 초안의 구현 전 계약 불일치를 제거한다.
- 작업:
  - Backend 계획의 실제 `ApplicationStatus`·`PolicyCategory` import 경로 수정
  - 상태 정렬의 `unknown`을 새 enum이 아닌 `application_status=null` 파생
    bucket으로 명시
  - query-level 지역 해석 경고와 row-level 미확인 조건의 DTO 위치 분리
  - Frontend `PolicySearchHit.unknown_count`와 Backend response parity 복구
  - Frontend draft 주석의 폐기된 FE4 Slice 번호를 현재 계획과 동기화
- 변경 경계:
  - 계획·draft type만 수정하고 Backend API·Repository·Frontend UI 본 구현은
    시작하지 않음
  - NormalizedProgram 1.1.0, Fixture, Seed, DB enum, `null`·빈 배열 규칙을
    변경하지 않음
- 완료 기준:
  - request·response 필드, 타입, nullability와 기본값 대조표에 불일치 0건
  - 코드의 실제 import·enum 경계와 계획 문서가 일치함

#### DT2B - Data 근거 기반 G1 결정 동결

- 상태: completed (`2026-08-04`)
- 선행 조건: DT2A
- 목적: 실제 표본과 세 영역 초안을 하나의 Release 1 검색 의미로 확정한다.
- 작업:
  - `GET /api/v1/policies/search`, 필수 `q`, flat explicit override 확정
  - confirmed mismatch 제외, unknown 후보 포함·감점과 partial 기본 포함 확정
  - 기본 상태 노출, null status bucket, score·tie-breaker·pagination 확정
  - query-level 해석 경고, row-level reason·미확인 조건과 오류 의미 확정
  - `G1-REASON`, `G1-UNK`, `G1-ROUTE`와 Backend 미확정 사항을 Release 1
    blocker 또는 후속 구현 위험으로 분류
- 산출물: 실제 Data 표본과 각 결정이 연결된 G1 결정표
- 완료 기준:
  - 본 구현을 막는 미확정 검색 의미 0건
  - Schema·Fixture·Seed·DB enum 변경 없음과 API·Frontend 영향이 명시됨

#### DT2C - 소비 계약 검증과 증거 기록

- 상태: completed (`2026-08-04`)
- 선행 조건: DT2B
- 목적: 승인 후보 문서와 draft type이 각 소비 환경에서 실행 가능함을 확인한다.
- 작업:
  - Frontend `npm run build`와 `npm run lint`
  - 문서 검증 단위 테스트와 `python scripts/validate_docs.py`
  - `git diff --check`, 비밀·Raw·DB 파일 비추적 확인
  - 실행 명령·환경·결과를 Data 개발 기록에 남기고 미실행 항목을 구분
- 완료 기준:
  - Frontend type build·lint와 문서 검증 통과
  - 계약 대조와 실제 검증 결과가 같은 승인 후보를 가리킴
- 완료 결과:
  - Node `22.22.0` 컨테이너에서 Frontend build·lint와 계약 테스트 7건 통과
  - 문서 검증 테스트 10건, `validate_docs.py`, `git diff --check` 통과
  - 비밀·Runtime Raw·로컬 DB credential과 산출물의 Git 비추적 경계 확인

#### DT2D - Gate G1 승인과 후속 해제

- 상태: completed (`2026-08-04`)
- 선행 조건: DT2A~DT2C
- 목적: DT2 완료 증거를 동기화하고 세 영역의 본 구현을 공식 해제한다.
- 작업:
  - Gate G1 인수인계에 결정표·검증 결과와 `G1_APPROVED` 기록
  - Backend W3-B0·Frontend W3-F0 준비 상태와 Data DT2 상태 동기화
  - `docs/index.md` 공동 인계 보드를 종료하거나 구현 후속 인계로 전환
  - 3주차 Data·Team Leader 체크리스트와 현재 Slice를 DT3로 전환
- 완료 기준:
  - Data DT2 `completed`와 Gate G1 `approved`가 관련 계획·인계·색인에서 일치
  - DT3, Backend B1~B4와 Frontend FE4-11~FE4-24 시작 조건이 명확함
- 완료 결과:
  - `G1_APPROVED`를 기록하고 Backend 06·Frontend 04 계획을 `approved`로 전환
  - Data DT3, Backend B1, Frontend FE4-11의 시작 조건을 해제
  - 공동 인계 보드를 검색 구현 후속 인계로 전환

### DT3 - 릴리스 snapshot 수집과 PostgreSQL bootstrap

- 상태: completed (`2026-08-04`)
- 목적: 승인 범위를 재현 가능하게 수집·재처리·적재한다.
- 선행 조건: DT1 릴리스 범위, Integration 03 Migration·Importer 기반,
  인증 가능한 Runtime DB
- 산출물: Runtime Raw, 적재 집계, 재실행·실패 복구 결과와 bootstrap 절차
- 완료 기준: 실제 Raw → Normalized → PostgreSQL 적재 및 재실행 검증

#### DT3A - 다중 page snapshot 경계와 호출 예산

- 상태: completed (`2026-08-04`)
- 목적: 단일 page Collector를 승인된 전체 목록 snapshot으로 안전하게 묶는다.
- 작업:
  - Collector 결과에 page·total·기여 Raw document ID metadata 추가
  - page size 500, Source total 도달, 중복·total 변동·조기 종료 검증
  - 목록·상세 합산 request budget 사전·사후 검증
  - 완료된 회차만 원자적 manifest로 확정하고 실패 중간 Raw와 구분
- 완료 기준:
  - 예산 안에서 여러 page를 완주하고 완전한 manifest를 생성함
  - 예산 부족·경로 이탈·중복·불완전 회차는 완료 snapshot으로 선택되지 않음

#### DT3B - manifest 기반 오프라인 재생

- 상태: completed (`2026-08-04`)
- 선행 조건: DT3A
- 목적: 여러 목록 응답을 하나의 명시적 회차로 재처리한다.
- 작업:
  - 최신 또는 명시한 snapshot ID의 manifest 로드
  - manifest가 가리키는 목록·항목·상세 Raw 완전성 검증
  - Runtime import limit을 전체 정책 수를 수용하는 5,000으로 확장
  - manifest가 없는 기존 Fixture·Raw의 단일 회차 호환 유지
- 완료 기준:
  - 여러 page Raw가 하나의 Extracted·Normalized batch로 재생됨
  - 누락·중복·role 불일치 manifest는 DB write 전에 실패함

#### DT3C - 승인 범위 실수집과 dry-run 전 품질 확인

- 상태: completed (`2026-08-04`)
- 선행 조건: DT3A~DT3B
- 목적: 승인된 호출량으로 실제 전체 목록을 수집하고 DB 전 경계를 확인한다.
- 승인 범위:
  - 온통청년 전체 목록, page size 500, 성공 요청 최대 6회, 상세 없음
  - 복지로 전체 목록, page size 500, 목록 1회와 상세 최대 5회
- 완료 기준:
  - 온통청년 2,698건과 복지로 461건의 완료 manifest 생성
  - 오프라인 replay에서 두 Source 모두 invalid 0건이고 total과 accepted 일치
  - 비밀·query·payload와 Runtime Raw가 Git 추적 후보에 포함되지 않음

#### DT3D - Runtime PostgreSQL bootstrap과 복구 검증

- 상태: completed (`2026-08-04`)
- 선행 조건: DT3C, 인증 가능한 Runtime DB
- 목적: 완료 snapshot을 Runtime PostgreSQL에 적재하고 재실행 안전성을 확인한다.
- 작업:
  - Runtime DB에 최신 Alembic과 versioned 지역 기준정보 적용
  - Source별 snapshot ID를 고정한 `--dry-run` 후 실제 import
  - 동일 snapshot 재실행의 unchanged·중복 0 검증
  - 실패 시 batch rollback과 다시 실행 가능한 bootstrap 절차 기록
- 완료 기준:
  - 두 Source accepted 합계와 DB 정책 identity 수가 일치함
  - 두 번째 import가 inserted·updated 0, 전건 unchanged임
  - CollectionRun 집계, rollback 경계와 Runtime·`_test` DB 분리가 확인됨
- 완료 결과:
  - 새 Runtime DB를 Alembic `20260803_0004` head까지 적용하고 지역 538건·
    alias 1,080건을 적재함
  - dry-run은 온통청년 2,698건·복지로 461건의 insert projection을 검증한 뒤
    rollback함
  - 첫 실제 import가 3,159건을 insert하고 동일 snapshot 재실행은 3,159건
    전부 unchanged로 판정함
  - Source별 DB row 수와 distinct external identity 수가 각각 2,698·461로
    일치함

### DT4 - 실제 데이터 품질 판정과 인계

- 상태: completed (`2026-08-04`)
- 목적: 검색 가능한 실제 데이터의 품질과 golden query 후보를 확인한다.
- 선행 조건: DT2와 DT3
- 산출물: 품질 분포, 검색 경계 사례, golden query 후보 또는 정책 부재 근거
- 완료 기준: Backend·Frontend가 사용할 안전한 실제 사례와 제약 전달

#### DT4A - 실제 snapshot 품질 Profile

- 상태: completed (`2026-08-04`)
- 완료 결과:
  - 고정한 두 완료 manifest를 외부 API·DB 연결 없이 재생하는
    `scripts/profile_release_dataset.py`를 추가함
  - accepted 3,159건, valid 1,462건, partial 1,697건, invalid 0건과
    기본 노출 1,187건을 집계함
  - Source별 상태·지역·연령·카테고리·경고와 identity·provenance 분포를
    안전한 JSON 집계로 재현함

#### DT4B - Source placeholder 연령 경계 보정

- 상태: completed (`2026-08-04`)
- 완료 결과:
  - 온통청년 631건의 `0세 ~ 0세`를 확인되지 않은 Source placeholder로 판정함
  - 원문은 보존하고 구조화 연령을 null, 품질을 partial로 처리해 27세 검색의
    confirmed mismatch 오분류를 방지함
  - Schema·Fixture·Seed·enum·null 표현과 Backend·Frontend type은 변경하지 않음

#### DT4C - 검색 경계와 golden query 판정

- 상태: completed (`2026-08-04`)
- 완료 결과:
  - 기본 노출에서 27세는 match 544·mismatch 26·unknown 617, 천안시는
    match 54·mismatch 671·unknown 462로 확인함
  - 월세 검색어는 전체 165건·기본 노출 51건이지만 `27세 천안 청년 월세
    지원`의 confirmed 정책은 0건임
  - confirmed mismatch를 제외한 실제 후보 2건은 복지로의 지역·연령·상태
    unknown 정책이므로 자격 확정 결과로 사용할 수 없음을 기록함

#### DT4D - Runtime DB 동기화와 담당자 인계

- 상태: completed (`2026-08-04`)
- 완료 결과:
  - 연령 placeholder 보정을 Runtime PostgreSQL에 재적재해 631건 updated,
    2,067건 unchanged를 확인함
  - 동일 snapshot 재실행은 온통청년 2,698건 전부 unchanged였고 Source별
    DB row와 identity·품질 집계가 오프라인 Profile과 일치함
  - 구조화된 `age_min=0 AND age_max=0` 행은 0건임을 SQL로 확인함
  - 안전한 실제 사례·제약을 Data 기준 문서와 공동 인계 보드에 등록함

DT5·DT6은 이 Data Forest의 구현 Slice가 아니다. Integration 04 계획과
개발 기록에서 실제 DB → API → UI 및 릴리스 판정을 수행한다.

## 검증 계획

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -B -m pytest tests/integration -q
python scripts/validate_docs.py
git diff --check
git status --short
```

PostgreSQL 통합 테스트는 `TEST_DATABASE_URL`이 `_test` DB를 가리킬 때만
실행한다. skip 결과를 실제 PostgreSQL 성공으로 기록하지 않는다. DT1의
외부 API 호출 명령과 호출 수는 preflight 직전에 확정한다.

## Forest 완료 기준

- 승인된 두 Source 릴리스 범위를 누락 없이 수집함
- 실제 Raw → Normalized → PostgreSQL bootstrap과 재실행이 성공함
- Source별 valid·partial·invalid와 적재·실패 집계를 설명할 수 있음
- 검색에 필요한 지역·연령·상태·카테고리 경계 사례가 준비됨
- golden query 후보가 실제 Source에 존재하거나 정책 부재가 명확히 기록됨
- 비밀키, Runtime Raw와 DB 파일이 Git에 포함되지 않음
- 관련 Data 테스트, PostgreSQL 통합 테스트와 문서 검증이 통과함

## 위험과 미확정 사항

- 복지로 461건은 현재 계약만으로 지역·연령·신청기간을 확정할 수 없어
  전건 partial이고 기본 검색에서 unknown 후보로만 사용할 수 있다.
- `27세 천안 청년 월세 지원`의 confirmed 정책은 0건이다. 실제 후보 2건은
  지역·연령·상태가 모두 unknown이므로 자격 충족으로 표시하면 안 된다.
- Integration 04는 일반 월세 탐색을 golden flow로 사용할지, confirmed
  천안·27세 정책을 위한 Source 범위를 보강할지 결정해야 한다.
- 충청남도 broad query는 현재 계약상 하위 시군 정책을 자동 포함하지 않는다.
  semantics 변경은 Backend·Frontend 영향이 있는 별도 공동 결정이다.
- Frontend 의존성 audit과 Starlette deprecation warning은 Data 02 범위 밖의
  기존 후속 위험이다.

## 관련 문서

- [3주차 Data·Team Leader 실행 계획](../../weekly_plan/week_03_data_team_leader.md)
- [3주차 전체 상세 실행 계획](../../weekly_plan/week_03_release_1.md)
- [Release와 Milestone 계획](../release_roadmap.md)
- [전체 Forest 로드맵](../forest_roadmap.md)
- [Data Pipeline Forest](01_data_pipeline.md)
- [Policy Data Database Integration](../integration/02_policy_data_database_integration.md)
- [Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md)
- [검색 계약 Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md)
- [Source Profile](../../../data/source_profiles.md)
- [Release 1 실데이터 품질 Profile](../../../data/release_dataset_profile.md)
- [Collector 실행](../../../operations/collector.md)
- [Backend Windows 로컬 환경](../../backend_local_setup.md)

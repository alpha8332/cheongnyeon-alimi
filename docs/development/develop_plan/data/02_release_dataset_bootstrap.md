# Release Dataset Bootstrap Forest 개발 계획

## 계획 정보

- 담당 영역: Data
- 상태: in-progress
- 대상 기간: 3주차 Release 1 실데이터 기준선
- 관련 브랜치: `feature/data/release-dataset-bootstrap`
- 현재 Slice: DT1 completed, next DT2
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
실제 종단 인수와 릴리스 판정은 Integration 03이 담당한다.

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
  - Data 02·Backend 06·Frontend 04·Integration 03의 책임과 기록 위치 확인

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

- 목적: 실제 표본을 바탕으로 지역·연령·상태·품질 의미를 제안하고
  Backend·Frontend 공동 계약 검토를 지원한다.
- 선행 조건: DT1, Backend 06·Frontend 04 초안
- 산출물: Data 권고안, 경계 사례와 Schema 변경 영향 판정
- 완료 기준: Data·Backend·Frontend 소비 관점의 G1 검토 증거 확보

### DT3 - 릴리스 snapshot 수집과 PostgreSQL bootstrap

- 목적: 승인 범위를 재현 가능하게 수집·재처리·적재한다.
- 선행 조건: DT1 릴리스 범위, 인증 가능한 Runtime DB와 Migration
- 산출물: Runtime Raw, 적재 집계, 재실행·실패 복구 결과와 bootstrap 절차
- 완료 기준: 실제 Raw → Normalized → PostgreSQL 적재 및 재실행 검증

### DT4 - 실제 데이터 품질 판정과 인계

- 목적: 검색 가능한 실제 데이터의 품질과 golden query 후보를 확인한다.
- 선행 조건: DT2와 DT3
- 산출물: 품질 분포, 검색 경계 사례, golden query 후보 또는 정책 부재 근거
- 완료 기준: Backend·Frontend가 사용할 안전한 실제 사례와 제약 전달

DT5·DT6은 이 Data Forest의 구현 Slice가 아니다. Integration 03 계획과
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

- DT0에서 Runtime DB를 Alembic head까지 준비했지만 실제 정책은 아직 0건이다.
  실제 snapshot은 DT3 전까지 존재하지 않는다.
- DT1 대표 표본 Raw 25개는 Git 제외 `runtime/raw`에만 있으며 아직 DB에
  적재하지 않았다.
- 온통청년은 2,696건을 보고했지만 계정별 숫자 호출 한도와 `pageSize=500`
  수용 여부가 공개 자료에서 확인되지 않았다. DT3 전체 순회 전에 큰
  page size 1회 확인과 호출 예산 승인이 필요하다.
- 복지로는 목록 전체 461건이 명세상 한 요청에 들어가지만, 공개 페이지의
  개발계정 트래픽 100은 기간 단위가 불명확하다. 전체 461건 상세 호출은
  릴리스 범위로 승인하지 않았다.
- 온통청년 `zipCd`는 실제 응답에 있으나 보유 코드 정의서에는 행정구역
  code-to-name 표가 없어 정규화 지역이 0건이다.
- 복지로 목록·상세 계약에는 현재 지역·연령·신청기간을 직접 정규화할
  근거가 없어 해당 필드가 모두 누락된다.
- 실제 Source에 golden query에 맞는 진행 중 정책이 없을 수 있다.
- 검색 의미에 필요한 Schema 변경이 발견되면 DT2에서 세 영역 영향을
  검토하기 전까지 구현하지 않는다.

## 관련 문서

- [3주차 Data·Team Leader 실행 계획](../../weekly_plan/week_03_data_team_leader.md)
- [3주차 전체 상세 실행 계획](../../weekly_plan/week_03_release_1.md)
- [Release와 Milestone 계획](../release_roadmap.md)
- [전체 Forest 로드맵](../forest_roadmap.md)
- [Data Pipeline Forest](01_data_pipeline.md)
- [Policy Data Database Integration](../integration/02_policy_data_database_integration.md)
- [Source Profile](../../../data/source_profiles.md)
- [Collector 실행](../../../operations/collector.md)
- [Backend Windows 로컬 환경](../../backend_local_setup.md)

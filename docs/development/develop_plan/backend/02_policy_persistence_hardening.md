# Backend Policy Persistence Hardening Forest 개발 계획

## 계획 정보

- 번호: Backend 02
- 담당 영역: Backend
- 상태: completed
- 선행 Forest:
  [Backend Policy Baseline](01_policy_baseline.md)
- 관련 브랜치: `feature/backend/policy-baseline-v2`
- 현재 Slice: B6 완료
- 후속 Forest:
  [Policy Data Database Integration](../integration/02_policy_data_database_integration.md)

## 목적

Backend Policy Baseline에서 마련한 ORM, Seed importer와 정책 API를 실제
PostgreSQL 기준으로 검증 가능한 상태로 완성한다. 코드와 문서의 차이를
해소하고 Migration, transaction, 검증과 Repository 경계를 확정해 Data
파이프라인이 안전하게 사용할 DB 적재 인터페이스를 제공한다.

## 범위

- Backend 계획·개발 기록과 실제 코드의 정합성 복구
- PostgreSQL과 테스트 DB의 명시적인 실행 경계
- Policy ORM과 실제 Alembic revision
- source-scoped 식별자와 upsert 규칙
- PostgreSQL JSONB, timezone과 핵심 DB constraint
- Schema·품질 검증을 적용한 Seed importer
- transaction, rollback과 적재 결과 집계
- Policy Repository와 목록·상세 API 기본 경계
- Backend 단위·API 테스트와 PostgreSQL 검증

## 범위 밖

- Collector, Extractor와 Normalizer 변경
- Runtime Raw 재처리 진입점
- 전체 수집 자동화와 Scheduler
- 자유 키워드 검색, 검색 순위와 추천
- Frontend TypeScript 타입과 화면
- CollectionRun 관리자 기능
- Dockerfile, Compose와 Production 배포

Data Pipeline과 DB의 종단 간 연결은 후속 Integration 02에서 수행한다.

## 선행 조건

- `feature/backend/policy-baseline`의 실제 변경을 기준으로 검토한다.
- `NormalizedProgram` 1.0.0과 canonical Seed를 입력 계약으로 사용한다.
- Backend가 관리하는 의존성 manifest와 실행 방법을 사용한다.
- PostgreSQL 검증 환경이 없으면 SQLite 결과를 PostgreSQL 성공으로 기록하지
  않는다.

## 공통 설계 원칙

- PostgreSQL 연결 실패를 SQLite 자동 fallback으로 숨기지 않는다.
- SQLite는 명시적인 단위 테스트 환경에서만 사용할 수 있다.
- Alembic Migration을 `Base.metadata.create_all()`로 대신하지 않는다.
- ORM 변경과 Alembic revision은 같은 변경에서 동기화한다.
- 잘못된 날짜·시각·필수값을 `null`, 현재 시각이나 빈 문자열로 보정하지
  않는다.
- `valid`와 `partial`은 적재 가능하고 `invalid`와 Schema 위반은 거부한다.
- Normalized Schema의 nullable `external_id` 계약은 유지한다. 현재
  온통청년·복지로의 DB admission에서는 external ID를 요구하고, 값이 없는
  입력은 확인 가능한 사유와 함께 적재하지 않는다. 향후 HTML Source의 대체
  ID는 별도 Forest에서 결정한다.
- `categories`, `regions`, 조건 배열과 provenance는 PostgreSQL `JSONB`를
  우선안으로 사용한다. category·region의 기본 필터에 필요한 GIN index를
  검토하고, 완전한 관계 정규화는 후속 DB 안정화 범위로 둔다.
- 수집·생성·수정 시각은 UTC timezone-aware 값으로 저장하고 사용자 표시에서
  Asia/Seoul로 변환한다.
- 핵심 enum, 연령 범위와 날짜 순서처럼 DB에서도 보호할 불변 조건은
  JSON Schema와 중복되더라도 최소 check constraint로 검토한다.
- 실제 실행한 테스트와 DB 종류만 개발 기록에 남긴다.

## Slice 계획

### B0 - Backend 기준선 정합성 복구

- 상태: completed
- 목적: 완료 선언, 개발 기록과 실제 코드를 같은 상태로 맞춘다.
- 주요 작업:
  - 실제 Alembic revision 존재 여부 확인
  - 범용 `JSON`과 문서의 `JSONB` 표현 정리
  - 조회 후 update와 문서의 `ON CONFLICT` 표현 정리
  - 완료 상태와 남은 작업의 모순 해소
  - 공백과 EOF 오류 정리
- 산출물:
  - 정정된 Backend 계획과 개발 기록
- 완료 기준:
  - 코드, 계획과 개발 기록의 DB 타입·upsert·Migration 설명 일치
  - `git diff --check` 통과
- 완료 결과:
  - Backend 01을 범용 `JSON`, 조회 후 update, Alembic 환경만 존재하는 실제
    기준선으로 정정하고 PostgreSQL hardening을 Backend 02로 이관함
  - Fixture·Seed 계약의 Backend 소비 상태와 현재 구현 설명을 동기화함
  - ORM과 테스트 파일의 공백 오류를 제거함
  - Backend 기능 테스트는 현재 사용 가능한 Python 환경에 SQLAlchemy가 없어
    재실행하지 않았으며 B1 이후 합의된 Backend 환경에서 검증해야 함

### B1 - PostgreSQL 연결과 테스트 DB 경계

- 상태: completed
- 목적: 실행 환경의 DB 선택과 연결 실패를 명시적으로 처리한다.
- 선행 조건:
  - B0 완료
- 주요 작업:
  - PostgreSQL 실패 시 SQLite 자동 fallback 제거
  - Engine과 Session의 테스트 주입 경계
  - `DATABASE_URL`과 선택적인 `TEST_DATABASE_URL` 계약
  - 연결 오류에서 비밀번호와 전체 URL 비노출
  - health check의 실제 연결 상태 검증
- 산출물:
  - Backend DB 설정과 연결 테스트
- 완료 기준:
  - 잘못된 PostgreSQL 설정이 명확하게 실패
  - SQLite는 명시적인 테스트 설정에서만 사용
  - 비밀정보 노출 0건
- 구현 결과:
  - PostgreSQL 연결 확인 실패를 로컬 SQLite 파일로 숨기던 자동 fallback을
    제거함
  - URL을 명시적으로 받는 Engine 생성 함수와 Engine을 받는 Session factory,
    연결 확인 함수로 테스트 주입 경계를 분리함
  - `DATABASE_URL`과 선택적 `TEST_DATABASE_URL` 설정 계약을 추가함
  - Engine 구성 오류에는 비밀번호를 마스킹한 URL과 예외 종류만 남기고 원본
    예외 메시지는 노출하지 않음
  - Backend 단위 테스트는 명시적인 인메모리 SQLite Engine을 사용하며 운영
    Engine을 재사용하지 않음
  - health check는 선택된 Engine에 `SELECT 1`을 실행하고 실패 시 기존 503
    응답을 유지함
- 검증 결과:
  - 저장소 전용 `.venv`에 `backend/requirements.txt` 의존성을 설치함
  - DB 경계·마스킹·health 테스트 10건 통과
  - Backend 전체 테스트 14건 통과
  - 테스트 SQLite는 명시적인 인메모리 Engine만 사용하며 PostgreSQL 성공으로
    기록하지 않음

### B2 - Policy ORM과 Alembic Migration

- 상태: completed
- 목적: Normalized 계약의 물리적 저장 구조를 Migration으로 고정한다.
- 선행 조건:
  - B1 완료
  - 배열과 provenance 저장 방식 공동 결정
- 주요 작업:
  - 31개 필드의 컬럼 타입, null과 배열 보존 검토
  - 배열·조건과 provenance의 PostgreSQL `JSONB` 저장
  - category·region 검색을 위한 GIN index 검토
  - `collected_at`, `created_at`, `updated_at`의 UTC timezone-aware 저장
  - quality·schedule·status enum, 연령 범위·순서의 check constraint
  - unique constraint와 필요한 기본 인덱스
  - 초기 Policy Alembic revision 생성
  - upgrade와 downgrade 검증
- 산출물:
  - Policy ORM과 Alembic revision
- 완료 기준:
  - 빈 PostgreSQL에서 `alembic upgrade head` 성공
  - ORM metadata와 Migration Schema 일치
  - 배열과 provenance의 JSONB 왕복, timezone과 constraint 검증
  - downgrade 또는 깨끗한 DB 재구성 검증
- 구현 결과:
  - NormalizedProgram 31개 필드와 ORM 컬럼 집합의 일치 테스트를 추가함
  - 배열·조건·provenance 8개 컬럼을 PostgreSQL `JSONB`, SQLite 단위
    테스트에서는 범용 `JSON`으로 매핑함
  - 신청 일정·상태·품질을 PostgreSQL enum으로 고정하고 SQLite에서는 같은
    값 집합의 CHECK constraint로 검증함
  - 연령 범위·순서와 신청일 순서 constraint, source-scoped unique,
    기본 B-tree index와 categories·regions GIN index를 추가함
  - 수집·생성·수정 시각을 timezone-aware 컬럼과 UTC Python 기본값으로
    변경함
  - 최초 revision `20260728_0001`과 enum을 포함한 명시적 downgrade를 추가함
  - PostgreSQL offline upgrade·downgrade SQL과 SQLite constraint 테스트를
    통과함
  - 명시적 `TEST_DATABASE_URL`과 `_test` DB명에서만 실행되는 PostgreSQL
    upgrade·JSONB 왕복·constraint·downgrade 통합 테스트를 추가함
- 실행 검증:
  - 일회성 PostgreSQL 17.10을 `127.0.0.1` 전용 포트에서 실행하고
    `cheongnyeon_alimi_test` 빈 DB를 사용함
  - 실제 upgrade, JSONB·timezone 왕복, 연령 constraint 거부와 downgrade 후
    테이블·enum 제거를 통과함
  - `TEST_DATABASE_URL`을 사용한 Backend 전체 테스트 28건 통과
  - 검증 후 일회성 PostgreSQL 서버·cluster·바이너리를 제거함

### B3 - 식별자와 upsert 규칙

- 상태: completed
- 목적: Seed와 이후 재수집 결과의 중복 생성을 막는다.
- 선행 조건:
  - B2 완료
- 주요 작업:
  - `(source_id, external_id)` uniqueness 검증
  - 온통청년·복지로의 null external ID를 DB admission에서 거부
  - PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` 기반 원자적 upsert
  - inserted, updated, unchanged, skipped와 failed 구분
  - 동일 Seed 재실행과 경계 사례 테스트
- 산출물:
  - 식별·upsert 결정과 구현
- 완료 기준:
  - 동일 Seed 재실행 후 중복 0건
  - 현재 두 API의 null external ID 적재 0건과 확인 가능한 거부 사유
  - 동시 또는 반복 실행 경계가 명시됨
- 구현 결과:
  - 온통청년·복지로 입력은 비어 있지 않은 `external_id`를 DB admission에서
    요구하고, 누락 입력은 `missing_external_id` 사유로 건너뜀
  - 향후 Source의 null 식별자는 임의 대체 ID를 만들지 않고
    `unsupported_null_external_id`로 분리함
  - PostgreSQL에서는 `uq_policies_source_external` constraint를 대상으로
    `INSERT ... ON CONFLICT DO UPDATE`를 사용하고, `IS DISTINCT FROM` 조건으로
    실제 값이 달라질 때만 update함
  - 결과를 inserted·updated·unchanged·skipped·failed로 집계하고 오류에는
    payload나 DB 예외 메시지 대신 안전한 코드와 예외 종류만 기록함
  - 동일 Seed 재실행, 현재 두 API의 null ID, DB constraint 실패와 두 세션의
    동시 upsert를 PostgreSQL 17.10에서 검증함
  - SQLite 경로는 단위 테스트용 이식성 경계로 유지하며 운영 원자성의
    증거로 사용하지 않음
  - CLI의 `Base.metadata.create_all()`을 제거해 Schema 생성 권한을 Alembic
    Migration으로 한정함
- 실행 검증:
  - 실제 PostgreSQL에서 동일 Seed 재실행과 동시 입력 모두 중복 0건
  - `TEST_DATABASE_URL`을 사용한 Backend 전체 테스트 35건 통과
  - 검증 후 일회성 PostgreSQL 서버·cluster·바이너리를 제거함

### B4 - 검증 우선 Seed importer

- 상태: completed
- 목적: Schema 위반 데이터를 DB에 넣지 않고 적재 실패를 원자적으로 처리한다.
- 선행 조건:
  - B3 완료
  - Data Validator 호출 방법 확인
- 주요 작업:
  - JSON root와 `NormalizedProgram` Schema 검증
  - `valid`·`partial` 허용, `invalid`와 Schema 위반 거부
  - 날짜·enum·필수값을 임의 기본값으로 보정하지 않음
  - canonical Seed all-or-nothing transaction
  - 실패 시 명시적 rollback
  - `--file`, `--dry-run` CLI
  - 검증·삽입·갱신·무변경·건너뜀·거부·실패 건수 출력
- 산출물:
  - 안전한 Seed import service와 CLI
- 완료 기준:
  - Seed 4건 적재
  - invalid와 Schema 위반 적재 0건
  - 실패 시 DB 변경 0건
  - payload와 비밀정보 로그 노출 0건
- 구현 결과:
  - Data 영역의 `NormalizedProgramValidator`로 모든 항목을 DB 접근 전에
    검증하고 `valid`·`partial`만 쓰기 대상으로 허용함
  - root가 배열이 아니거나 항목이 객체가 아닌 경우, Schema·Python 모델
    위반과 `invalid` 품질 상태를 path·code와 함께 rejected로 분류함
  - Schema-valid null external ID는 현재 두 API의 DB admission에서 skipped,
    빈 문자열은 Schema 위반으로 rejected 처리하며 어느 경우든 전체 batch를
    저장하지 않음
  - 날짜·시각·필수값·배열·enum에 importer 기본값이나 파싱 fallback을
    적용하지 않음
  - 사전 검증을 통과한 전체 batch를 단일 transaction으로 실행하고 한 건의
    DB 실패에도 전체 rollback함
  - `--dry-run`은 실제 upsert 경로의 예상 결과를 집계한 뒤 rollback함
  - CLI가 validated·inserted·updated·unchanged·skipped·rejected·failed를
    출력하고 issue는 index·path·code·예외 종류만 노출함
- 실행 검증:
  - canonical Seed 4건의 정상 적재와 dry-run DB 변경 0건 검증
  - valid와 Schema 위반 혼합 batch, invalid 품질, 강제 DB 실패의 적재 0건
    검증
  - PostgreSQL 18.4 실제 테스트 DB에서 Migration·upsert·dry-run·rollback
    통합 테스트 3건 통과

### B5 - Repository와 Policy API 기준선

- 상태: completed
- 목적: HTTP, 비즈니스 흐름과 DB 조회 책임을 분리한다.
- 선행 조건:
  - B4 완료
- 주요 작업:
  - Route → Service → Repository 구조
  - `GET /api/v1/policies`
  - `GET /api/v1/policies/{policy_id}`
  - pagination과 기본 category·region·status 필터
  - PostgreSQL JSONB 배열 연산과 합의된 기본 인덱스 사용
  - valid 기본 노출과 partial opt-in 정책
  - 상세 API에서 partial을 조회할 수 있는지 명시적으로 결정
  - provenance 일반 사용자 API 비노출
  - 404와 query 오류 응답
- 산출물:
  - Policy Repository, Service와 API 계약
- 완료 기준:
  - 목록·상세·pagination·필터·404 테스트 통과
  - category·region 배열 검색의 부분 문자열 오탐 0건
  - partial 노출 규칙이 목록과 상세에서 일관됨
  - provenance 사용자 응답 노출 0건
- 구현 결과:
  - Route → `PolicyService` → `PolicyRepository`로 HTTP, 품질 정책과 DB
    조회 책임을 분리함
  - 목록은 `id` 오름차순 pagination과 category·region·status 필터를
    제공하고 total은 pagination 전 필터 건수로 계산함
  - PostgreSQL은 JSONB `@>`, SQLite 단위 테스트는 `json_each`로
    category·region 배열의 정확한 원소만 검색함
  - category와 status query는 enum, page·limit·region은 범위 검증을
    적용해 잘못된 query를 422로 반환함
  - 목록과 상세 모두 기본 valid만 노출하고 `include_partial=true`일 때
    valid·partial을 허용하며 invalid는 항상 숨김
  - 품질 범위에서 숨겨진 상세와 존재하지 않는 ID를 같은 404 응답으로 처리함
  - 공개 DTO의 배열·null·enum 경계를 명시하고 provenance를 제외함
  - `docs/api/policies.md`에 요청·응답·오류 계약을 기록함
- 실행 검증:
  - SQLite Repository·Service·API와 기존 Policy 회귀 테스트 19건 통과
  - PostgreSQL 18.4에서 JSONB exact membership, pagination과 partial 상세
    정책 테스트 1건 통과
  - 초기 `.contains()`가 JSON 기반 `LIKE`로 컴파일되는 실제 오류를 확인하고
    명시적 JSONB `@>` 연산자로 수정함

### B6 - Backend PostgreSQL 검증

- 상태: completed
- 목적: Backend 기준선을 실제 PostgreSQL에서 최종 확인한다.
- 선행 조건:
  - B1~B5 완료
- 주요 작업:
  - Migration upgrade
  - Seed 적재와 재실행
  - invalid 거부와 rollback
  - 배열, null, 날짜와 provenance 보존
  - Repository와 API 조회
  - PostgreSQL 연결 실패
- 산출물:
  - Backend PostgreSQL 테스트와 실제 실행 기록
- 완료 기준:
  - Migration → Seed → Repository → API 흐름 통과
  - 중복, invalid 적재와 주요 필드 손실 0건
  - 실제 DB 종류와 실행 명령이 개발 기록에 남음
- 완료 결과:
  - PostgreSQL 18.4 전용 테스트 DB에서 Migration upgrade 후 canonical Seed
    4건 적재와 동일 Seed 재실행 unchanged 4건을 확인함
  - Normalized 31개 필드를 Seed와 ORM 조회 결과로 비교해 null·빈 배열·enum,
    날짜·timezone instant와 provenance 손실 0건을 확인함
  - Schema 위반 혼합 batch의 추가 DB 변경 0건을 확인함
  - 실제 PostgreSQL Session을 FastAPI dependency에 주입해 valid 2건,
    partial 포함 4건, JSONB category 2건과 목록·상세 품질 정책을 확인함
  - 공개 API의 null·빈 배열·날짜 보존과 provenance 비노출을 확인함
  - 닫힌 PostgreSQL 포트 연결 실패가 SQLite 성공으로 전환되지 않음을 확인함
  - downgrade 후 Policy 테이블 제거를 확인함

## 검증 계획

- Backend 단위·API 테스트
- Alembic upgrade와 downgrade
- PostgreSQL 연결 성공·실패
- Seed 정상·재실행·Schema 위반·rollback
- null·빈 배열·날짜·provenance 보존
- JSONB 배열 필터, timezone과 DB constraint
- `uv run python -B scripts/validate_docs.py`
- `git diff --check`

Backend 의존성이 현재 환경에 없으면 새 패키지를 임의로 설치하지 않고
합의된 manifest와 기존 실행 환경을 먼저 확인한다.

## Forest 완료 기준

- B0~B6 완료
- 실제 Alembic revision과 PostgreSQL 적용 성공
- canonical Seed 4건 적재와 재실행 중복 0건
- invalid와 Schema 위반 적재 0건
- rollback과 적재 결과 집계 검증
- Policy Repository와 목록·상세 API 통과
- 문서, ORM, Migration과 실제 테스트 결과 일치
- Integration 02가 사용할 검증된 import service 제공

## 위험과 미확정 사항

- Backend 의존성은 저장소 `.venv`에서 재현했고 PostgreSQL 17.10 일회성
  DB와 로컬 PostgreSQL 18.4 전용 테스트 DB에서 B2~B6을 검증했다. 지속적인
  PostgreSQL 제공 방식과 컨테이너 구성은 Integration·Deploy에서 결정한다.
- 배열과 provenance는 PostgreSQL JSONB와 SQLite JSON variant로 구현했으며
  JSONB 왕복과 GIN index 생성까지 검증했다. 실제 검색 쿼리의 GIN 사용 여부는
  B5 Repository와 B6 종단 간 검증에서 확인한다.
- Normalized Schema의 `source_id`에는 최대 길이가 없지만 PostgreSQL에서는
  unique·B-tree index key 크기 제한을 받는다. 현재 source ID는 짧지만
  논리 계약에 상한을 둘지는 Data·Backend 공동 결정이 필요하다.
- 현재 두 API의 external ID admission과 원자적 upsert는 B3에서 검증했으며,
  Normalized Schema의 nullable 계약과 향후 HTML Source의 대체 ID까지
  일반화하지 않는다.
- 자유 키워드 검색과 인덱스 최적화는 이 Forest 범위가 아니다.

## 관련 문서

- [개발 계획 안내](../README.md)
- [Backend Policy Baseline](01_policy_baseline.md)
- [Policy Data Database Integration](../integration/02_policy_data_database_integration.md)
- [Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [역할과 책임](../../../governance/role_assignment.md)
- [API 문서 안내](../../../api/README.md)

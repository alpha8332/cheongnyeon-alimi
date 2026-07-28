# Backend Policy Persistence Hardening Forest 개발 기록

## 작업 정보

- 시작일: 2026-07-28
- 상태: in-progress
- 영역: backend
- 브랜치: `feature/backend/policy-baseline-v2`
- 관련 계획:
  [`02_policy_persistence_hardening.md`](../../develop_plan/backend/02_policy_persistence_hardening.md)
- 현재 Slice: B2 완료, B3 대기

## 목적

Backend Policy Baseline의 ORM, Seed importer와 정책 API를 실제 PostgreSQL
기준으로 보강한다. 코드와 문서의 차이를 먼저 해소하고 Migration,
transaction, Repository와 PostgreSQL 검증을 순서대로 완료한다.

## Forest 범위

- Backend 기준선 정합성 복구
- PostgreSQL 연결과 테스트 DB 경계
- Policy ORM과 Alembic Migration
- 식별자와 원자적 upsert
- 검증 우선 Seed importer
- Repository와 Policy API
- Backend PostgreSQL 검증

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| B0 | completed | Backend 01 문서·코드 정합성 복구와 공백 정리 |
| B1 | completed | 명시적 DB 선택·테스트 주입·비밀 마스킹과 health 검증 |
| B2 | completed | ORM·초기 revision·PostgreSQL 17.10 실제 Migration 검증 |
| B3 | pending | 식별자와 upsert |
| B4 | pending | 검증 우선 Seed importer |
| B5 | pending | Repository와 Policy API |
| B6 | pending | Backend PostgreSQL 검증 |

## 구현 내용

### B0 - Backend 기준선 정합성 복구

- 실제 코드를 기준으로 Backend 01 계획과 개발 기록을 재검토했다.
- 기존 모델은 범용 SQLAlchemy `JSON`을 사용하며 PostgreSQL `JSONB`는 아직
  구현하지 않았음을 기록했다.
- Alembic metadata 연결 환경은 있지만 `backend/alembic/versions/`에 실제
  revision이 없음을 기록했다.
- 기존 Seed importer는 PostgreSQL `ON CONFLICT`가 아니라
  `(source_id, external_id)` 조회 후 insert·update 방식임을 기록했다.
- CLI의 `Base.metadata.create_all()`과 PostgreSQL 실패 시 SQLite 자동
  fallback을 후속 B1~B2 위험으로 이관했다.
- 실제 필드명인 `application_start`, `application_end`,
  `application_period_text`로 문서를 정정했다.
- Fixture·Seed 계약에서 Backend 모델이 없다는 과거 설명과 JSONB 구현 완료
  표현을 현재 상태로 갱신했다.
- `backend/app/models/policy.py`의 trailing whitespace와
  `backend/tests/conftest.py`의 불필요한 EOF 빈 줄을 제거했다.

### B1 - PostgreSQL 연결과 테스트 DB 경계

- PostgreSQL 연결 실패 시 `sqlite:///./cheongnyeon_alimi.db`로 자동 전환하던
  fallback을 제거했다.
- `create_db_engine()`은 전달받은 URL로만 Engine을 만들며 생성 시 실제 연결을
  시도하지 않는다. 잘못된 URL이나 드라이버 설정은
  `DatabaseConfigurationError`로 명확하게 실패한다.
- Engine 구성 오류는 비밀번호가 마스킹된 URL과 예외 종류만 제공하며, 원본
  예외 메시지와 전체 인증정보는 전달하지 않는다.
- `create_session_factory()`와 Engine을 선택적으로 받는
  `check_db_connection()`을 추가해 운영 전역 객체 없이 DB 동작을 검증할 수
  있게 했다.
- health check는 선택된 실제 Engine의 `SELECT 1` 결과에 따라 200 또는 503을
  유지한다. 연결 실패를 다른 DB의 성공으로 바꾸지 않는다.
- 설정에 선택적인 `TEST_DATABASE_URL`을 추가했다. 이는 향후 PostgreSQL 통합
  테스트가 명시적으로 선택할 URL이며, 단위 테스트는 별도의 인메모리 SQLite
  Engine을 직접 생성한다.
- Backend 테스트 fixture는 운영 Engine과 Session을 재사용하지 않고
  `sqlite+pysqlite:///:memory:`와 `StaticPool`을 명시적으로 사용한다.
- DB URL 선택, SQLite 명시 사용, 비밀번호 마스킹, Session 주입, 연결
  성공·실패를 검증하는 단위 테스트를 추가했다.

### B2 - Policy ORM과 Alembic Migration

- `NormalizedProgram`의 31개 필드와 Policy ORM 컬럼을 일대일로 대조했다.
  기존 `source_id`, nullable text와 `source_url`의 추가 길이 제한은 논리
  Schema에 없는 거부 조건이므로 PostgreSQL `TEXT`로 맞췄다.
- categories·regions·조건 배열과 provenance 8개 컬럼은 PostgreSQL에서
  `JSONB`를 사용한다. 동일 ORM을 사용하는 명시적 SQLite 단위 테스트에서는
  SQLAlchemy type variant로 범용 `JSON`을 사용한다.
- `application_schedule`, `application_status`, `data_quality_status`를
  PostgreSQL named enum으로 고정했다. SQLite에서는 동일 SQLAlchemy Enum이
  CHECK constraint를 생성한다.
- `age_min`·`age_max`의 0~150 범위, 최소·최대 순서와 신청 시작·종료일 순서를
  DB CHECK constraint로 보호한다.
- `(source_id, external_id)` unique constraint와 source·external ID·품질
  B-tree index를 유지하고 categories·regions에 PostgreSQL GIN index를
  추가했다.
- `collected_at`, `created_at`, `updated_at`을 timezone-aware 컬럼으로
  변경했다. Python 기본값과 Seed importer가 만드는 수정 시각은 UTC aware
  datetime을 사용한다.
- 최초 Alembic revision `20260728_0001`을 추가했다. upgrade는 enum·Policy
  테이블·index를 만들고 downgrade는 index·테이블·enum을 역순으로 제거한다.
- Alembic 비교 설정에 type과 server default 비교를 활성화했다.
- Normalized JSON Schema, Fixture와 Seed 값은 바꾸지 않았다.

## 주요 변경 파일

- `backend/app/models/policy.py`
- `backend/.env.example`
- `backend/app/api/v1/endpoints/health.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/20260728_0001_create_policies.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/models/policy.py`
- `backend/app/services/seed_importer.py`
- `backend/tests/conftest.py`
- `backend/tests/test_database.py`
- `backend/tests/test_migrations.py`
- `backend/tests/test_policy_model.py`
- `backend/tests/test_postgresql_migration.py`
- `docs/data/data_schema.md`
- `docs/data/fixture_seed_contract.md`
- `docs/development/develop_plan/backend/01_policy_baseline.md`
- `docs/development/develop_plan/backend/02_policy_persistence_hardening.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/backend/policy_baseline.md`
- `docs/development/development_notes/backend/policy_persistence_hardening.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`

## 설계 결정

### 기존 Backend 01 완료 기록을 기초 구현으로 보존한다

Backend 01은 ORM, Seed importer와 정책 목록·상세 API의 기초 구현 결과로
유지한다. 실제 Migration, PostgreSQL JSONB, 원자적 upsert, transaction과
PostgreSQL 통합 검증은 구현된 것처럼 소급 기록하지 않고 Backend 02에서
완료한다.

### 계약 승인과 PostgreSQL hardening을 구분한다

Backend가 canonical Seed의 배열·null·날짜·품질·provenance 소비 방향을
검토한 사실은 유지한다. 다만 범용 JSON 모델 반영과 실제 PostgreSQL 물리
계약 완료를 같은 의미로 취급하지 않는다.

### DB 선택은 설정과 테스트 코드에서 명시한다

운영 기본값은 PostgreSQL `DATABASE_URL`이며 연결 실패를 SQLite로 대체하지
않는다. 단위 테스트의 SQLite는 테스트 fixture가 URL과 Engine을 직접
선택한다. `TEST_DATABASE_URL`은 실제 PostgreSQL 통합 테스트가 필요할 때만
명시적으로 소비하며, 값이 없다는 이유로 SQLite를 자동 선택하지 않는다.

### 연결 오류에는 인증정보를 포함하지 않는다

Engine 구성 단계의 오류는 비밀번호를 마스킹한 URL과 예외 종류로 제한한다.
실제 연결 상태 확인은 상세 드라이버 예외를 응답에 포함하지 않고 boolean으로
health endpoint에 전달한다.

### 논리 Schema와 PostgreSQL 물리 타입을 분리한다

Normalized JSON Schema의 배열·null·enum 계약은 유지하면서 PostgreSQL의 배열
저장에는 JSONB를 사용한다. SQLite는 운영 대체 DB가 아니라 빠른 constraint와
API 단위 테스트를 위한 명시적 variant다. GIN index와 named enum을 포함한
실제 물리 계약은 Alembic revision이 권위를 가진다.

### DB constraint와 Validator의 책임을 중복하되 범위를 제한한다

DB에는 연령 범위·순서, 신청일 순서와 enum처럼 저장 후 깨지면 검색 의미가
달라지는 불변 조건만 둔다. 문자열 패턴, provenance 내부 구조, 배열 원소
중복과 품질 admission은 Normalized Validator와 후속 B4 importer가
담당한다.

### source-scoped nullable 식별자는 이번 Slice에서 유지한다

Normalized Schema가 허용하는 `external_id=null`과 기존 unique constraint를
그대로 유지한다. 현재 두 API의 null external ID 거부와 PostgreSQL 원자적
upsert는 B3에서 구현한다.

## 검증 결과

### B0 검증 (Backend 환경 구성 전)

- Backend 의존성 확인:
  `uv run python -B -c "import sqlalchemy, fastapi, pytest, pydantic"` 실패.
  현재 `uv` CPython 3.14 환경에 `sqlalchemy`가 없음
- Backend 테스트:
  `uv run python -B -m pytest backend/tests -q` 미실행. 현재 환경에
  `pytest`가 없어 명령이 종료 코드 1로 실패했으며 테스트 성공으로 기록하지
  않음
- Python 구문 검사:
  `uv run python -B -m py_compile backend/app/models/policy.py
  backend/tests/conftest.py` 통과
- 문서 검증기 단위 테스트:
  `uv run python -B -m unittest tests.test_validate_docs -v` 10건 통과
- 문서 검증:
  `uv run python -B scripts/validate_docs.py` 통과
- 공백 검사: `git diff --check` 통과

### B1 검증

- Backend 환경:
  `uv venv .venv`와
  `uv pip install --python .venv\Scripts\python.exe
  -r backend\requirements.txt`로 저장소 전용 환경을 구성함.
  CPython 3.14.5, SQLAlchemy 2.0.51, pytest 9.1.1 사용
- Backend B1 단위·health 테스트:
  `.venv\Scripts\python.exe -B -m pytest
  backend/tests/test_database.py backend/tests/test_health.py -q` 10건 통과
- Backend 전체 테스트:
  `.venv\Scripts\python.exe -B -m pytest backend/tests -q` 14건 통과
- Python 구문 검사:
  `uv run python -B -m py_compile backend/app/core/config.py
  backend/app/core/database.py backend/app/api/v1/endpoints/health.py
  backend/tests/conftest.py backend/tests/test_database.py` 통과
- 문서 검증기 단위 테스트:
  `uv run python -B -m unittest tests.test_validate_docs -v` 10건 통과
- 문서 검증:
  `uv run python -B scripts/validate_docs.py` 통과
- 실제 PostgreSQL 연결 검증: B1에서는 실행하지 않음. B6 범위에서 별도
  검증하며 SQLite 결과를 PostgreSQL 성공으로 기록하지 않음
- 경고:
  - Starlette TestClient의 `httpx` 사용 방식 deprecation 1건
  - `seed_importer.py`와 SQLAlchemy default의 `datetime.utcnow()` 관련
    deprecation 36건. timezone-aware 저장을 다루는 B2에서 검토함
- 공백 검사: `git diff --check` 통과

### B2 검증

- B2 ORM·Migration 단위 테스트:
  `.venv\Scripts\python.exe -B -m pytest
  backend/tests/test_policy_model.py backend/tests/test_migrations.py -q`
  13건 통과
- Backend 전체 테스트:
  `TEST_DATABASE_URL`을 설정한
  `.venv\Scripts\python.exe -B -m pytest backend/tests -q` 28건 통과
- PostgreSQL offline upgrade SQL:
  `cd backend` 후
  `..\.venv\Scripts\python.exe -B -m alembic upgrade head --sql` 통과.
  JSONB 8개, timezone-aware timestamp, named enum 3개, GIN index 2개와
  constraint 생성을 확인함
- PostgreSQL offline downgrade SQL:
  `cd backend` 후
  `..\.venv\Scripts\python.exe -B -m alembic downgrade
  20260728_0001:base --sql` 통과. index·테이블·enum 제거 SQL을 확인함
- 실제 PostgreSQL upgrade·JSONB 왕복·downgrade:
  PostgreSQL 17.10 공식 Windows portable 바이너리로 일회성 cluster를
  `127.0.0.1:55432`에 실행하고 빈 `cheongnyeon_alimi_test` DB에서
  `backend/tests/test_postgresql_migration.py` 1건 통과. 실제 upgrade,
  JSONB 배열·provenance와 timezone 절대 시각 왕복, 연령 constraint 거부,
  downgrade 후 Policy 테이블과 named enum 3개 제거를 확인함
- 테스트 환경 정리:
  PostgreSQL은 Windows 서비스로 설치하지 않았고 검증 후 서버를 중지한 뒤
  저장소 밖 임시 ZIP·바이너리·cluster를 제거함. Docker·WSL·VS Code 확장은
  B2 실행에 사용하지 않음
- Normalized·Fixture 회귀 확인:
  `.venv\Scripts\python.exe -B -m pytest tests/test_normalization.py
  tests/test_data_fixtures.py -q`는 23건 중 22건 통과, 결정적 산출물 비교 1건
  실패. B2는 Fixture·Seed를 변경하지 않았으며 Windows checkout의 committed
  JSON은 CRLF, 생성기는 LF를 만들어 newline 정규화 후 byte가 일치함을
  확인했다. `scripts/build_data_fixtures.py --check`도 같은 원인으로 12개
  JSON을 outdated로 보고하며 범위 밖 Data 재현성 문제로 남김
- 테스트 경고:
  Starlette TestClient의 `httpx` 사용 방식 deprecation 1건. B2 DB 계약과
  무관해 수정하지 않음
- 확인된 계약 위험:
  Normalized `source_id`에는 최대 길이가 없지만 PostgreSQL의 source-scoped
  unique·B-tree index는 key 크기 제한을 받는다. 현재 source ID는 최대
  27자라 문제가 없으며, 논리 Schema 상한 추가는 Data·Backend 공동 결정이
  필요하므로 B2에서 변경하지 않음

## 남은 작업

- B3: 현재 두 API의 external ID admission과 PostgreSQL 원자적 upsert
- B4: Schema 검증, transaction과 rollback을 적용한 Seed importer
- B5: Repository와 Policy API 기준선
- B6: 실제 PostgreSQL 통합 검증

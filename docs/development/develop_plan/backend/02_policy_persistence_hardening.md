# Backend Policy Persistence Hardening Forest 개발 계획

## 계획 정보

- 번호: Backend 02
- 담당 영역: Backend
- 상태: approved
- 선행 Forest:
  [Backend Policy Baseline](01_policy_baseline.md)
- 관련 브랜치: `feature/backend/policy-baseline-v2`
- 현재 Slice: 구현 시작 전
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
- 잘못된 날짜·시각·필수값을 `null`, 현재 시각이나 빈 문자열로 보정하지
  않는다.
- `valid`와 `partial`은 적재 가능하고 `invalid`와 Schema 위반은 거부한다.
- Data Schema의 nullable 계약과 DB uniqueness가 충돌하면 Data와 공동
  결정하고 한쪽에서 임의로 확정하지 않는다.
- 배열과 provenance의 `JSON`, PostgreSQL `JSONB` 또는 별도 테이블 선택은
  검색 요구, 호환성과 Migration을 검토한 뒤 코드·문서에 동일하게 반영한다.
- 실제 실행한 테스트와 DB 종류만 개발 기록에 남긴다.

## Slice 계획

### B0 - Backend 기준선 정합성 복구

- 상태: pending
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

### B1 - PostgreSQL 연결과 테스트 DB 경계

- 상태: pending
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

### B2 - Policy ORM과 Alembic Migration

- 상태: pending
- 목적: Normalized 계약의 물리적 저장 구조를 Migration으로 고정한다.
- 선행 조건:
  - B1 완료
  - 배열과 provenance 저장 방식 공동 결정
- 주요 작업:
  - 31개 필드의 컬럼 타입, null과 배열 보존 검토
  - 날짜와 timezone-aware 수집 시각 저장
  - unique constraint와 필요한 기본 인덱스
  - 초기 Policy Alembic revision 생성
  - upgrade와 downgrade 검증
- 산출물:
  - Policy ORM과 Alembic revision
- 완료 기준:
  - 빈 PostgreSQL에서 `alembic upgrade head` 성공
  - ORM metadata와 Migration Schema 일치
  - downgrade 또는 깨끗한 DB 재구성 검증

### B3 - 식별자와 upsert 규칙

- 상태: pending
- 목적: Seed와 이후 재수집 결과의 중복 생성을 막는다.
- 선행 조건:
  - B2 완료
- 주요 작업:
  - `(source_id, external_id)` uniqueness 검증
  - nullable `external_id`의 DB 처리 방안 공동 결정
  - 조회 후 update 또는 PostgreSQL 원자적 upsert 중 실제 방식 확정
  - inserted, updated, unchanged, skipped와 failed 구분
  - 동일 Seed 재실행과 경계 사례 테스트
- 산출물:
  - 식별·upsert 결정과 구현
- 완료 기준:
  - 동일 Seed 재실행 후 중복 0건
  - null external ID의 기대 동작이 테스트와 문서에 일치
  - 동시 또는 반복 실행 경계가 명시됨

### B4 - 검증 우선 Seed importer

- 상태: pending
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

### B5 - Repository와 Policy API 기준선

- 상태: pending
- 목적: HTTP, 비즈니스 흐름과 DB 조회 책임을 분리한다.
- 선행 조건:
  - B4 완료
- 주요 작업:
  - Route → Service → Repository 구조
  - `GET /api/v1/policies`
  - `GET /api/v1/policies/{policy_id}`
  - pagination과 기본 category·region·status 필터
  - valid 기본 노출과 partial opt-in 정책
  - provenance 일반 사용자 API 비노출
  - 404와 query 오류 응답
- 산출물:
  - Policy Repository, Service와 API 계약
- 완료 기준:
  - 목록·상세·pagination·필터·404 테스트 통과
  - partial 노출 규칙이 목록과 상세에서 일관됨
  - provenance 사용자 응답 노출 0건

### B6 - Backend PostgreSQL 검증

- 상태: pending
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

## 검증 계획

- Backend 단위·API 테스트
- Alembic upgrade와 downgrade
- PostgreSQL 연결 성공·실패
- Seed 정상·재실행·Schema 위반·rollback
- null·빈 배열·날짜·provenance 보존
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

- Backend 의존성과 PostgreSQL 테스트 환경의 재현 방법이 확정돼야 한다.
- 배열과 provenance의 물리적 저장 방식은 검색 요구와 SQLite 단위 테스트
  필요성을 함께 검토해야 한다.
- nullable external ID와 DB uniqueness의 최종 규칙은 Data와 공동 결정한다.
- 자유 키워드 검색과 인덱스 최적화는 이 Forest 범위가 아니다.

## 관련 문서

- [개발 계획 안내](../README.md)
- [Backend Policy Baseline](01_policy_baseline.md)
- [Policy Data Database Integration](../integration/02_policy_data_database_integration.md)
- [Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [역할과 책임](../../../governance/role_assignment.md)
- [API 문서 안내](../../../api/README.md)

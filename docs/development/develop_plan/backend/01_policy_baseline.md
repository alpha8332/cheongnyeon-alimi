# Backend 01 Policy Baseline Forest 개발 계획

## 계획 정보

- 담당 영역: Backend
- 상태: completed
- 대상 기간: 백엔드 정책 데이터 모델 및 기본 API 구축 Forest
- 관련 브랜치: `feature/backend/policy-baseline`
- 현재 Slice: Backend 0, 1, 2 전체 완료

- 개발 기록:
  [Backend Baseline Forest 개발 기록](../../development_notes/backend/policy_baseline.md)

## 목적

Data Pipeline Forest에서 생성한 `NormalizedProgram` 1.0.0 기반의 canonical
JSON Seed (`data/seeds/initial_programs.json`)를 수용하는 SQLAlchemy 모델,
Seed importer CLI와 정책 목록·상세 조회 API의 기초 구현을 제공한다.
Migration과 실제 PostgreSQL 적재를 포함한 운영 저장 기준은 후속
[Backend 02](02_policy_persistence_hardening.md)에서 완성한다.

## 범위

- `NormalizedProgram` 1.0.0 31개 필드에 대응하는 SQLAlchemy ORM `Policy`
  모델과 Alembic 환경
- `(source_id, external_id)` 복합 unique constraint와 조회 후 insert·update
  방식의 Seed 재적재
- `data/seeds/initial_programs.json` 적재용 Python CLI Importer (`python -m app.cli.import_seed`)
- 범용 SQLAlchemy `JSON` 컬럼의 provenance 보존 및 일반 사용자 API 비노출
- `application_start`, `application_end` Date 파싱과
  `application_period_text` 원문 동시 보존
- `GET /api/v1/policies` 목록 조회 (카테고리, 지역, 신청상태, valid 품질 기본 필터 및 페이징)
- `GET /api/v1/policies/{policy_id}` 상세 조회
- API 및 Importer 단위/통합 테스트 (`pytest backend/tests`)

## 범위 밖

- 사용자 인증 및 OAuth, 즐겨찾기/알림 API (후속 Backend Forest)
- LLM 기반 추천 및 검색 (후속 Integration Forest)
- Docker / Docker Compose 실환경 배포 컨테이너 구성 (Integration/Deploy Forest)

## 선행 조건

- Data 6 (`fixture_seed_contract.md`)의 `NormalizedProgram` 1.0.0 canonical Seed 준비 완료
- Backend 1-A ~ 5-A 소비 방향 검토 완료. 실제 PostgreSQL upsert, JSONB,
  Migration과 transaction 검증은 Backend 02에서 수행
- 백엔드 실행 환경에 `pytest`, `sqlalchemy`, `alembic`, `pydantic` 패키지 준비

## 공통 설계 원칙

- Seed 데이터는 `source_id + external_id`를 고유 식별 경계로 사용한다.
- `data_quality_status`가 `valid` 및 `partial`인 모든 정규화 레코드를 DB에 보존하되, 사용자 API는 기본적으로 `valid` 레코드만 반환한다.
- API 응답 Schema는 DB에 저장한 provenance를 노출하지 않으며, 관리자 전용
  API가 필요한 시점에 분리한다.
- 날짜와 함께 원문 기간 문자열(`application_period_text`)을 보존한다.

## Slice 계획

### Backend 0 - DB Model 및 Alembic 환경

- 상태: completed
- 목적: `NormalizedProgram` 1.0.0에 맞춘 DB Schema 및 ORM 모델을 정의한다.
- 작업:
  - `backend/app/models/policy.py` ORM 작성
  - `(source_id, external_id)` 복합 유니크 인덱스 지정
  - `provenance`, `categories`, `regions` 범용 `JSON` 컬럼
  - Alembic Migration 환경 구성
- 완료 기준:
  - SQLAlchemy 모델이 정상 로드되고 테이블 생성됨
  - 실제 revision 생성과 PostgreSQL 적용은 Backend 02로 이관

### Backend 1 - Seed Importer CLI

- 상태: completed
- 목적: `data/seeds/initial_programs.json`을 DB에 Upsert 방식으로 적재한다.
- 작업:
  - `backend/app/services/seed_importer.py` 로직 구현
  - `backend/app/cli/import_seed.py` CLI 명령어 추가
  - `(source_id, external_id)` 조회 후 insert·update로 재적재 검증
- 완료 기준:
  - `python -m app.cli.import_seed` 실행 시 initial_programs.json 4건(valid 2, partial 2)이 DB에 성공적으로 적재됨

### Backend 2 - Policy API Endpoints 및 테스트

- 상태: completed

- 목적: 정책 목록 및 상세 조회 API를 제공한다.
- 작업:
  - `backend/app/schemas/policy.py` Pydantic DTO 정의
  - `GET /api/v1/policies` 목록 API (페이징, 필터, valid 기본 적용)
  - `GET /api/v1/policies/{policy_id}` 상세 API
  - `pytest backend/tests` 단위 및 통합 테스트 작성
- 완료 기준:
  - 목록/상세 API가 200 OK와 올바른 JSON 응답을 반환하고 단위 테스트 통과

## 검증 계획

- `python -m app.cli.import_seed` CLI 실행 및 적재 건수/오류 검증
- pytest 백엔드 단위/통합 테스트: `python -m pytest backend/tests`
- 문서 검증 스크립트: `python scripts/validate_docs.py`

## Forest 완료 기준

- `initial_programs.json` 4건이 DB에 정상적재됨
- `GET /api/v1/policies` 및 `GET /api/v1/policies/{policy_id}`가 200 OK 응답을 반환함
- 관련 단위 테스트 및 `validate_docs.py` 검증을 통과함
- `docs/development/development_notes/backend/policy_baseline.md`에 최종 결과가 기록됨

## 후속 이관

다음 항목은 이 기초 Forest의 완료 결과가 아니며
[Backend Policy Persistence Hardening](02_policy_persistence_hardening.md)에서
구현·검증한다.

- 실제 Alembic revision과 PostgreSQL upgrade·downgrade
- PostgreSQL 연결 실패 시 SQLite 자동 fallback 제거
- PostgreSQL JSONB와 원자적 `ON CONFLICT DO UPDATE`
- Schema 위반 거부, transaction과 rollback
- Repository 계층과 실제 PostgreSQL 통합 테스트

## 위험과 미확정 사항

- PostgreSQL DB 연결 환경변수와 명시적인 테스트 DB 경계
- 배열과 provenance의 PostgreSQL 물리 저장 방식
- nullable external ID와 DB uniqueness의 경계

## 관련 문서

- [Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [Backend Baseline Forest 개발 기록](../../development_notes/backend/policy_baseline.md)
- [Backend Policy Persistence Hardening](02_policy_persistence_hardening.md)

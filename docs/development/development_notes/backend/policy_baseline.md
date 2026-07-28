# Backend Baseline Forest 개발 기록

## 작업 정보

- 시작일: 2026-07-28
- 상태: completed
- 영역: backend
- 관련 계획:
  [`01_policy_baseline.md`](../../develop_plan/backend/01_policy_baseline.md)
- 관련 Slice: Backend 0~Backend 2
- 브랜치: `feature/backend/policy-baseline`

## 목적

Data Pipeline Forest에서 생성한 `NormalizedProgram` 1.0.0 기반 canonical
JSON Seed (`data/seeds/initial_programs.json`)를 수용하는 SQLAlchemy 모델,
조회 후 insert·update 방식의 Seed importer CLI와 정책 목록·상세 조회 API
기준선을 구현했다.

## Forest 범위

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

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| Backend 0 | completed | ORM 모델과 Alembic 환경 구성. 실제 revision은 후속 Forest로 이관 |
| Backend 1 | completed | Seed CLI와 조회 후 insert·update 재적재 구현 |
| Backend 2 | completed | Policy 목록·상세 API와 테스트 7개 구현 |

## 구현 내용

### Backend 0 - DB Model 및 Alembic 환경

- `docs/data/fixture_seed_contract.md` 문서의 백엔드 검토 상태를 `reviewed`로 업데이트함.
- 1-A ~ 5-A 소비 방향(CLI Importer, 재적재, valid 기본 필터링,
  provenance 비노출, Date+Text 동시 보존)을 검토함.
- `backend/app/models/policy.py` ORM과 Alembic metadata 연결 환경을 작성함.
- 실제 Alembic revision과 PostgreSQL 적용은 구현하지 않았음.

### Backend 1 - Seed Importer CLI 구축

- `backend/app/services/seed_importer.py`에서 `initial_programs.json`을 읽고
  `(source_id, external_id)`로 기존 행을 조회한 뒤 insert 또는 update함.
- `backend/app/cli/import_seed.py` CLI 스마트 명령 구축 (`python -m app.cli.import_seed`).
- CLI가 `Base.metadata.create_all()`을 호출하고 PostgreSQL 연결 실패 시
  SQLite로 자동 fallback하는 현재 한계가 있음.

### Backend 2 - Policy API Endpoints 및 테스트

- `backend/app/schemas/policy.py` Pydantic DTO (provenance 비노출) 작성.
- `backend/app/api/v1/endpoints/policies.py` 에 목록/상세 API 및 valid 품질 기본 필터 구현.
- `backend/tests/test_policies.py`와 `conftest.py`를 포함해 Backend 테스트 함수
  7개를 작성함. 기존 기록에는 통과로 남아 있으나 Backend 02 B0에서는 현재
  실행 환경에 SQLAlchemy가 없어 재실행하지 못함.


## 주요 변경 파일

- `backend/app/models/policy.py`
- `backend/app/services/seed_importer.py`
- `backend/app/cli/import_seed.py`
- `backend/app/schemas/policy.py`
- `backend/app/api/v1/endpoints/policies.py`
- `backend/app/core/database.py`
- `backend/alembic/env.py`
- `backend/tests/conftest.py`
- `backend/tests/test_policies.py`
- `docs/data/fixture_seed_contract.md`
- `docs/development/develop_plan/backend/01_policy_baseline.md`
- `docs/development/development_notes/backend/policy_baseline.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`

## 설계 결정

1. **Seed Importer (1-A)**: `python -m app.cli.import_seed` CLI 기반 독립 배치 실행 방식으로 구현하여 서버 타임아웃 위험을 차단함.
2. **재적재 경계 (2-A)**: `(source_id, external_id)` 복합 unique constraint와
   조회 후 insert·update를 사용함. PostgreSQL 원자적 upsert는 후속
   Backend 02 범위임.
3. **품질 필터링 (3-A)**: `data_quality_status` (valid, partial) 전량 DB 적재 후 일반 API는 `valid` 기본 필터링 제공.
4. **Provenance 보존 (4-A)**: `provenance`를 범용 `JSON` 컬럼에 보존하고
   일반 API DTO에서는 비노출함.
5. **날짜 동시 보존 (5-A)**: `application_start`, `application_end` Date와
   `application_period_text` 원문을 함께 저장함.

## 검증 결과

- 기존 구현 기록: Backend 테스트 7개 통과
- Backend 02 B0 재검토: 현재 `uv` Python 환경에 SQLAlchemy가 없어 Backend
  테스트 미실행
- Backend 02 B0에서 문서 검증과 공백 검사는 후속 개발 기록에 별도로 기록

## 남은 작업

다음 항목은
[Backend Policy Persistence Hardening](../../develop_plan/backend/02_policy_persistence_hardening.md)
Forest로 이관했다.

- 실제 Alembic revision과 PostgreSQL 적용
- PostgreSQL 실패 시 SQLite 자동 fallback 제거
- PostgreSQL JSONB와 원자적 upsert
- Schema 검증, transaction과 rollback
- Repository 계층과 PostgreSQL 통합 테스트

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

Data Pipeline Forest에서 생성한 `NormalizedProgram` 1.0.0 기반 canonical JSON Seed (`data/seeds/initial_programs.json`)를 수용할 DB 모델, PostgreSQL/SQLite 호환 ORM, Upsert Seed Importer CLI 및 정책 목록·상세 조회 API를 구현한다.

## Forest 범위

- `NormalizedProgram` 1.0.0 31개 필드 준수 SQLAlchemy ORM `Policy` 모델 및 Alembic Migration
- `(source_id, external_id)` 복합 유니크 인덱스 및 PostgreSQL `ON CONFLICT DO UPDATE` (Upsert) 적재 로직
- `data/seeds/initial_programs.json` 적재용 Python CLI Importer (`python -m app.cli.import_seed`)
- `JSONB` 기반 provenance 데이터 보존 및 일반 사용자 API 패킷 비노출
- `start_date`, `end_date` (Date) 파싱 및 `raw_apply_period` (Text) 동시 보존
- `GET /api/v1/policies` 목록 조회 (카테고리, 지역, 신청상태, valid 품질 기본 필터 및 페이징)
- `GET /api/v1/policies/{policy_id}` 상세 조회
- API 및 Importer 단위/통합 테스트 (`pytest backend/tests`)

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| Backend 0 | completed | DB Schema, ORM 모델 및 Alembic Migration 구성 완료 |
| Backend 1 | completed | `python -m app.cli.import_seed` CLI 적재 및 Upsert 구현 완료 |
| Backend 2 | completed | Policy 목록/상세 API 및 pytest 단위/통합 테스트 7건 통과 |

## 구현 내용

### Backend 0 - DB Model 및 Migration 준비

- `docs/data/fixture_seed_contract.md` 문서의 백엔드 검토 상태를 `reviewed`로 업데이트함.
- 1-A ~ 5-A 의사결정 사항(CLI Importer, Upsert, valid 전용 필터링, JSONB provenance, Date+Text 동시 보존)을 승인 및 확정함.
- `backend/app/models/policy.py` ORM 작성 및 PostgreSQL/SQLite 호환 DB Engine 설정 완료.

### Backend 1 - Seed Importer CLI 구축

- `backend/app/services/seed_importer.py` 로 `initial_programs.json` 4건의 Seed 데이터를 읽어 `(source_id, external_id)` 기준 Upsert 적재 로직 작성.
- `backend/app/cli/import_seed.py` CLI 스마트 명령 구축 (`python -m app.cli.import_seed`).

### Backend 2 - Policy API Endpoints 및 테스트

- `backend/app/schemas/policy.py` Pydantic DTO (provenance 비노출) 작성.
- `backend/app/api/v1/endpoints/policies.py` 에 목록/상세 API 및 valid 품질 기본 필터 구현.
- `backend/tests/test_policies.py` 및 `conftest.py` 작성하여 pytest 7건 통과.


## 주요 변경 파일

- `docs/data/fixture_seed_contract.md`
- `docs/development/develop_plan/backend/01_policy_baseline.md`
- `docs/development/development_notes/backend/policy_baseline.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`

## 설계 결정

1. **Seed Importer (1-A)**: `python -m app.cli.import_seed` CLI 기반 독립 배치 실행 방식으로 구현하여 서버 타임아웃 위험을 차단함.
2. **Upsert 경계 (2-A)**: `(source_id, external_id)` 복합 유니크 인덱스와 PostgreSQL `ON CONFLICT DO UPDATE`로 동일 정책 재수집/Seed 업데이트 시 최신화 보장.
3. **품질 필터링 (3-A)**: `data_quality_status` (valid, partial) 전량 DB 적재 후 일반 API는 `valid` 기본 필터링 제공.
4. **Provenance 보존 (4-A)**: `provenance`를 `JSONB` 컬럼으로 보존하고 일반 API DTO에서는 비노출.
5. **날짜 동시 보존 (5-A)**: `start_date`, `end_date` (Date)와 `raw_apply_period` (Text)를 동시 작성하여 범위 검색과 원문 텍스트 보존 병행.

## 검증 결과

- `python scripts/validate_docs.py` 문서 검증 스크립트 통과

## 남은 작업

- `backend/app/models/policy.py` ORM 모델 구현
- Alembic Migration 생성 및 적용
- `backend/app/services/seed_importer.py` 및 `backend/app/cli/import_seed.py` 작성
- `backend/app/api/v1/endpoints/policies.py` API 작성 및 pytest 테스트 코드 구현

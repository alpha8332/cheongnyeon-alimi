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

Data Pipeline Forest에서 생성한 `NormalizedProgram` 1.0.0 기반의 canonical JSON Seed (`data/seeds/initial_programs.json`)를 수용하고, PostgreSQL DB 모델, Upsert Importer CLI 및 정책 목록·상세 조회 API를 구축한다. Frontend가 Mock 데이터를 대체하고 실제 백엔드 API 계약으로 연동할 수 있는 기본 백엔드 파이프라인을 완료한다.

## 범위

- `NormalizedProgram` 1.0.0 31개 필드 준수 SQLAlchemy ORM `Policy` 모델 및 Alembic Migration
- `(source_id, external_id)` 복합 유니크 인덱스 및 PostgreSQL `ON CONFLICT DO UPDATE` (Upsert) 적재 로직
- `data/seeds/initial_programs.json` 적재용 Python CLI Importer (`python -m app.cli.import_seed`)
- `JSONB` 기반 provenance 데이터 보존 및 일반 사용자 API 패킷 비노출
- `start_date`, `end_date` (Date) 파싱 및 `raw_apply_period` (Text) 동시 보존
- `GET /api/v1/policies` 목록 조회 (카테고리, 지역, 신청상태, valid 품질 기본 필터 및 페이징)
- `GET /api/v1/policies/{policy_id}` 상세 조회
- API 및 Importer 단위/통합 테스트 (`pytest backend/tests`)

## 범위 밖

- 사용자 인증 및 OAuth, 즐겨찾기/알림 API (후속 Backend Forest)
- LLM 기반 추천 및 검색 (후속 Integration Forest)
- Docker / Docker Compose 실환경 배포 컨테이너 구성 (Integration/Deploy Forest)

## 선행 조건

- Data 6 (`fixture_seed_contract.md`)의 `NormalizedProgram` 1.0.0 canonical Seed 준비 완료
- Backend 1-A ~ 5-A 의사결정 승인 완료 (CLI Importer, Upsert, valid 전용 필터링, JSONB provenance, Date+Text 동시 보존)
- 백엔드 실행 환경에 `pytest`, `sqlalchemy`, `alembic`, `pydantic` 패키지 준비

## 공통 설계 원칙

- Seed 데이터는 `source_id + external_id`를 고유 식별 경계로 사용한다.
- `data_quality_status`가 `valid` 및 `partial`인 모든 정규화 레코드를 DB에 보존하되, 사용자 API는 기본적으로 `valid` 레코드만 반환한다.
- API 응답 스키마는 `JSONB` provenance를 노출하지 않으며, 관리자 전용 API가 필요한 시점에 분리한다.
- 텍스트 정제 및 파싱 실패에 대비해 원문 기간 문자열(`raw_apply_period`)을 항상 보존한다.

## Slice 계획

### Backend 0 - DB Model 및 Migration

- 상태: completed
- 목적: `NormalizedProgram` 1.0.0에 맞춘 DB Schema 및 ORM 모델을 정의한다.
- 작업:
  - `backend/app/models/policy.py` ORM 작성
  - `(source_id, external_id)` 복합 유니크 인덱스 지정
  - `provenance` (JSONB), `categories` (JSONB), `regions` (JSONB)
  - Alembic Migration 환경 구성
- 완료 기준:
  - SQLAlchemy 모델이 정상 로드되고 테이블 생성됨

### Backend 1 - Seed Importer CLI

- 상태: completed
- 목적: `data/seeds/initial_programs.json`을 DB에 Upsert 방식으로 적재한다.
- 작업:
  - `backend/app/services/seed_importer.py` 로직 구현
  - `backend/app/cli/import_seed.py` CLI 명령어 추가
  - `ON CONFLICT DO UPDATE` 로 최신화 검증
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

## 위험과 미확정 사항

- PostgreSQL DB 연결 환경변수 (`DATABASE_URL`) 및 로컬 SQLite fallback 지원 필요성
- array 타입 (categories, regions) DB 처리 방식: PostgreSQL native ARRAY vs JSONB 호환성 (SQLite fallback 지원 위해 JSONB 고려)

## 관련 문서

- [Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [Backend Baseline Forest 개발 기록](../../development_notes/backend/policy_baseline.md)

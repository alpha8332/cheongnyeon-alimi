# Data 03 Recurrent Collection and Quality Operations

## 작업 정보

- 기간: `2026-08-10`~
- 상태: in-progress
- 담당 영역: Data
- 작업 브랜치: `feature/data/recurrent-quality-operations`
- merge target: `develop`
- 시작 SHA: `0b9485b`
- 계획: [Data 03 개발 계획](../../develop_plan/data/03_recurrent_collection_quality_operations.md)

## 목적

반복 수집의 business 변경과 실행 metadata 변경을 구분하고, 중복·검증 실패·
DB 실패를 안전한 집계로 분리하는 결정적 기반을 만든다.

## Forest 범위

- 동일·수정·중복·실패 합성 계약 Fixture
- importer business 비교 필드와 실행 내 duplicate 판정
- `validate`·`persist` 안전한 오류 단계
- 실제 PostgreSQL·CollectionRun Migration은 DTL4-2B 범위

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| DTL4-2A | 완료 | fixture 6개 시나리오, metadata-only unchanged, duplicate·안전 오류 단계 단위 검증 |
| DTL4-2B | 대기 | CollectionRun 컬럼·Migration과 전용 PostgreSQL 반복·rollback 검증 |

## 구현 내용

- Policy 변경 비교를 business field와 `collected_at`·provenance collection
  metadata로 분리했다. metadata만 달라지면 기존 row와 `updated_at`을 바꾸지
  않고 `unchanged`로 판정한다.
- 한 import 실행에 같은 `(source_id, external_id)`가 반복되면 첫 후보만
  처리하고 이후 후보를 `duplicate_identity`, stage `validate`로 집계한다.
- Import 결과에 `duplicate`를 추가하고 Seed·Runtime CLI의 안전한 요약에
  포함했다.
- Schema·identity 문제는 `validate`, SQLAlchemy write 실패는 `persist`로
  기록한다. 오류 message는 Import 결과와 CLI에 포함하지 않는다.
- canonical Seed batch의 invalid·admission 실패 원자성과 DB write 실패 전체
  rollback은 유지했다.

## 주요 변경 파일

- `backend/app/services/seed_importer.py`
- `backend/app/cli/import_seed.py`
- `scripts/import_runtime_data.py`
- `data/fixtures/contracts/recurrent_quality_cases.json`
- `backend/tests/test_recurrent_quality_operations.py`
- `docs/architecture/collection_run_database.md`
- `docs/data/fixture_seed_contract.md`

## 설계 결정

- collection metadata-only 재실행에서는 최신 metadata로 row를 덮어쓰지 않는다.
  PostgreSQL과 portable 경로가 같은 `unchanged`·timestamp 의미를 유지하기
  위한 선택이다.
- duplicate는 invalid·skipped로 합치지 않는다. 첫 canonical 후보 외 입력을
  쓰지 않되 관리자 집계의 별도 의미를 유지한다.
- 현재 CollectionRun Schema에 없는 duplicate·rejected를 기존 count에 억지로
  넣지 않는다. 물리 저장은 Migration을 포함하는 DTL4-2B에서 수행한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| DTL4-2A importer·CLI 집중 pytest | 37건 통과, 기존 Starlette deprecation warning 1건 |
| Data unittest 전체 회귀 | 139건 통과 |
| Backend pytest 전체 회귀 | 110건 통과, 15건 skip, 기존 deprecation warning 2건 |
| Fixture·Seed 결정성 | 14개 파일 통과 |
| PostgreSQL 통합 pytest | 4건 skip: `TEST_DATABASE_URL` 미주입, DTL4-2B에서 실제 실행 필요 |
| 문서 검증·diff 검사 | `scripts/validate_docs.py`, `git diff --check` 통과 |

## 남은 작업

- `duplicate_count`·`rejected_count` CollectionRun 컬럼과 Alembic Migration
- Seed·Runtime CLI의 두 집계 영속 연결과 Backend 05 소비 대조
- 전용 PostgreSQL에서 metadata-only·수정·중복·write rollback 실제 검증
- DTL4-2B 완료 뒤 전체 Data·Backend 회귀와 문서 검증

# Data 03 Recurrent Collection and Quality Operations

## 작업 정보

- 기간: `2026-08-10`~
- 상태: completed
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
- CollectionRun 반복 품질 count Migration과 Seed·Runtime 영속 연결
- 전용 PostgreSQL에서 반복 실행·rollback 실제 검증

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| DTL4-2A | 완료 | fixture 6개 시나리오, metadata-only unchanged, duplicate·안전 오류 단계 단위 검증 |
| DTL4-2B | 완료 | CollectionRun 컬럼·Migration·영속 연결과 전용 PostgreSQL 반복·rollback 검증 통과 |

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
- CollectionRun에 `duplicate_count`와 `rejected_count`를 추가하고 nonnegative
  제약을 새 count까지 확장하는 Alembic revision `20260810_0005`를 추가했다.
- invalid는 검증 실패, rejected는 invalid와 identity admission 거부를 포함한
  전체 제외 입력으로 분리했다. duplicate는 별도 비실패 집계로 유지하고 현재
  identity admission 거부는 `skipped` 대신 `rejected`로 기록한다.
- Seed·Runtime CLI 종료 이력에 두 품질 count를 연결했다. Runtime은 replay
  invalid와 importer rejected를 중복 없이 합쳐 저장한다.
- 전용 PostgreSQL 통합 테스트에 metadata-only unchanged, business update,
  실행 내 duplicate, CollectionRun count 영속과 강제 write 실패 전체 rollback을
  구성했다.
- BE 기준점 `f7ffca4`는 Backend 04 구현과 Backend 05 draft 계획까지 포함한다.
  Backend 05 계획의 안전한 상태·집계·오류 소비 및 Raw·credential 비노출 방향은
  현재 Data 계약과 호환된다. 실제 DTO·endpoint는 아직 없어 후속 Backend 05에서
  신규 count를 소비해야 한다.

## 주요 변경 파일

- `backend/app/services/seed_importer.py`
- `backend/app/models/collection_run.py`
- `backend/app/services/collection_runs.py`
- `backend/app/cli/import_seed.py`
- `scripts/import_runtime_data.py`
- `backend/alembic/versions/20260810_0005_collection_run_quality_counts.py`
- `data/fixtures/contracts/recurrent_quality_cases.json`
- `backend/tests/test_recurrent_quality_operations.py`
- `tests/integration/test_recurrent_quality_operations.py`
- `docs/architecture/collection_run_database.md`
- `docs/data/fixture_seed_contract.md`

## 설계 결정

- collection metadata-only 재실행에서는 최신 metadata로 row를 덮어쓰지 않는다.
  PostgreSQL과 portable 경로가 같은 `unchanged`·timestamp 의미를 유지하기
  위한 선택이다.
- duplicate는 invalid·skipped로 합치지 않는다. 첫 canonical 후보 외 입력을
  쓰지 않되 관리자 집계의 별도 의미를 유지한다.
- invalid는 rejected의 부분집합이므로 두 값을 합산해 전체 제외 수로 해석하지
  않는다. 기존 `skipped_count`는 호환을 위해 남기되 현재 importer 판정에는
  사용하지 않는다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| DTL4-2A importer·CLI 집중 pytest | 37건 통과, 기존 Starlette deprecation warning 1건 |
| DTL4-2B 집중 pytest | 40건 통과, 초기 PostgreSQL 2건 skip 후 전용 DB 전체 검증 통과 |
| Data unittest 전체 회귀 | 139건 통과 |
| Backend pytest 전체 회귀 | 전용 PostgreSQL 포함 125건 통과, 기존 deprecation warning 2건 |
| Fixture·Seed 결정성 | 14개 파일 통과 |
| PostgreSQL 통합 pytest | 전용 `cheongnyeon_alimi_test`에서 5건 통과, 기존 warning 1건 |
| 문서 검증·diff 검사 | `scripts/validate_docs.py`, `git diff --check` 통과 |

테스트 종료 뒤 전용 DB에는 기존 테스트 관례대로 `alembic_version`만 남았고,
Policy·CollectionRun 테이블과 DTL4-2B 강제 실패 함수는 제거됐다.

## 남은 작업

- Backend 05 관리자 DTO가 두 집계와 invalid·rejected 포함 관계를 같은 의미로
  소비하는지 대조
- Integration 09 통계·로그 correlation이 같은 count 의미와 비노출 경계를
  유지하는지 확인

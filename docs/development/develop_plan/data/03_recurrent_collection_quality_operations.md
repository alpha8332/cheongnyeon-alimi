# Data 03 Recurrent Collection and Quality Operations Forest 개발 계획

## 계획 정보

- 번호: Data 03
- 담당 영역: Data
- 상태: in-progress
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 선행 Forest: Integration 05 Contract Baseline, Data 02 Release Dataset Bootstrap
- 후속 Forest: Backend 05, Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/data/recurrent-quality-operations`
- 현재 진행: DTL4-2A fixture·판정·실패 단계 기반 구현 완료, DTL4-2B 대기

## 목적

승인된 수집 범위를 반복 실행했을 때 unchanged·updated·duplicate·failed를
재현 가능하게 구분하고, 정상 정책과 실패 자료를 섞지 않으면서 관리자 API가
소비할 안전한 품질 통계를 제공한다.

## 범위

- 같은 snapshot과 변경 snapshot의 반복 수집·재처리
- `(source_id, external_id)` identity 기반 중복 방지
- inserted·updated·unchanged·rejected·failed 집계
- partial·invalid와 실행 실패의 분리
- 변경 감지의 비교 필드와 timestamp 의미
- CollectionRun과 품질 통계 연결
- 관리자 DTO에 제공 가능한 분류·건수·안전한 오류 요약 검토
- Raw·credential·DB 파일 Git 비추적 재검증

## 범위 밖

- 자동 Scheduler와 분산 worker
- 관리자 품질 수정·승인 UI
- 원본 오류의 자동 보정과 Source 근거 없는 필드 승격
- Raw payload·stack trace·credential의 관리자 노출
- 새 외부 Source 추가

## 선행 조건

- Integration 05의 품질 노출·수동 실행 계약이 승인돼야 한다.
- Data 02의 실제 snapshot·idempotency·identity 기준선을 재확인한다.
- 전용 PostgreSQL 테스트 DB와 Git 제외 Runtime 경로를 준비한다.

## 공통 설계 원칙

- Raw와 정규화 실패를 성공 정책에 섞거나 조용히 폐기하지 않는다.
- Source 근거 없는 필드 승격과 오류 자동 보정을 하지 않는다.
- 같은 identity에 대한 재실행은 중복 row를 만들지 않는다.
- 관리자 소비에는 분류·건수·안전한 요약만 제공한다.

## DTL4-2A 구현 기준

- business 변경 비교에서 `collected_at`과 `provenance`를 제외한다. 이 두 값만
  달라진 재실행은 저장 row를 바꾸지 않고 `unchanged`로 판정한다.
- 실행 내 같은 `(source_id, external_id)`는 첫 후보만 canonical 입력으로
  사용하고 이후 후보는 `duplicate`로 별도 집계한다.
- importer가 다루는 오류 단계는 `validate`와 `persist`로 제한하며 예외
  메시지·Raw·credential 대신 안전한 code·exception class만 유지한다.
- canonical Seed의 invalid·identity admission 실패 시 전체 batch를 쓰지 않는
  기존 원자성은 유지한다. Runtime의 invalid 격리는 replay 단계에서 accepted
  program만 importer로 넘기는 기존 경계를 사용한다.
- `duplicate_count`와 `rejected_count`의 CollectionRun 컬럼·Migration·관리자
  소비 연결은 DTL4-2B PostgreSQL 작업에서 구현한다.

## Slice 계획

### DQ0 - 반복 실행 기준선

- 현재 importer·upsert·CollectionRun 계약과 실제 snapshot 기준선을 확인한다.
- 동일 입력 재실행에서 unchanged 이외의 변화가 없는지 고정한다.

### DQ1 - 변경·중복 감지

- 수정 표본에서 updated와 unchanged를 구분한다.
- Source 내부·실행 간 duplicate가 추가 row를 만들지 않는지 검증한다.

### DQ2 - 실패 격리와 품질 통계

- fetch·extract·normalize·validate·persist 실패를 안전한 분류로 집계한다.
- 실패 자료가 성공 정책과 transaction 경계를 오염시키지 않는지 확인한다.

### DQ3 - 관리자 소비와 실제 재검증

- Backend 05가 소비할 DTO 초안을 Data 의미와 대조한다.
- 실제 또는 승인 fixture로 재실행·수정·실패 시나리오를 재검증한다.

## Forest 완료 기준

- 동일 snapshot 재실행이 중복 row와 거짓 updated를 만들지 않음
- 수정 snapshot에서 updated·unchanged가 결정적으로 구분됨
- 실패·partial·invalid가 서로 다른 의미로 집계되고 정상 데이터와 격리됨
- 관리자 통계에 Raw·credential·stack trace가 노출되지 않음
- Data 단위 테스트와 PostgreSQL 통합 테스트가 실제로 통과함
- 품질 기준 문서·개발 기록·관리자 소비 문서가 실제 결과와 일치함

## 검증 계획

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
$env:TEST_DATABASE_URL = '<dedicated-postgresql-test-url>'
.\.venv\Scripts\python.exe -B -m pytest tests/integration -q
python scripts/validate_docs.py
git diff --check
```

## 위험과 미확정 사항

- 수정 감지 비교 필드에 수집 시각 같은 실행 메타데이터를 포함하면 모든 행이
  거짓 updated가 될 수 있어 비교 범위를 먼저 확정해야 한다.
- Source가 같은 정책을 다른 external ID로 다시 발행하면 현재 identity만으로
  의미 중복을 자동 확정할 수 없다. 후보 통계와 자동 병합을 구분한다.
- 실패 격리 transaction이 기존 importer의 원자성 계약과 충돌하면 Backend·DB
  공동 검토 없이는 구조를 바꾸지 않는다.

## 관련 문서

- [Release Dataset Bootstrap](02_release_dataset_bootstrap.md)
- [v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- [CollectionRun Admin API](../backend/05_collection_run_admin_api.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)

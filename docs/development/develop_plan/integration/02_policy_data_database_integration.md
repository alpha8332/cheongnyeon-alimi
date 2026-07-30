# Policy Data Database Integration Forest 개발 계획

## 계획 정보

- 번호: Integration 02
- 담당 영역: Data·Backend 공동 통합
- 상태: in-progress
- 대상 기간: 데이터 담당 2주차
- 선행 Forest:
  [Backend Policy Persistence Hardening](../backend/02_policy_persistence_hardening.md)
- 권장 브랜치: `feature/database/pipeline-integration`
- 현재 Slice: D4 completed (D0 Frontend review-pending)
- 참고 계획:
  `opensource_plan/주차별 개발 목표_데이터담당/2주차 개발 목표.docx`

## 목적

1주차에 완성한 수집·추출·정규화·검증 파이프라인의 canonical 데이터를
PostgreSQL에 안전하게 적재하고, Backend와 Frontend가 실제로 소비할 수 있는
공통 데이터 계약을 확정한다.

```text
canonical Seed 또는 Runtime Raw
→ NormalizedProgram 검증
→ Backend Import Service
→ PostgreSQL
→ Policy Repository
→ GET /api/v1/policies
→ Frontend Mock 또는 실제 API
```

이 Forest는 Collector와 Normalizer를 다시 구현하지 않는다. Backend ORM,
Migration과 importer 자체의 완성은 Backend 02가 담당하고, 이 Forest는 Data
결과와 Backend 저장·조회 경계의 통합을 담당한다.

## 범위

- Backend·Frontend의 NormalizedProgram 1.0.0 공동 검토
- 31개 Normalized 필드의 DB 매핑과 손실 검증
- canonical Seed → PostgreSQL → Repository → API 통합 테스트
- 저장된 Runtime Raw의 재처리와 DB 적재 연결
- 적재 idempotency, 품질 분기와 실행 결과 요약
- 선택적인 최소 수집 실행 이력 협의
- API 소비 자료와 Frontend 인계
- Data 6와 Data Pipeline Forest 완료 게이트

## 범위 밖

- Collector, Extractor와 Normalizer 재구현
- 새로운 API Source와 HTML Collector
- 전체 데이터 수집과 외부 API 자동 순회
- Scheduler와 정기 수집
- 수정·삭제 감지
- 소스 간 유사 정책 병합
- 자유 키워드 검색, 추천과 검색 인덱스 최적화
- 관리자 수동 실행 API와 상세 대시보드
- Dockerfile, Compose와 Production 배포

## 선행 조건

- Backend 02에서 Migration, import service, Repository와 API 기준선을 제공한다.
- `NormalizedProgram` 1.0.0과 canonical Seed 4건을 입력 계약으로 사용한다.
- Backend 검토 결과는 Fixture·Seed 계약에 기록돼 있어야 한다.
- PostgreSQL 테스트 DB와 실행 방법이 제공돼야 한다.
- Backend 의존성 manifest에 실제 사용 라이브러리와 테스트 의존성이 반영돼
  있어야 한다.
- 실제 Runtime Raw는 Git에 포함하지 않는다.
- Frontend 승인이 없으면 Data 6를 완료 처리하지 않는다.

## 공통 설계 원칙

- Data는 Schema·품질 검증과 손실 검사를 담당하고 SQLAlchemy ORM을 직접
  생성하지 않는다.
- Backend는 DB 모델, Migration, transaction과 Repository를 담당한다.
- Seed와 Runtime은 검증된 program iterable을 받는 같은 import service를
  사용한다.
- `valid`와 `partial`은 소비 가능 데이터이고 `invalid`는 DB와 정상 API에서
  제외한다.
- null, 빈 배열, enum, 날짜, 원문 text와 provenance를 임의로 축약하지 않는다.
- 자동 테스트는 Git에 포함된 합성 Fixture를 사용한다.
- 합성 Raw Fixture → Extractor → Normalizer → Validator → importer 흐름을
  CI에서 검증해 운영 Raw 없이 Runtime adapter를 재현한다.
- Runtime Raw 검증은 추가 외부 호출이 없는 선택적인 로컬 smoke test로
  분리한다.
- 최소 CollectionRun은 Seed 적재와 Runtime 연결이 완료된 뒤 구현 여부를
  결정하며 Forest 완료의 필수 조건으로 두지 않는다.

## Slice 계획

### D0 - 데이터 계약 공동 확정

- 상태: review-pending
- 기술 검토: completed
- 외부 검토: Frontend pending
- 목적: NormalizedProgram 1.0.0과 canonical Seed의 실제 소비 가능성을
  확인한다.
- 선행 조건:
  - Backend 검토 증거 확인
- 주요 작업:
  - Backend importer·API 소비 결과 검토
  - Frontend TypeScript·Mock 소비 항목 전달
  - nullable, 배열, 일정·상태, partial과 provenance 정책 검토
  - 변경이 필요한 필드만 최소 변경
  - 계약 버전 유지 또는 변경 판단
- 산출물:
  - Fixture·Seed 공동 검토 기록
  - 변경 요청 또는 명시적 승인
- 완료 기준:
  - Backend가 Seed 적재 가능 여부를 확인
  - Frontend가 타입·Mock 소비 가능 여부를 확인
  - 미확정 필드가 승인되거나 변경 계획에 기록
  - 두 영역 승인 전에는 Data 6를 완료 처리하지 않음

### D1 - NormalizedProgram → DB 매핑 검증

- 상태: completed
- 목적: JSON 계약과 관계형 DB 구조 사이의 손실 없는 매핑을 확정한다.
- 선행 조건:
  - D0의 Backend 검토 완료
  - Backend 02의 ORM과 Migration 제공
- 주요 작업:
  - 31개 필드의 JSON 타입, DB 컬럼, null, 배열과 API 노출 여부 매핑
  - `category_text`·`categories`, `region_text`·`regions` 동시 보존
  - 일정·상태, 날짜와 원문 기간 text 동시 보존
  - 조건 배열, 출처, 수집 시각, provenance와 품질 보존
  - source-scoped identity와 upsert 규칙 확인
  - 현재 두 API의 external ID admission과 향후 Source 확장 경계 확인
- 산출물:
  - DB 매핑표
  - Seed 원본과 DB 조회 결과 비교 기준
- 완료 기준:
  - 필드 누락 0건
  - null·빈 배열 변형 0건
  - 다중 category와 provenance 손실 0건

### D2 - Seed → PostgreSQL 통합 테스트

- 상태: completed
- 목적: canonical Seed가 Schema 검증부터 DB 조회까지 통과하는지 확인한다.
- 선행 조건:
  - D1 완료
  - Backend 02 PostgreSQL 검증 완료
- 테스트 흐름:

  ```text
  data/seeds/initial_programs.json
  → Normalized Schema 검증
  → Backend Import Service
  → PostgreSQL
  → Policy Repository
  ```

- 필수 테스트:
  - 정상 Seed와 partial Seed 적재
  - invalid와 Schema 위반 거부
  - 동일 Seed 재실행
  - 배열, null, 날짜, category와 provenance 보존
  - transaction rollback
  - DB 조회 결과와 Seed 비교
- 권장 위치:
  `tests/integration/test_seed_to_database.py`
- 완료 기준:
  - Seed 4건 → DB 4건 → Repository 조회 4건
  - 재실행 중복 0건
  - invalid 적재와 주요 필드 손실 0건
  - 외부 네트워크 없이 재현 가능

### D3 - Policy API 첫 통합

- 상태: completed
- 목적: DB에 적재된 정책을 합의된 API로 조회한다.
- 선행 조건:
  - D2 완료
- 주요 작업:
  - `GET /api/v1/policies`
  - `GET /api/v1/policies/{policy_id}`
  - 기본 valid 조회와 partial opt-in
  - pagination과 현재 합의된 기본 필터
  - Seed 값과 API 응답 비교
  - provenance 사용자 API 비노출 확인
  - 상세 API의 partial 노출 정책 확인
  - `docs/api/policies.md`에 query, pagination, DTO와 오류 계약 작성
- 산출물:
  - Seed → DB → API 통합 테스트
  - `docs/api/policies.md` 요청·응답 계약과 합성 예시
- 완료 기준:
  - 기본 조회 valid 2건
  - partial 포함 조회 4건
  - 상세 조회와 404 동작 확인
  - nullable·배열·partial·422·500 계약 문서화
  - API 응답의 값 손실과 provenance 노출 0건

### D4 - Runtime Raw 재처리와 DB 적재

- 상태: completed
- 목적: 기존 Runtime Raw를 추가 API 호출 없이 같은 DB 경계로 적재한다.
- 선행 조건:
  - D2 완료
- 권장 흐름:

  ```text
  runtime/raw/
  → Raw reload
  → Extractor
  → Normalizer
  → Validator
  → accepted programs
  → Backend Import Service
  ```

- 주요 작업:
  - Seed와 분리된 Runtime 입력 adapter
  - source와 limit을 받는 명시적 CLI
  - dry-run, valid·partial·invalid 집계
  - source 단위 또는 합의된 batch transaction
  - validation rejection은 DB transaction 전에 분리
  - DB failure는 해당 batch rollback
  - 같은 Runtime 재실행 idempotency
  - Raw payload, 인증 파라미터와 키 로그 제외
- 산출물:
  - Runtime import 진입점
  - 합성 Raw Fixture 기반 전체 처리 자동 테스트
  - Runtime Raw가 있을 때 선택적인 로컬 smoke 기록
- 완료 기준:
  - 자동 테스트는 외부 네트워크 없이 통과
  - Runtime 검증 시 추가 API 호출 0회
  - invalid 적재와 중복 0건
  - 실행 요약과 실제 DB 결과 일치

### D5 - 최소 실행 이력 협의

- 상태: optional
- 목적: 향후 관리자 기능을 위한 최소 실행 이력의 필요성과 저장 위치를
  결정한다.
- 선행 조건:
  - D2와 D4 완료
- 검토 필드:
  - `run_id`, `source_id`, `run_type`, `trigger_type`
  - 시작·종료 UTC 시각과 상태
  - 요청·Raw·추출·accepted·partial·invalid 건수
  - inserted·updated·skipped·failed 건수
  - 안전한 `error_type`
- 선택지:
  - 최소 `collection_runs` DB 레코드
  - Backend DB 구조가 불안정하면 실행 결과 JSON
  - 후속 운영 Forest로 연기
- enum 후보:
  - `run_type`: `seed_import`, `runtime_import`, `collection`
  - `trigger_type`: `cli`, `scheduler`, `admin`
- 완료 기준:
  - 구현 여부, 책임 영역과 후속 완료 기준이 문서 또는 Issue에 기록
  - 구현하지 않아도 D0~D4와 D6 완료를 막지 않음

### D6 - Frontend 인계와 Data 6 종료

- 상태: pending
- 목적: Frontend가 Mock 또는 실제 API로 정책 기능을 구현할 계약을 제공한다.
- 선행 조건:
  - D0와 D3 완료
- 주요 작업:
  - Policy 목록·상세 API 문서
  - TypeScript 타입 생성 기준
  - nullable·배열·일정·상태·partial 표시 규칙
  - 빈 목록, 오류와 Mock → API 전환 안내
  - Frontend 승인 또는 실제 소비 테스트 기록
  - Data 6, Data Pipeline 계획과 개발 기록 상태 갱신
- 산출물:
  - `docs/api/` Policy API 계약
  - 갱신된 Fixture·Seed 공동 검토 기록
  - Integration 개발 기록
- 완료 기준:
  - Frontend 승인 또는 소비 테스트 증거
  - Backend·Frontend 공동 검토 완료
  - Data 6와 Data Pipeline Forest 완료
  - 승인 전에는 `기술 구현 완료 / Frontend 승인 대기`로 유지

## 의존 순서

```text
Backend 02
    ↓
D0 → D1 → D2 → D3
           ↓
          D4 → D5(optional)
           ↓
          D6
```

D0의 Frontend 검토 요청과 D1 매핑 초안은 Backend 02 후반에 병렬로 진행할 수
있다. D6 최종 승인은 D3의 실제 API 결과를 확인한 뒤 기록한다.

## 검증 계획

- 전체 Data 회귀 테스트
- canonical Seed와 rejected Fixture Schema 검증
- `uv run python -B scripts/build_data_fixtures.py --check`
- 합성 Raw Fixture → Extracted → Normalized → PostgreSQL 자동 테스트
- Seed → PostgreSQL → Repository → API 통합 테스트
- Runtime Raw → Normalized → PostgreSQL 통합 테스트
- 동일 입력 재실행과 rollback
- null·빈 배열·enum·날짜·category와 provenance 보존
- 비밀정보와 운영 Raw의 Git 제외
- `uv run python -B scripts/validate_docs.py`
- `git diff --check`
- canonical JSON byte 결정성을 위한 line ending 검사

실제 Runtime Raw와 PostgreSQL 환경이 없으면 해당 검증을 성공으로 기록하지
않고 합성 Fixture 자동 테스트와 미실행 항목을 구분한다.

## Forest 완료 기준

- D0~D4와 D6 완료
- NormalizedProgram 계약 확정 또는 변경 내용 동기화
- canonical Seed 4건의 PostgreSQL 적재와 Repository 조회
- 동일 Seed와 Runtime 재실행 중복 0건
- invalid와 Schema 위반 적재 0건
- null·빈 배열·enum·날짜·category와 provenance 손실 0건
- `/api/v1/policies` 목록·상세 조회
- 합성 Fixture 기반 통합 테스트와 Data 회귀 테스트 통과
- 실제 실행한 PostgreSQL·Runtime 검증 결과 기록
- API, Data와 Integration 문서 동기화
- Frontend 승인 후 Data 6 완료

D5는 선택 사항이며 구현하지 않아도 Forest 완료를 막지 않는다. 다만
수집 실행 이력의 구현 또는 후속 Forest 여부는 기록해야 한다.

## 위험과 미확정 사항

- Backend 02가 완료되기 전에 Data가 SQLAlchemy 구현을 대신하면 책임 경계와
  병합 충돌이 생긴다.
- PostgreSQL 테스트 DB 제공 방식은 별도 Integration·Deploy 결정이 필요할
  수 있다.
- Backend 02에서 확정한 JSONB 물리 매핑과 현재 두 API의 external ID
  admission이 Normalized 계약을 손실 없이 보존하는지 D1에서 확인한다.
  향후 Source의 대체 ID 규칙은 이 Forest에서 일반화하지 않는다.
- Windows line ending 설정은 canonical JSON의 byte 결정성 검사를 방해할 수
  있다. `data/fixtures/**/*.json`, `data/seeds/*.json`,
  `data/schema/*.json`의 LF를 `.gitattributes`로 고정하는 최소 변경을
  우선 검토하고 저장소 전체 파일을 기계적으로 재작성하지 않는다.
- Runtime Raw는 Git에 포함되지 않으므로 CI 완료 기준은 합성 Fixture에 둔다.
- Frontend 승인이 없으면 기술 흐름이 동작해도 Data 6 공동 완료 기준은
  충족하지 않는다.
- Data 코드가 Backend 실행 환경을 공유하면 새 Python 라이브러리를
  Backend의 합의된 manifest에 반영하고 별도 root manifest를 임의로 만들지
  않는다.

## 관련 문서

- [개발 계획 안내](../README.md)
- [Backend Policy Persistence Hardening](../backend/02_policy_persistence_hardening.md)
- [Backend Policy Baseline](../backend/01_policy_baseline.md)
- [Data Pipeline Forest 계획](../data/01_data_pipeline.md)
- [Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [정규화 규칙](../../../data/normalization_rules.md)
- [역할과 책임](../../../governance/role_assignment.md)
- [시스템 흐름](../../../architecture/system_flow.md)
- [API 문서 안내](../../../api/README.md)

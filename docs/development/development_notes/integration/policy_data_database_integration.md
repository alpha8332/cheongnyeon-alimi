# Policy Data Database Integration Forest 개발 기록

## 작업 정보

- 시작일: 2026-07-29
- 상태: completed
- 영역: Data·Backend 공동 통합
- 브랜치: `feature/database/pipeline-integration`
- 관련 계획:
  [`02_policy_data_database_integration.md`](../../develop_plan/integration/02_policy_data_database_integration.md)
- 현재 Slice: D0~D6 completed

## 목적

Data 파이프라인의 `NormalizedProgram` 1.0.0과 canonical Seed를 Backend
PostgreSQL 저장·조회 경계 및 Frontend 소비 계약과 공동 확정한다. D0에서는
기존 Backend 검증 증거를 확인하고 Frontend 타입·Mock 인계 경계를 명시하며,
D1에서는 31개 필드의 JSON·DB·API 매핑과 무손실 비교 기준을 확정했다.
D2에서는 canonical Seed가 Schema 검증부터 PostgreSQL과 Repository 조회까지
통과하는 전용 통합 테스트 경계를 확정했다. D3에서는 실제 PostgreSQL에
적재된 Seed를 Policy 목록·상세 API로 조회하고 공개 응답 계약을 확정했다.
D4에서는 저장된 Runtime Raw를 외부 재호출 없이 재처리해 같은 Backend
Importer와 PostgreSQL source batch transaction으로 연결했다. D5에서는
향후 관리자 기능이 사용할 Seed·Runtime 최소 실행 이력을 별도 PostgreSQL
transaction으로 저장한다.
D6에서는 실제 Backend OpenAPI와 원격 Frontend 구현을 대조해 사용자 Policy
DTO·endpoint·Mock 전환 인계 기준과 Frontend 변경 요청을 확정한다.

## Forest 범위

- Backend·Frontend의 NormalizedProgram 1.0.0 공동 검토
- 31개 Normalized 필드의 DB 매핑과 손실 검증
- canonical Seed와 Runtime 결과의 PostgreSQL·Policy API 통합
- 적재 idempotency, 품질 분기와 실행 결과 요약
- API 소비 자료와 Frontend 인계

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| D0 | completed | Backend·Frontend 데이터 계약 공동 승인 완료 |
| D1 | completed | 31필드 JSON·Importer·ORM·PostgreSQL·API 매핑과 비교 기준 확정 |
| D2 | completed | canonical Seed 4건의 Schema → Importer → PostgreSQL → Repository 통합 검증 |
| D3 | completed | 실제 PostgreSQL 기반 목록·상세·필터·오류 API 계약 검증 |
| D4 | completed | 최신 source Raw 회차의 재처리·품질 분리·원자적 DB 적재와 재실행 검증 |
| D5 | completed | Seed·Runtime CollectionRun 모델·Migration·상태·집계 이력 구현 |
| D6 | completed | Frontend API 소비·자동·실제 API·브라우저 렌더링 검증 후 Data 6 종료 |

## 구현 내용

### D0 - 데이터 계약 공동 확정

- Backend 02 B6의 Migration → canonical Seed 4건 → Repository → API 종단
  검증과 31개 필드 비교 결과를 D0의 Backend 승인 증거로 확인했다.
- Backend importer는 `valid`·`partial`만 적재하고 공개 API는 기본
  `valid`, 명시적인 `include_partial=true`에서만 `partial`을 노출한다.
  `invalid`는 적재·공개 대상이 아니다.
- nullable 단일 값, 항상 배열인 복수 값, 일정·상태의 분리, 날짜와 원문
  text의 동시 보존, DB provenance 보존·사용자 API 비노출 정책이 기존
  Schema·Seed·Backend 코드·API 문서에서 일치함을 검토했다.
- 변경이 필요한 필드를 발견하지 않아 `NormalizedProgram` 버전은 `1.0.0`을
  유지하고 JSON Schema, Python 모델, Fixture와 Seed는 변경하지 않았다.
- Frontend가 Policy DTO 타입과 Mock 소비 테스트를 작성할 때 확인할 nullable,
  배열, 일정·상태, partial, provenance와 timezone 경계를
  `fixture_seed_contract.md`에 명시했다.
- 현재 브랜치에는 Policy DTO 타입과 Mock 소비 코드가 없고, 원격 Frontend
  브랜치의 구현은 공개 API 계약과 달라 Data 담당이 이를 대신 수정하거나
  승인으로 간주하지 않았다.
- D0는 저장된 합성 Seed와 기존 Backend 증거를 검토하는 단계이므로 외부 API를
  호출하거나 인증키를 사용하지 않았다.
- canonical JSON의 byte 결정성을 위해 `.gitattributes`에서 Fixture, Seed와
  Schema JSON을 `text eol=lf`로 고정하고 공식 재생성 스크립트로 기존 산출물을
  LF byte로 정규화했다.

### D1 - NormalizedProgram → DB 매핑 검증

- Normalized 31개 필드의 JSON 타입, PostgreSQL 컬럼 타입, nullability,
  importer 변환과 공개 API 노출 여부를
  `docs/architecture/policy_database_mapping.md`에 확정했다.
- Schema properties·required, `NormalizedProgram.FIELD_NAMES`, importer write
  key와 ORM의 system field 제외 컬럼이 모두 같은 31개 집합임을 자동
  검증한다.
- 공개 `PolicyRead`는 Normalized 31개 중 `provenance`만 제외하고 DB 생성
  필드 `id`·`created_at`·`updated_at`을 추가하는 집합임을 자동 검증한다.
- nullable 단일 값 16개와 non-null JSONB 배열 8개를 명시하고 ORM
  nullability·PostgreSQL dialect type과 대조했다.
- canonical Seed 4건의 importer 변환에서 string·integer·enum·null·배열과
  provenance는 exact equality, 날짜는 ISO date, 수집 시각은 UTC absolute
  instant로 비교했다.
- `category_text`·`categories`, `region_text`·`regions`, 원문 기간 text·날짜,
  일정·상태를 각각 동시에 보존하는 매핑을 확인했다.
- `(source_id, external_id)` unique constraint와 현재 두 Source의 비어 있지
  않은 external ID admission을 고정했다. 다른 Source의 null ID는
  `unsupported_null_external_id`로 유지하고 대체 ID를 일반화하지 않았다.
- Schema, Fixture, Seed, ORM, Migration과 API 응답 계약의 변경이 필요한
  충돌은 발견하지 않았다. 외부 API와 인증키는 사용하지 않았다.

### D2 - Seed → PostgreSQL 통합 테스트

- Integration 소유 경계인
  `tests/integration/test_seed_to_database.py`에 canonical Seed → Schema
  Validator → Backend Import Service → PostgreSQL → Policy Repository 흐름을
  한 테스트로 고정했다.
- canonical Seed 4건이 `valid` 2건·`partial` 2건으로 검증되고 최초 적재,
  DB 직접 조회와 Repository 조회에서 모두 4건인지 확인한다.
- system field를 제외한 DB 31개 필드를 Seed 원본과 비교한다. scalar·null·
  JSONB 배열·provenance는 exact equality, 날짜는 ISO date, `collected_at`은
  UTC absolute instant 기준을 사용한다.
- 같은 Seed 재실행은 4건 모두 `unchanged`이고 insert·update 및
  `updated_at` 변경이 없음을 확인한다.
- Schema required 필드가 없는 batch와 명시적인 `invalid` 품질 후보는
  적재하지 않으며, batch 안의 정상 후보도 함께 쓰이지 않는 preflight
  원자성을 확인한다.
- PostgreSQL trigger로 두 번째 write를 강제 실패시켜 첫 번째 write까지
  rollback되고 기존 canonical 4건만 남는지 확인한다.
- 테스트 입력은 저장소의 합성 Seed만 사용하고 외부 API·인증키·네트워크를
  사용하지 않는다.

### D3 - Policy API 첫 통합

- `tests/integration/test_seed_to_policy_api.py`에서 Alembic Migration으로
  실제 PostgreSQL 테스트 DB를 구성하고 canonical Seed 4건을 Backend
  Import Service로 적재한 뒤 FastAPI 목록·상세 endpoint를 호출한다.
- 기본 목록은 `valid` 2건, `include_partial=true` 목록은 valid·partial
  전체 4건이며 응답의 `total`, `page`, `limit`과 page 범위 밖 빈
  `items`를 검증한다.
- category·region은 배열 원소 완전 일치, status는 enum 일치로 필터링하고
  partial 포함 범위와 결합한 실제 PostgreSQL JSONB 조회 결과를 확인한다.
- 공개 응답은 canonical Seed의 31개 필드 중 `provenance`만 제외한 30개
  필드를 보존하며 DB 생성 필드 `id`·`created_at`·`updated_at`을 추가한다.
  nullable·빈 배열·다중 category·날짜·timezone 시각을 Seed와 비교한다.
- valid 상세는 기본 공개하고 partial 상세는 기본 404,
  `include_partial=true`에서만 200으로 공개한다. 존재하지 않는 ID도 같은
  404 응답으로 처리해 품질 비노출 원인을 구분하지 않는다.
- page·limit·category·status·region·boolean query와 `policy_id` path 타입
  위반의 422 구조를 검증한다.
- 강제로 발생시킨 처리되지 않은 오류의 500 응답이 고정된 공통 메시지만
  반환하고 내부 예외 메시지를 노출하지 않는지 확인한다.
- 생산 API·Schema·Fixture·Seed·DB Migration은 변경하지 않았으며 외부
  API와 인증키를 사용하지 않았다.
- D3 기술 구현은 완료로 유지하되 실제 API의 Frontend 소비 검토는 D6
  완료 조건이므로 `docs/index.md` 인계 보드에 `INT-02-D3-FE`를
  `review-pending`으로 등록했다.

### D4 - Runtime Raw 재처리와 DB 적재

- `collectors/runtime.py`에 Git 제외 `runtime/raw` 또는 주입한 합성 Raw
  root를 안전하게 탐색하고 `RawDocumentStore.load` → source Extractor →
  Normalizer·Validator로 재처리하는 adapter를 구현했다.
- source의 가장 최신 `list_response`를 회차 경계로 선택하고 그
  `document_id`를 부모로 참조하는 list item만 처리한다. detail은 선택 item과
  external ID가 같고 목록 수집 시각 이후인 문서 중 최신 한 건만 결합한다.
- `--limit`은 list item에만 적용하며 부모 response와 연결 detail은 처리
  문서 수에 포함하되 제한 수에는 포함하지 않는다. 최신 response에 item이
  없으면 과거 회차로 조용히 후퇴하지 않는다.
- Normalizer 결과의 valid·partial program만 기존 Backend
  `import_programs`에 전달하고 invalid는 transaction 전에 분리한다. invalid
  issue에는 오류 코드·JSON path와 기여 Raw document ID만 보존한다.
- `backend/app/services/runtime_importer.py`는 Data adapter의 accepted
  program dict를 기존 Backend importer에 전달할 뿐 Collector가 ORM이나
  SQLAlchemy Session을 알게 하지 않는다.
- `scripts/import_runtime_data.py`에 `--source`, `--raw-root`, `--limit`,
  `--dry-run` CLI를 추가했다. 출력은 처리·DB 집계와 안전한 issue metadata만
  포함하고 Raw payload, source URL query, 인증키를 출력하지 않는다.
- CLI는 Backend 전역 development engine을 재사용하지 않고 `echo=False`인
  전용 engine·session factory를 생성한다. DB URL·비밀번호와 SQL parameter가
  출력되지 않도록 하고 종료 시 session과 engine을 정리한다.
- source별 accepted batch는 한 DB transaction으로 처리한다. DB write 하나가
  실패하면 accepted batch 전체를 rollback하고 validation invalid와 DB
  failure를 별도 수치로 유지한다.
- 같은 Runtime Raw 재실행은 `(source_id, external_id)` 경계에서
  `unchanged`로 집계하며 중복 row를 만들지 않는다.
- `opensource_plan` 원안은 진입점과 idempotency를 D3·D4로 나누고
  `--include-partial`을 제안한다. 현재 Forest는 이를 D4로 통합하고 공통
  계약에서 valid·partial을 모두 소비 가능 데이터로 확정했으므로, 현재
  코드·API와 충돌하는 선택 옵션을 추가하지 않고 partial을 항상 적재한다.
- 실제 `runtime/raw`는 이 PC에 없어 운영 Raw 성공 smoke는 실행하지 않았다.
  저장 경로 부재가 DB 변경 없이 명확한 종료 코드 1을 반환하는지만 확인했다.
  자동·PostgreSQL 검증은 외부 네트워크 없이 합성 Raw Fixture로 수행했다.

### D5 - 최소 CollectionRun 실행 이력

- 향후 관리자 기능의 기반이 필요하다는 사용자 결정을 근거로 D5의 세 선택지
  중 PostgreSQL `collection_runs` 레코드를 구현했다. 실행 결과 JSON이나
  후속 운영 Forest 연기안은 선택하지 않았다.
- `CollectionRun` ORM과 `20260730_0002` Alembic revision에 UUID `run_id`,
  nullable `source_id`, 실행·trigger·상태 enum, UTC 시작·종료 시각,
  D4 처리·DB count와 안전한 `error_type`을 추가했다.
- source별 Runtime은 실제 `source_id`, 두 source가 섞인 canonical Seed는
  `null`을 저장한다. 이는 NormalizedProgram의 null 계약을 바꾸지 않는 운영
  이력 규칙이다.
- 상태는 시작 시 `running`, 전체 성공 시 `succeeded`, Runtime invalid 일부를
  제외하고 accepted batch를 적재하면 `partial_failure`, 검증·DB·실행 실패는
  `failed`로 확정했다. 품질 `partial`은 허용된 데이터이므로 그 자체로 실행
  실패가 아니다.
- 모든 count의 비음수, terminal 상태의 종료 시각 필수, 종료 시각 순서와
  빈 source ID 금지를 DB constraint로 고정했다. 향후 관리자 조회를 위해
  source·시작 시각·상태 index를 추가했다.
- 공통 `CollectionRunWriter`가 실행 이력을 Policy import와 별도
  session/transaction으로 기록한다. 따라서 Policy rollback 후에도 실패
  이력이 남고, 종료 write 실패 시 `running` row가 운영 확인 지점으로 남는다.
- Seed와 Runtime CLI 실제 실행을 writer에 연결하고 출력에 `run_id`를
  포함했다. D4의 DB 변경 없음 계약을 유지하기 위해 `--dry-run`은 실행
  이력을 만들지 않는다.
- Raw payload, 정책 원문, URL·query, 인증정보, DB 예외 메시지와 상세 실패
  목록은 저장하지 않는다. 실패에는 최대 255자의 예외 class 이름만 저장한다.
- 관리자 조회·수동 실행 API, 인증·권한, Scheduler와 대시보드는 현재 Forest
  범위 밖이다. 후속 착수 조건을 `BE-ADMIN-RUN-HISTORY`로 인계 보드에
  기록했다.

### D6 - Frontend 인계와 Data 6 종료 게이트

- `.venv`의 실제 FastAPI `app.openapi()`에서 `/api/v1/policies`,
  `/api/v1/policies/{policy_id}`, `PolicyRead`와 `PolicyListResponse`를
  추출해 D3 문서와 비교했다. 경로, query, 공개 필드, nullable·배열·enum과
  pagination 계약은 일치했다.
- `docs/api/policies.md`에 정확한 `PolicyDto`·`PolicyListResponse`
  TypeScript 기준, 목록·상세 API Client 예시, Mock → API 변환과
  loading·empty·404·422·500·partial 검증 항목을 추가했다.
- 원격 `feature/frontend/policy-discovery`의 `784a2a8`을 merge 없이
  읽기 전용으로 검토했다. 이 커밋은 canonical Seed 기반 타입·Mock UI를
  구현했지만 현재 공개 API와 다음 차이가 있다.
  - 사용자 타입에 `provenance`와 `invalid`를 포함한
    `NormalizedProgram`을 사용함
  - 존재하지 않는 `/api/v1/programs` 목록·source/external 상세 endpoint를
    호출함
  - 목록 pagination envelope와 DB 숫자 `id` 상세 route를 소비하지 않음
  - 기본 valid 2건과 partial opt-in 대신 Seed 4건을 기본 반환함
  - API 소비 계약을 검증하는 Frontend 테스트가 없음
- 당시 Integration 브랜치에는 `ProgramListPage` 파일이 없었으나 원격
  Frontend 커밋은 `SearchPage`의 default export를 `ProgramListPage`라는
  유효한 별칭으로 import하고 있었다. 이를 존재하지 않는 import 문제로 본
  기록은 잘못된 판단이며 FE 2A 후속 검토에서 정정했다.
- Data·Database 담당 범위를 넘어 Frontend 브랜치를 수정·merge하거나
  Backend API를 변경하지 않았다. D0·D6와 Data 6는 Frontend 조치와 소비
  테스트가 생길 때까지 `action-needed`로 유지한다.

## 주요 변경 파일

- `docs/development/develop_plan/integration/02_policy_data_database_integration.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/integration/policy_data_database_integration.md`
- `docs/development/development_notes/README.md`
- `docs/development/backend_local_setup.md`
- `docs/troubleshooting/backend/windows_postgresql_test_environment.md`
- `docs/troubleshooting/README.md`
- `docs/development/README.md`
- `docs/data/fixture_seed_contract.md`
- `docs/index.md`
- `backend/.env.example`
- `README.md`
- `.gitattributes`
- `backend/tests/test_policy_mapping_contract.py`
- `tests/integration/test_seed_to_database.py`
- `tests/integration/test_seed_to_policy_api.py`
- `collectors/runtime.py`
- `backend/app/services/runtime_importer.py`
- `scripts/import_runtime_data.py`
- `tests/test_runtime_replay.py`
- `tests/test_runtime_import_cli.py`
- `tests/integration/test_runtime_to_database.py`
- `backend/app/models/collection_run.py`
- `backend/app/services/collection_runs.py`
- `backend/alembic/versions/20260730_0002_create_collection_runs.py`
- `backend/app/cli/import_seed.py`
- `backend/app/services/seed_importer.py`
- `backend/tests/test_collection_runs.py`
- `tests/integration/test_collection_run_history.py`
- `docs/architecture/collection_run_database.md`
- `CHANGELOG.md`
- `docs/architecture/policy_database_mapping.md`
- `docs/architecture/README.md`
- `docs/data/data_schema.md`
- `docs/api/policies.md`
- `docs/operations/collector.md`
- `docs/operations/README.md`

## 설계 결정

### Backend 검증 증거와 Frontend 승인을 분리한다

Backend 02의 실제 PostgreSQL 종단 검증은 Backend 소비 가능성을 승인하기에
충분하다. 원격 Frontend 타입·Mock UI가 존재하더라도 공개 API 계약과 다른
상태이므로 소비 승인으로 간주하지 않는다. D0와 Forest는 Frontend 수정과
소비 테스트 또는 명시적 재검토가 생길 때까지 완료하지 않는다.

### canonical Seed와 공개 Policy DTO를 같은 타입으로 취급하지 않는다

canonical Seed는 31개 Normalized 필드와 provenance를 포함한다. 공개 Policy
DTO는 provenance를 제외하고 DB `id`, `created_at`, `updated_at`을 추가한다.
Frontend Mock은 Seed 사례를 재사용할 수 있지만 이 노출 경계를 반영해야 한다.

### 계약 버전은 1.0.0을 유지한다

Schema, Fixture, Seed, Backend importer·ORM과 API 사이에서 D0가 해결해야 할
필드 충돌을 발견하지 않았다. 따라서 소비 코드 부재만을 이유로 계약 버전을
변경하지 않는다.

### 물리 매핑표는 공통 Architecture 문서에 둔다

`docs/data/`는 논리 Schema의 권위를 가지며 PostgreSQL Migration 상세를
포함하지 않는다. 31개 필드 매핑은 Data·Backend·API가 함께 참조하므로
`docs/architecture/policy_database_mapping.md`에 두고 Data와 API 기준
문서에서 연결한다.

### DB nullable과 importer admission을 같은 의미로 취급하지 않는다

`external_id`는 Normalized Schema와 DB에서 nullable이지만 현재 importer는
null identity를 적재하지 않는다. 현재 두 Source는 `missing_external_id`,
아직 합의되지 않은 Source는 `unsupported_null_external_id`로 분리한다.
향후 대체 ID 결정 없이 DB nullable을 제거하거나 임의 ID를 생성하지 않는다.

### 무손실 비교는 타입별로 명시한다

JSONB와 scalar는 exact equality, 날짜는 ISO date, timezone 시각은 UTC
absolute instant로 비교한다. PostgreSQL이 같은 instant를 다른 offset
문자열로 반환하는 것을 손실이나 변경으로 오판하지 않는다.

### 실행 이력은 Policy transaction과 분리한다

정책 write와 같은 transaction에 실행 이력을 넣으면 rollback 시 실패 증거도
사라진다. D5 writer는 별도 session에서 시작 row를 먼저 commit하고 terminal
결과를 다시 commit한다. 이 때문에 Policy commit 후 이력 종료가 실패할 수
있으며, CLI는 이를 성공으로 숨기지 않고 남은 `running` row를 운영 확인
대상으로 둔다.

### dry-run은 실행 이력을 만들지 않는다

D4에서 `--dry-run`은 실제 upsert를 수행한 뒤 모든 DB 변경을 rollback하는
계약이다. D5 이력만 commit하면 기존 계약과 충돌하므로 dry-run에는 writer를
생성하지 않는다. 실제 Seed·Runtime 실행만 관리자 조회 대상이 된다.

## 검증 결과

- 최초 Data 계약 회귀:
  `python -B -m unittest tests.test_normalization tests.test_data_fixtures -v`
  실행 결과 23건 중 22건 통과, 결정적 byte 비교 1건 실패
- 최초 결정적 Fixture 검사:
  `python -B scripts/build_data_fixtures.py --check`가 Windows checkout의
  CRLF와 생성기의 LF 차이로 12개 JSON을 outdated로 판정
- 원인과 조치:
  `.gitattributes`가 없어 checkout EOL이 지정되지 않은 상태였다. Fixture,
  Seed와 Schema JSON을 LF로 고정하고 공식 생성기의 `--write`로 정규화했다.
- 수정 후 Data 계약 회귀와 결정적 Fixture 검사 결과는 아래 최종 검증에
  기록한다.
- 수정 후 Data 계약 회귀:
  `python -B -m unittest tests.test_normalization tests.test_data_fixtures -v`
  23건 통과
- 수정 후 결정적 Fixture 검사:
  `python -B scripts/build_data_fixtures.py --check` 12개 파일 통과
- Backend 단위·통합 테스트:
  이 데스크톱의 전역 Python 3.11.9와 저장소의 Unix 형식 `venv`를 그대로
  사용하지 않고 Windows용 `.venv`를 생성한 뒤 `backend/requirements.txt`를
  설치했다. `.venv`는 Git ignore 대상이며 manifest 변경은 없다.
- PostgreSQL 미설정 Backend 전체 회귀:
  `.venv\Scripts\python.exe -B -m pytest backend/tests -q` 실행 결과
  46건 통과, 명시적인 `TEST_DATABASE_URL`이 필요한 5건 skipped
- PostgreSQL:
  로컬 PostgreSQL 18의 `127.0.0.1:5432`에 전용
  `cheongnyeon_alimi_test` DB를 생성했다. 비밀번호는 코드·명령행·URL·문서에
  넣지 않고 PostgreSQL `pgpass` 임시 파일로만 전달했다.
- 실제 PostgreSQL Backend 전체 회귀:
  비밀번호 없는 `TEST_DATABASE_URL`과 임시 `PGPASSFILE`을 설정해
  `.venv\Scripts\python.exe -B -m pytest backend/tests -q` 51건 통과
- PostgreSQL 검증 범위:
  실제 Alembic upgrade·downgrade, JSONB·enum·timezone 왕복, 원자적 upsert,
  Seed transaction·rollback, Repository 필터와 Seed → DB → API 종단 검증을
  통과했다. 종료 후 Policy 테이블과 enum은 제거되고 빈 `alembic_version`
  테이블만 남아 다음 Migration에 재사용할 수 있다.
- 자격증명 정리:
  검증 후 임시 credential·`pgpass` 파일이 모두 삭제된 것을 확인했다.
- 환경 복구 기록:
  다른 PC의 Unix 가상환경, PostgreSQL 역할 인증과 테스트 DB 생성 과정은
  [Windows PostgreSQL 테스트 환경 복구](../../../troubleshooting/backend/windows_postgresql_test_environment.md)에
  재사용 가능한 해결 절차로 분리했다.
- Backend 경고:
  Starlette TestClient의 `httpx` 사용 방식 deprecation 1건. D0 계약과
  무관해 수정하지 않았다.
- 최초 D1 구조 테스트:
  `.venv\Scripts\python.exe -B -m pytest
  backend/tests/test_policy_mapping_contract.py
  backend/tests/test_policy_model.py backend/tests/test_migrations.py -q`에서
  16건 통과, 1건 실패. SQLAlchemy `ColumnCollection`의 이름이 아니라
  `Column` 객체를 비교한 새 테스트 오류였으며 생산 코드·계약 문제는 아니었다.
- 수정 후 D1 구조·ORM·Migration 테스트:
  같은 명령으로 17건 통과
- D1 PostgreSQL 미설정 Backend 전체 회귀:
  `.venv\Scripts\python.exe -B -m pytest backend/tests -q` 50건 통과,
  PostgreSQL 5건 skipped
- D1 실제 PostgreSQL Backend 전체 회귀:
  로컬 PostgreSQL 18, `cheongnyeon_alimi_test`에서 비밀번호 없는
  `TEST_DATABASE_URL`과 임시 `PGPASSFILE`을 사용해
  `.venv\Scripts\python.exe -B -m pytest backend/tests -q` 55건 통과
- D1 PostgreSQL 결과:
  Migration, canonical Seed 4건의 31필드 DB 왕복, JSONB 다중 category·빈
  배열·provenance, null·enum·날짜·timezone instant, source-scoped upsert와
  공개 API provenance 비노출을 확인했다.
- D1 자격증명 정리:
  PostgreSQL 검증 후 session 환경변수를 제거하고 임시 `pgpass` 파일이 삭제된
  것을 확인했다.
- D1 Data 회귀:
  `.venv\Scripts\python.exe -B -m unittest
  tests.test_normalization tests.test_data_fixtures -v` 23건 통과
- D1 결정적 Fixture 검사:
  `.venv\Scripts\python.exe -B scripts/build_data_fixtures.py --check`
  12개 파일 통과
- D2 PostgreSQL 전용 통합 테스트:
  로컬 PostgreSQL 18의 `cheongnyeon_alimi_test`에서
  `.venv\Scripts\python.exe -B -m pytest
  tests/integration/test_seed_to_database.py -q` 1건 통과
- D2 실제 PostgreSQL 전체 회귀:
  비밀번호 없는 `TEST_DATABASE_URL`과 임시 `PGPASSFILE`을 사용해
  `.venv\Scripts\python.exe -B -m pytest backend/tests tests/integration -q`
  56건 통과, Starlette TestClient deprecation 경고 1건
- D2 PostgreSQL 결과:
  canonical Seed 4건의 valid·partial Schema 분기, 31필드 무손실 DB 왕복,
  Repository 4건 조회, 같은 Seed 4건 unchanged, Schema·invalid 거부와
  PostgreSQL write 실패 시 batch rollback을 확인했다.
- D2 최초 실행 오류:
  설치되지 않은 `psycopg` 드라이버명을 URL에 지정해 DB 접속 전에
  `ModuleNotFoundError`가 발생했다. manifest의 `psycopg2-binary`와 기존
  환경 문서에 맞게 `postgresql+psycopg2://`를 사용해 해결했으며 패키지는
  추가·변경하지 않았다.
- D2 자격증명 정리:
  PostgreSQL 검증 후 임시 credential·`pgpass` 파일의 `Test-Path`가 모두
  `False`임을 확인했다.
- D2 Data 계약 회귀:
  `.venv\Scripts\python.exe -B -m unittest
  tests.test_normalization tests.test_data_fixtures -v` 23건 통과
- D2 결정적 Fixture 검사:
  `.venv\Scripts\python.exe -B scripts/build_data_fixtures.py --check`
  12개 파일 통과
- D2 문서 검증기 단위 테스트:
  `.venv\Scripts\python.exe -B -m unittest tests.test_validate_docs -v`
  10건 통과
- D2 문서 검증:
  `.venv\Scripts\python.exe -B scripts/validate_docs.py` 통과
- D2 공백 검사:
  `git diff --check` 통과
- D3 API·매핑 단위 테스트:
  `.venv\Scripts\python.exe -B -m pytest
  backend/tests/test_policy_api.py
  backend/tests/test_policy_mapping_contract.py -q` 10건 통과
- D3 PostgreSQL 전용 통합 테스트:
  로컬 PostgreSQL 18의 `cheongnyeon_alimi_test`에서
  `.venv\Scripts\python.exe -B -m pytest
  tests/integration/test_seed_to_policy_api.py -q` 1건 통과,
  Starlette TestClient deprecation 경고 1건
- D3 실제 PostgreSQL 전체 회귀:
  비밀번호 없는 `TEST_DATABASE_URL`과 임시 `PGPASSFILE`을 사용해
  `.venv\Scripts\python.exe -B -m pytest backend/tests tests/integration -q`
  57건 통과, Starlette TestClient deprecation 경고 1건
- D3 자격증명 정리:
  PostgreSQL 검증 후 임시 `pgpass` 파일의 `Test-Path`가 `False`임을
  확인했다. 이번 방식은 credential XML을 생성하지 않았다.
- D3 PostgreSQL 결과:
  기본 valid 2건·partial 포함 4건, pagination·JSONB 배열 필터·status,
  공개 DTO 30개 Seed 필드 보존·provenance 비노출, 상세 opt-in,
  404·422·500 응답을 확인했다.
- D3 timestamp 순서 확인:
  추가 자체 검토에서 순서 assertion을 넣은 D3 전용 테스트가 1건 실패했다.
  최초 insert의 application `updated_at`이 PostgreSQL default
  `created_at`보다 약간 먼저 생성되어 `created_at <= updated_at` 가정이
  성립하지 않았기 때문이다. 현재 API 계약은 timezone-aware만 보장하므로
  근거 없는 순서 assertion을 제거한 뒤 D3 전용 1건과 전체 57건이
  통과했다. Backend가 순서 불변식과 생성 주체를 결정하도록
  `docs/index.md` 인계 보드에 `BE-POLICY-TIMESTAMP-ORDER`를 기록했다.
- D3 Data 계약 회귀:
  `.venv\Scripts\python.exe -B -m unittest
  tests.test_normalization tests.test_data_fixtures -v` 23건 통과
- D3 결정적 Fixture 검사:
  `.venv\Scripts\python.exe -B scripts/build_data_fixtures.py --check`
  12개 파일 통과
- D3 문서 검증기 단위 테스트:
  `.venv\Scripts\python.exe -B -m unittest tests.test_validate_docs -v`
  10건 통과
- D3 문서 검증:
  `.venv\Scripts\python.exe -B scripts/validate_docs.py` 통과
- D3 공백 검사:
  `git diff --check` 통과
- D4 Runtime adapter·CLI 단위 테스트:
  `.venv\Scripts\python.exe -B -m pytest
  tests/test_runtime_replay.py tests/test_runtime_import_cli.py -q`
  8건 통과. 합성 Raw 재처리 중 외부 network 연결 0회와 CLI 전용
  non-echo engine 생성을 함께 검증했다.
- D4 실제 Runtime Raw smoke:
  `.venv\Scripts\python.exe -B scripts/import_runtime_data.py
  --source youthcenter-api --raw-root runtime/raw --dry-run`은
  `runtime/raw`가 없어 명확한 오류와 종료 코드 1을 반환했다. 실제 Runtime
  적재 성공으로 기록하지 않는다.
- D4 PostgreSQL 전용 통합 테스트:
  로컬 PostgreSQL 18의 `cheongnyeon_alimi_test`에서
  `.venv\Scripts\python.exe -B -m pytest
  tests/integration/test_runtime_to_database.py -q` 1건 통과
- D4 실제 PostgreSQL Backend·Integration 회귀:
  비밀번호 없는 `TEST_DATABASE_URL`과 임시 `PGPASSFILE`을 사용해
  `.venv\Scripts\python.exe -B -m pytest backend/tests tests/integration -q`
  58건 통과, Starlette TestClient deprecation 경고 1건
- D4 전체 Data·Integration 회귀:
  같은 PostgreSQL 환경에서
  `.venv\Scripts\python.exe -B -m pytest tests -q` 91건과 subtest 25건
  통과, Starlette TestClient deprecation 경고 1건
- D4 PostgreSQL 결과:
  youthcenter Raw 4건 → extracted 3건 → valid 2건·invalid 1건,
  Bokjiro Raw 4건 → extracted 2건 → partial 2건으로 집계했다. dry-run
  rollback 0건, 강제 DB failure 시 source accepted batch 0건, 정상 최초
  적재 4건, 같은 Raw 재실행 unchanged 4건과 invalid 적재 0건을 확인했다.
  최종 DB 31개 필드는 canonical Seed와 일치했다.
- D4 최초 실제 CLI 로깅 검사:
  명령은 성공했지만 기존 전역 development `SessionLocal`의 SQLAlchemy
  `echo=True`가 SQL parameter의 정규화 데이터·provenance를 출력하고
  Windows CP949 encoding 오류를 냈다. 원본 Raw byte와 인증키는 출력되지
  않았지만 D4 로그 최소화 기준 실패로 판정했다.
- D4 CLI 로깅 수정:
  Runtime CLI가 `echo=False` 전용 engine을 만들도록 분리했다. 수정 후 실제
  CLI의 dry-run은 inserted 2·invalid 1·DB 변경 0, 최초 youthcenter 적재는
  inserted 2, 재실행은 unchanged 2, Bokjiro 적재는 partial·inserted 2로
  통과했고 SQL·parameter·provenance echo는 0건이었다.
- D4 검증 중 자격증명 정리 경합:
  추가 CLI 검증과 pgpass 삭제 시점이 겹쳐 Alembic upgrade 후 CLI와
  downgrade가 `OperationalError: no password supplied`로 실패했다.
  pgpass를 재생성해 남은 `20260728_0001 (head)`를 `base`로 복구하고
  `to_regclass('public.policies') IS NULL`을 확인한 뒤 전체 CLI 흐름을 다시
  통과시켰다. 운영 DB와 실제 데이터에는 영향이 없었다.
- D4 자격증명·DB 정리:
  최종 CLI 검증 종료 시 Alembic `base` downgrade와 `policies` 테이블 부재를
  확인했고, 이후 임시 `pgpass` 파일의 `Test-Path`가 `False`임을 확인했다.
- D4 Data 계약 회귀:
  `.venv\Scripts\python.exe -B -m unittest
  tests.test_normalization tests.test_data_fixtures -v` 23건 통과
- D4 결정적 Fixture 검사:
  `.venv\Scripts\python.exe -B scripts/build_data_fixtures.py --check`
  12개 파일 통과
- D4 문서 검증기 단위 테스트:
  `.venv\Scripts\python.exe -B -m unittest tests.test_validate_docs -v`
  10건 통과
- D4 문서 검증:
  `.venv\Scripts\python.exe -B scripts/validate_docs.py` 통과
- D4 공백 검사:
  `git diff --check` 통과
- D5 ORM·writer·Migration·CLI 단위 검증:
  `.venv\Scripts\python.exe -B -m pytest
  backend/tests/test_collection_runs.py backend/tests/test_migrations.py
  backend/tests/test_import_seed_cli.py tests/test_runtime_import_cli.py -q`로
  상태 전이, count·시각 constraint, 안전한 error type, Alembic offline SQL,
  Seed·Runtime CLI 이력 연결과 dry-run 비기록 18건을 검증했다.
- D5 PostgreSQL 전용 검증:
  로컬 PostgreSQL 18의 `cheongnyeon_alimi_test`에서
  `backend/tests/test_postgresql_migration.py`와
  `tests/integration/test_collection_run_history.py` 2건이 통과했다. UUID,
  enum, timezone, Seed 성공·Runtime 부분 실패·관리자 trigger 실패 lifecycle와
  downgrade를 확인했다.
- D5 실제 CLI 최초 실패:
  Migration을 head까지 적용한 뒤 Backend 작업 디렉터리에서
  `python -m app.cli.import_seed`를 실행했을 때 저장소 루트의 `collectors`가
  import path에 없어 `ModuleNotFoundError`가 발생했다. Seed와 실행 이력 row가
  생성되기 전 실패했으며 DB는 head에 남았다.
- D5 Seed CLI 실행 경계 수정:
  CLI가 저장소 루트와 Backend root를 모두 import path에 등록하게 수정하고,
  Backend 작업 디렉터리에서 `--help` module 실행을 확인하는 회귀 테스트를
  추가했다. 새 패키지나 실행 방법 변경은 없다.
- D5 실제 CLI 재검증:
  `ENVIRONMENT=test`로 SQL echo를 끈 뒤 canonical Seed 4건을 적재해
  `seed_import`, nullable source, `succeeded`, accepted 4·partial 2·inserted
  4를 확인했다. `runtime/raw`가 없는 Runtime 실행은 종료 코드 1과 함께
  `runtime_import`, `failed`, failed 1, `RuntimeReplayError`를 기록했다.
  두 이력 모두 URL·payload·오류 메시지 없이 안전한 집계만 포함했다.
- D5 실제 PostgreSQL 전체 회귀:
  비밀번호 없는 `TEST_DATABASE_URL`과 임시 `PGPASSFILE`을 사용해
  `.venv\Scripts\python.exe -B -m pytest backend/tests tests -q` 결과
  156건과 subtest 25건이 통과했고 Starlette TestClient deprecation 경고
  1건이 남았다.
- D5 DB 정리:
  실제 CLI와 전체 회귀 후 Alembic `base`, `policies`·`collection_runs`
  테이블 부재와 CollectionRun enum 0개를 확인했다.
- D5 Data 계약·결정성 회귀:
  `.venv\Scripts\python.exe -B -m unittest
  tests.test_normalization tests.test_data_fixtures -v` 23건과
  `.venv\Scripts\python.exe -B scripts/build_data_fixtures.py --check`
  12개 파일이 통과했다.
- D5 문서 검증:
  문서 검증기 단위 테스트 10건과
  `.venv\Scripts\python.exe -B scripts/validate_docs.py`,
  `git diff --check`가 통과했다.
- D6 Policy DTO·API 단위 검증:
  `.venv\Scripts\python.exe -B -m pytest
  backend/tests/test_policy_api.py
  backend/tests/test_policy_mapping_contract.py
  backend/tests/test_policies.py -q` 23건이 통과했다. 공개 필드,
  nullable·배열·enum, pagination, partial 품질 범위와 provenance 비노출을
  확인했다.
- D6 실제 OpenAPI 검토:
  `.venv`의 `app.openapi()`에서 두 Policy path와 `PolicyRead`,
  `PolicyListResponse`를 추출했다. Schema는 코드·API 문서와 일치했고,
  Unicode escape 확인에서 route 한글 summary·description도 정상 문자열임을
  확인했다.
- D6 PostgreSQL 전용 통합 테스트:
  로컬 PostgreSQL 18의 `cheongnyeon_alimi_test`에서
  `.venv\Scripts\python.exe -B -m pytest
  tests/integration/test_seed_to_policy_api.py -q` 1건이 통과했다. 기본 valid
  2건, partial 포함 4건, 목록 envelope, 필터, 숫자 ID 상세, 404·422·500과
  provenance 비노출을 실제 API 응답으로 재검증했다.
- D6 실제 PostgreSQL 전체 회귀:
  비밀번호 없는 `TEST_DATABASE_URL`과 임시 `PGPASSFILE`을 사용해
  `.venv\Scripts\python.exe -B -m pytest backend/tests tests -q` 결과
  156건과 subtest 25건이 통과했다. Starlette TestClient deprecation 경고
  1건이 남았다.
- D6 Data 계약·결정성 회귀:
  `.venv\Scripts\python.exe -B -m unittest
  tests.test_normalization tests.test_data_fixtures -v` 23건과
  `.venv\Scripts\python.exe -B scripts/build_data_fixtures.py --check`
  12개 파일이 통과했다.
- D6 DB 정리:
  통합·전체 회귀 후 Alembic `base`, `policies`·`collection_runs` 테이블
  부재와 Policy·CollectionRun enum 0개를 확인했다.
- Frontend:
  D6 당시 이 PC에 Node와 npm이 없어 build·lint·타입 검사를 실행하지
  못했다. 당시 Integration 브랜치에는 Policy DTO·Mock 소비 구현이 없고 원격
  `784a2a8`은 읽기 전용 정적 검토만 수행했다. 따라서 Frontend 테스트 성공
  또는 승인으로 기록하지 않는다.
- Frontend FE 2A 후속 검증:
  Node.js 24.18.0에서 소비 테스트 7건·lint·production build가 통과했다.
  PostgreSQL canonical Seed 실제 API도 기본 2건·partial 4건, 숫자 ID
  상세·404·422·provenance 비노출과 CORS를 확인했다. 사용자 제공 실제 API
  모드 브라우저 캡처로 홈·목록의 기본 valid 2건과 공개 필드 렌더링을
  확인했다.
- 문서 검증기 단위 테스트:
  `python -B -m unittest tests.test_validate_docs -v` 10건 통과
- 문서 검증:
  `python -B scripts/validate_docs.py` 통과
- 공백 검사:
  `git diff --check` 통과

## 남은 작업

- 관리자 실행 이력 조회·수동 실행 기능은 D5 DB 계약을 기반으로 별도
  Backend·Frontend 관리자 Forest에서 인증·권한·API·UI와 함께 구현해야 한다.
  현재 재개 조건은 `docs/index.md`의 `BE-ADMIN-RUN-HISTORY`에 기록했다.
- Backend는 `BE-POLICY-TIMESTAMP-ORDER`에서 최초 insert의
  `created_at`·`updated_at` 순서 불변식과 생성 주체를 결정해야 한다. D3는
  현재 계약에 없는 순서를 임의로 강제하지 않는다.
- D4 Runtime CLI는 non-echo engine으로 분리했지만 Backend 전역 development
  engine의 `echo=True` 정책은 범위 밖이라 변경하지 않았다. 다른 write
  진입점의 정책 값·provenance 로그 가능성은 `BE-SQL-ECHO-LOGGING`에서
  Backend·보안·운영 영향과 함께 결정해야 한다.

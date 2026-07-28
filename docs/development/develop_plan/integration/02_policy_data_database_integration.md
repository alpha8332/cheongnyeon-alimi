# Policy Data Database Integration Forest 개발 계획

## 계획 정보

- 번호: Integration 02
- 담당 영역: Backend·Data 공동 통합
- 상태: approved
- 대상 기간: 데이터 담당 2주차
- 선행 구현 브랜치: `feature/backend/policy-baseline`
- 권장 구현 브랜치: `feature/database/pipeline-integration`
- 현재 Slice: 구현 시작 전
- 참고 계획:
  `opensource_plan/주차별 개발 목표_데이터담당/2주차 개발 목표.docx`

## 목적

Data Pipeline Forest의 Raw → Extracted → Normalized → Validated 흐름과
Backend Policy Baseline의 ORM·Seed importer·정책 API를 PostgreSQL 기준으로
연결한다. 검증된 canonical Seed와 선택적인 Runtime Raw 재처리 결과를 같은
적재 경계로 안전하게 저장하고 `GET /api/v1/policies`에서 조회할 수 있는
Release 1 데이터·Backend 기준선을 완성한다.

```text
공식 API 또는 합성 Fixture
→ RawPolicyDocument
→ ExtractedPolicy
→ NormalizedProgram
→ Validator
→ valid / partial
→ PostgreSQL Importer
→ Policy Repository
→ GET /api/v1/policies
→ Frontend 소비 계약
```

## 현재 기준선

### Data

- 두 공식 API Collector, Raw 저장, Extractor, Normalizer와 Validator 구현
- `NormalizedProgram` 1.0.0 JSON Schema 구현
- 합성 Normalized Fixture 4건과 rejected Fixture 1건 제공
- canonical JSON Seed 4건 제공
- Backend 소비 검토 완료, Frontend 소비 검토 대기

### Backend

`feature/backend/policy-baseline`에는 다음 기준선이 존재한다.

- 31개 Normalized 필드에 대응하는 `Policy` ORM
- Seed JSON을 읽는 importer와 CLI
- `GET /api/v1/policies`
- `GET /api/v1/policies/{policy_id}`
- Seed 재적재, valid·partial 필터, provenance 비노출과 날짜 보존 테스트

다만 다음 항목은 실제 구현 또는 검증과 문서 선언이 일치하는지 다시 확인해야
한다.

- 실제 Alembic revision 생성과 PostgreSQL 적용
- PostgreSQL `JSONB`와 범용 `JSON` 중 저장 타입
- 실제 `ON CONFLICT DO UPDATE` 구현 여부
- PostgreSQL 연결 실패 시 SQLite 자동 fallback
- Schema 위반·invalid 입력 차단과 rollback
- PostgreSQL 환경에서의 통합 테스트 증거

## 범위

- Backend Policy Baseline의 코드·계획·개발 기록 정합성 복구
- 명시적인 PostgreSQL 연결과 테스트 DB 경계
- Policy ORM과 Alembic Migration 완성
- source-scoped 식별자, uniqueness와 upsert 규칙
- Schema 검증 우선 Seed importer와 원자적 transaction
- Policy Repository, 목록·상세 API와 기본 필터 안정화
- `NormalizedProgram` 31개 필드의 DB 매핑 및 손실 검증
- canonical Seed → PostgreSQL → API 종단 간 통합 테스트
- 저장된 Runtime Raw → 정규화 → DB 적재 진입점
- Runtime 재처리 idempotency와 실패 분리
- 최소 `CollectionRun` 실행 이력
- Frontend 소비 계약 인계와 Data 6 완료 게이트
- 관련 계획, 기준 문서, 개발 기록과 API 문서 동기화

## 범위 밖

- 새로운 API Source와 HTML Collector
- 외부 API 전체 페이지 자동 수집
- Scheduler와 정기 자동 수집
- 수정·삭제 자동 감지
- 소스 간 유사 정책 병합과 정교한 중복 판정
- 자유 키워드 검색, 연령 검색과 검색 순위
- 추천 점수, LLM 또는 벡터 검색
- 즐겨찾기, 알림과 인증
- 관리자 수동 실행 API와 상세 실패 화면
- Dockerfile, Docker Compose와 Production 배포
- 운영 DB 전체 삭제를 수행하는 `--replace`

검색·추천은 3주차 이후 Backend·Integration Forest, HTML Collector와
Scheduler는 독립적인 Data 또는 운영 Forest에서 다룬다.

## 선행 조건

- `feature/backend/policy-baseline`의 변경 내용을 최신 `develop` 기준으로
  검토한다.
- `NormalizedProgram` 1.0.0과 canonical Seed를 입력 계약으로 사용한다.
- Backend가 관리하는 실제 Python 의존성 manifest를 사용한다.
- PostgreSQL 통합 테스트용 `DATABASE_URL` 또는 `TEST_DATABASE_URL`을
  비밀정보가 포함되지 않는 방식으로 주입할 수 있어야 한다.
- Frontend 승인이 없으면 Data 6를 `completed`로 처리하지 않는다.
- `opensource_plan/`은 읽기 전용 참고 자료로 유지한다.

## 공통 설계 원칙

### Data와 Backend 책임을 분리한다

Data는 Raw 재처리, 정규화, Schema·품질 검증과 손실 검사를 담당한다.
Backend는 SQLAlchemy 모델, Migration, Repository, transaction과 API를
담당한다. Collector와 Normalizer는 SQLAlchemy 모델이나 DB Session을 직접
사용하지 않는다.

```text
collectors/
→ NormalizedProgram
→ validation result
→ Backend Import Service
→ PostgreSQL
```

### PostgreSQL 실패를 SQLite로 숨기지 않는다

기본 실행은 명시된 PostgreSQL을 사용하고 연결 실패를 오류로 처리한다.
SQLite는 빠른 단위 테스트에서 명시적으로 주입한 경우에만 허용하며
PostgreSQL Migration·JSONB·upsert 통합 검증을 대신하지 않는다.

### 검증되지 않은 값을 보정해 저장하지 않는다

잘못된 날짜를 `null`, 잘못된 `collected_at`을 현재 시각, 누락된 필수
문자열을 빈 문자열로 바꾸지 않는다. Schema와 DB admission rule을 통과한
`valid`·`partial`만 적재하고 오류 위치와 사유를 결과에 남긴다.

### Seed와 Runtime은 같은 importer 경계를 사용한다

Seed 파일 전용 적재 로직과 Runtime 전용 적재 로직을 복제하지 않는다.
검증된 프로그램 iterable을 받는 공통 import service를 두고 입력 준비만
분리한다.

### 실제 실행 결과만 완료로 기록한다

SQLite 테스트를 PostgreSQL 검증으로 기록하지 않는다. 존재하지 않는
Migration, 실행하지 않은 테스트, 구현하지 않은 `JSONB`나 `ON CONFLICT`를
완료 상태로 문서화하지 않는다.

## Slice 계획

### I0 - Backend 기준선 정합성 복구

- 상태: pending
- 목적: Backend 계획·개발 기록과 실제 코드를 같은 상태로 맞춘다.
- 선행 조건:
  - `feature/backend/policy-baseline`의 변경 파일 검토
- 작업:
  - `JSON`·`JSONB`, 조회 후 update·`ON CONFLICT`, Alembic 환경·revision을
    구분
  - Backend Forest의 `completed` 선언과 남은 작업 모순 해소
  - 미실행 PostgreSQL 검증을 계획 또는 미확정 상태로 정정
  - trailing whitespace와 EOF 오류 정리
- 주요 산출물:
  - 정정된 Backend 계획과 개발 기록
  - 공백 오류가 없는 Backend 변경
- 완료 기준:
  - 코드·계획·개발 기록의 DB 타입, upsert와 Migration 설명이 일치
  - `git diff --check` 통과

### I1 - PostgreSQL 연결 경계

- 상태: pending
- 목적: PostgreSQL 장애가 다른 DB로 숨겨지지 않는 실행 경계를 만든다.
- 선행 조건:
  - Backend 의존성 설치 방법과 환경변수 계약 확인
- 작업:
  - PostgreSQL 실패 시 SQLite 자동 fallback 제거
  - Engine과 Session을 환경 또는 테스트에서 주입 가능한 구조로 분리
  - SQLite는 명시적인 단위 테스트 설정에서만 사용
  - DB URL, 비밀번호와 연결 세부정보의 로그·예외 마스킹
  - health check가 실제 연결 DB 상태를 반영하도록 검증
- 주요 산출물:
  - Backend DB 설정과 Engine factory
  - PostgreSQL 연결 성공·실패 테스트
- 완료 기준:
  - PostgreSQL 중단 또는 잘못된 설정이 명시적으로 실패
  - SQLite 테스트가 별도 설정에서만 실행
  - 비밀정보 노출 0건

### I2 - Policy ORM과 Alembic Migration

- 상태: pending
- 목적: `NormalizedProgram`의 물리적 저장 구조를 Migration으로 고정한다.
- 선행 조건:
  - I1 완료
  - 배열과 provenance 저장 타입 결정
- 작업:
  - scalar, 날짜, 시각, 배열과 provenance 컬럼 타입 검토
  - PostgreSQL `JSONB` 사용 시 필요한 SQLite test variant 분리
  - schedule, status, 품질과 연령 범위 DB constraint 검토
  - Policy 초기 Alembic revision 생성
  - upgrade와 downgrade 검증
  - `Base.metadata.create_all()`을 운영 Seed CLI의 Migration 대체 수단으로
    사용하지 않음
- 주요 산출물:
  - `Policy` ORM
  - Alembic revision
  - Migration 검증 테스트 또는 실행 기록
- 완료 기준:
  - 빈 PostgreSQL에서 `alembic upgrade head` 성공
  - `policies` 테이블, unique constraint와 인덱스 생성
  - ORM metadata와 Migration Schema 일치

### I3 - 식별자와 PostgreSQL upsert

- 상태: pending
- 목적: source-scoped 식별과 재실행 안전성을 확정한다.
- 선행 조건:
  - I2 완료
- 결정 기준:
  - 현재 두 공식 API의 DB 적재 대상은 `external_id`가 있어야 한다.
  - Normalized Schema의 nullable 계약은 유지하되 `external_id = null`은
    DB admission 단계에서 적재하지 않고 사유를 남긴다.
  - 향후 HTML Source의 대체 ID는 별도 Forest에서 결정한다.
- 작업:
  - `(source_id, external_id)` unique constraint 검증
  - PostgreSQL 원자적 upsert 또는 실제 채택한 방식을 코드·문서에 일치시킴
  - inserted, updated, unchanged와 rejected 구분
  - null external ID 사례 테스트
- 주요 산출물:
  - 명시적인 identity·upsert 규칙
  - 재실행과 null ID 테스트
- 완료 기준:
  - 동일 Seed 재실행 후 총 4건 유지
  - 중복 생성 0건
  - null external ID 적재 0건과 확인 가능한 거부 사유

### I4 - 검증 우선 Seed importer

- 상태: pending
- 목적: Schema 위반과 invalid 데이터를 DB에 넣지 않는 원자적 importer를
  구현한다.
- 선행 조건:
  - I3 완료
  - Data Validator의 호출 경계 확인
- 작업:
  - JSON root 배열과 31개 필드 Schema 검증
  - `valid`·`partial` 허용, `invalid`와 DB admission 위반 거부
  - 날짜, enum, 필수 필드를 임의 기본값으로 보정하지 않음
  - canonical Seed 전체를 all-or-nothing transaction으로 처리
  - 실패 시 명시적 rollback
  - `--file`, `--dry-run` CLI 제공
  - `--replace`는 구현하지 않음
  - 요청, 검증, 삽입, 갱신, 무변경, 건너뜀, 거부와 실패 건수 반환
- 주요 산출물:
  - 검증된 program iterable을 받는 import service
  - 안전한 Seed CLI
  - 정상·경계·실패 테스트
- 완료 기준:
  - Seed 4건 적재
  - rejected Fixture와 Schema 위반 적재 0건
  - 오류 시 전체 rollback
  - 오류 위치 출력과 payload·비밀정보 로그 노출 0건

### I5 - Repository와 Policy API 안정화

- 상태: pending
- 목적: ORM 조회와 HTTP 계약을 분리하고 기본 목록·상세 API를 안정화한다.
- 선행 조건:
  - I4 완료
- 작업:
  - Route → Service → Repository 경계 적용
  - `GET /api/v1/policies` 목록과 pagination
  - `GET /api/v1/policies/{policy_id}` 상세
  - valid 기본 노출과 partial opt-in 정책을 목록·상세에서 일관되게 적용
  - category·region 배열 필터를 PostgreSQL JSON 연산에 맞게 구현
  - status query enum 검증
  - provenance 일반 사용자 API 비노출
  - 404와 query 오류 응답을 공통 예외 계약과 일치시킴
- 주요 산출물:
  - Policy Repository와 Service
  - Policy API Schema와 endpoint
  - API 테스트
- 완료 기준:
  - 목록·상세·pagination·필터·404 테스트 통과
  - 배열 검색의 부분 문자열 오탐 없음
  - provenance 사용자 응답 노출 0건

### I6 - Backend PostgreSQL 검증

- 상태: pending
- 목적: SQLite가 아닌 PostgreSQL에서 DB 기준선을 검증한다.
- 선행 조건:
  - I1~I5 완료
- 작업:
  - Migration upgrade
  - Seed 4건 적재와 재실행
  - invalid 거부와 rollback
  - JSONB 또는 확정된 JSON 타입의 배열·provenance 보존
  - null·빈 배열·날짜·timezone 보존
  - 목록·상세 API와 필터 검증
  - PostgreSQL 연결 실패 검증
- 주요 산출물:
  - Backend PostgreSQL 통합 테스트
  - 실제 DB 종류와 명령이 기록된 검증 결과
- 완료 기준:
  - 빈 PostgreSQL에서 Migration → Seed → API 흐름 통과
  - 중복, Schema 오류 적재와 주요 필드 손실 0건
  - SQLite 결과를 PostgreSQL 결과로 대체 기록하지 않음

### I7 - Data·Backend import 경계

- 상태: pending
- 목적: Data 파이프라인과 DB를 결합하지 않고 같은 importer를 공유한다.
- 선행 조건:
  - I4 완료
- 작업:
  - import service가 검증된 `Iterable[dict]` 또는 합의된 DTO를 입력으로 받음
  - Seed adapter와 Runtime adapter 분리
  - Collector와 Normalizer가 Backend ORM·Session을 import하지 않도록 확인
  - Data Validator 결과와 Backend import 결과 타입 연결
- 주요 산출물:
  - 공통 import interface
  - Seed와 Runtime adapter
- 완료 기준:
  - Seed와 Runtime이 같은 DB 적재 service를 사용
  - Data 계층의 SQLAlchemy 의존 0건

### I8 - 31개 필드 DB 매핑 검증

- 상태: pending
- 목적: Normalized → DB 변환에서 의미와 provenance 손실을 막는다.
- 선행 조건:
  - I7 완료
- 작업:
  - JSON 필드, Python 타입, DB 컬럼, null, 배열, API 노출과 검색 여부 매핑
  - `category_text`·`categories`, `region_text`·`regions` 동시 보존
  - 신청 일정·상태와 원문 기간 text 동시 보존
  - 조건 배열, 출처 URL, 수집 시각, provenance와 품질 보존
- 주요 산출물:
  - 문서화된 31개 필드 매핑표
  - Seed 원본과 DB 조회 결과 비교 테스트
- 완료 기준:
  - 필드 누락, null·빈 배열 변형과 다중 category 손실 0건
  - provenance DB 보존과 사용자 API 비노출 확인

### I9 - Seed → PostgreSQL → API 종단 간 테스트

- 상태: pending
- 목적: canonical Seed가 실제 서비스 조회 경계까지 전달되는지 검증한다.
- 선행 조건:
  - I6~I8 완료
- 테스트 흐름:

  ```text
  data/seeds/initial_programs.json
  → Normalized Schema 검증
  → Alembic Migration
  → PostgreSQL Importer
  → Repository
  → GET /api/v1/policies
  ```

- 권장 위치:
  `tests/integration/test_seed_to_database.py`
- 완료 기준:
  - 입력·검증·DB 적재 4건
  - valid 2건, partial 2건 DB 보존
  - 기본 API 2건, `include_partial=true` 4건
  - 중복, invalid 적재, 주요 필드 손실과 provenance API 노출 0건
  - 외부 네트워크 없이 재현 가능

### I10 - Runtime Raw 재처리와 DB 적재

- 상태: pending
- 목적: 저장된 Raw를 외부 API 재호출 없이 재처리해 DB에 적재한다.
- 선행 조건:
  - I7~I9 완료
- 작업:
  - `scripts/import_runtime_data.py` 진입점
  - `--source`, `--raw-root`, `--dry-run`, `--limit`,
    `--include-partial` 옵션
  - Raw reload → Extractor → Normalizer → Validator → importer 연결
  - Runtime Raw 부재 시 안전하고 명확한 종료
  - source별 batch transaction
  - validation rejection과 DB failure 분리
  - payload 전체, 인증 파라미터와 인증키를 로그에 남기지 않음
- 주요 산출물:
  - Runtime import CLI
  - 합성 Fixture 기반 자동 테스트
  - 기존 Runtime Raw가 있을 때 선택적인 로컬 smoke 결과
- 완료 기준:
  - 자동 테스트는 Git에 포함된 합성 Fixture만으로 통과
  - 기존 Runtime Raw 검증 시 추가 API 호출 0회
  - 동일 Runtime 재실행 중복 0건
  - 실제 DB 결과와 실행 요약 건수 일치

### I11 - 최소 CollectionRun 기록

- 상태: pending
- 목적: 관리자 기능 전에 수집·적재 실행의 최소 추적 정보를 보존한다.
- 선행 조건:
  - I10 완료
- 최소 필드:
  - `run_id`
  - `source_id`
  - `started_at`, `finished_at`, `status`
  - `requested_count`, `raw_document_count`, `extracted_count`
  - `accepted_count`, `partial_count`, `invalid_count`
  - `inserted_count`, `updated_count`, `unchanged_count`
  - `skipped_count`, `failed_count`, `error_type`
- 작업:
  - ORM과 Alembic revision
  - Seed 또는 Runtime import 실행 요약 연결
  - payload·인증정보와 상세 오류 본문 제외
- 주요 산출물:
  - 최소 CollectionRun 모델과 Migration
  - 성공·부분 실패·실패 테스트
- 완료 기준:
  - 실행별 요약 레코드 생성
  - 실제 처리 수치와 DB 기록 일치
  - 비밀정보와 Raw payload 저장 0건

### I12 - Frontend 인계와 Data 6 종료 게이트

- 상태: pending
- 목적: Frontend가 별도 추측 없이 Policy API를 소비할 수 있게 한다.
- 선행 조건:
  - I5와 I9 완료
- 작업:
  - `GET /api/v1/policies`와 상세 endpoint 요청·응답 문서화
  - 목록·상세 합성 응답 예시
  - TypeScript 타입 생성 기준
  - nullable·배열·일정·상태·partial 처리 규칙
  - provenance 비노출 결정과 Mock → API 전환 안내
  - Frontend 승인 또는 실제 소비 테스트 결과를 공동 검토 기록에 반영
- 주요 산출물:
  - `docs/api/` Policy API 계약
  - 갱신된 Fixture·Seed 공동 검토 기록
  - Integration Forest 개발 기록
- 완료 기준:
  - Frontend 승인 또는 소비 테스트 증거
  - Backend·Frontend 공동 승인 완료
  - Data 6와 Data Pipeline Forest 완료 상태 갱신
  - Frontend 승인이 없으면 `기술 구현 완료 / Frontend 승인 대기`로 유지

## 의존 순서

```text
I0
↓
I1 → I2 → I3 → I4 → I5 → I6
                     ↓
                    I7 → I8 → I9 → I10 → I11
                                   ↓
                                  I12
```

I12의 API 문서 초안과 Frontend 검토 요청은 I5 이후 병렬로 시작할 수 있지만,
최종 승인은 I9 종단 간 결과를 확인한 뒤 기록한다.

## 검증 계획

### Backend

- Backend 단위·API 테스트
- Alembic upgrade와 downgrade
- PostgreSQL 연결 성공·실패
- 실제 PostgreSQL upsert·JSON·transaction

### Data

- 전체 Data 회귀 테스트
- `uv run python -B scripts/build_data_fixtures.py --check`
- Schema, null·빈 배열·enum·날짜·provenance 보존

### Integration

- Seed → PostgreSQL → Repository → API
- Runtime Raw → Extracted → Normalized → Validated → PostgreSQL
- 동일 입력 재실행과 rollback
- 외부 네트워크가 없는 합성 Fixture 기반 자동 테스트
- 선택적인 기존 Runtime Raw smoke test

### 공통

- `uv run python -B scripts/validate_docs.py`
- `git diff --check`
- 비밀정보와 운영 Raw의 Git 제외
- 실행하지 않은 검증이 결과 문서에 없는지 확인

Python 명령이 실패하면 새 패키지를 임의로 설치하지 않고 Backend manifest,
저장소의 `uv`와 사용 가능한 기존 실행 환경을 먼저 확인한다.

## Forest 완료 기준

- I0~I12의 기술 작업 완료
- Alembic Migration으로 빈 PostgreSQL 구성 성공
- canonical Seed 4건 적재와 재실행 중복 0건
- invalid와 Schema 오류 적재 0건
- null·빈 배열·enum·날짜와 다중 category 손실 0건
- provenance DB 보존과 사용자 API 노출 0건
- 저장된 Runtime Raw 재처리 결과를 같은 importer로 적재 가능
- Runtime 재실행 중복 0건
- `/api/v1/policies` 목록·상세와 기본 필터 정상
- SQLite fallback이 PostgreSQL 장애를 숨기지 않음
- Backend 단위 테스트와 PostgreSQL 통합 테스트 통과
- Data 회귀와 Fixture 결정성 검사 통과
- 문서 검증과 `git diff --check` 통과
- API, DB, Data 기준 문서와 실제 구현 일치
- Frontend 소비 자료 제공

Frontend 승인이 없으면 기술 구현 완료를 기록할 수 있으나 I12와 Data 6의
공동 승인 완료 기준은 충족하지 않은 것으로 유지한다.

## 위험과 미확정 사항

- `feature/backend/policy-baseline`은 코드와 문서의 완료 선언이 일부 다를 수
  있으므로 I0에서 실제 실행 결과를 다시 확인해야 한다.
- 현재 로컬 Python 환경에 Backend 의존성이 없으면 테스트를 재현할 수 없다.
  합의된 Backend manifest를 사용하고 새 환경 설치가 필요하면 팀에 알린다.
- PostgreSQL 통합 테스트 DB의 제공 방식은 아직 확정되지 않았다. Docker
  구성이 필요하면 이 Forest에서 임의로 확장하지 않고 Integration·Deploy
  담당과 별도 합의한다.
- Windows `core.autocrlf` 환경에서 canonical JSON의 byte 비교가 실패할 수
  있으므로 `.gitattributes`를 통한 LF 고정 필요성을 검토한다.
- `external_id = null`은 현재 DB admission에서 제외하는 안을 사용한다.
  향후 HTML Source가 대체 ID를 요구하면 별도 계약으로 확장한다.
- JSONB 배열 필터는 자유 키워드 검색을 대신하지 않는다. 검색 알고리즘과
  인덱스 최적화는 후속 Forest에서 다룬다.
- 실제 Runtime Raw는 Git에 포함되지 않으므로 자동 테스트 완료 기준은 합성
  Fixture에 두고 로컬 Runtime 결과는 별도 smoke 검증으로 기록한다.

## 관련 문서

- [개발 계획 안내](../README.md)
- [Data Pipeline Forest 계획](../data/01_data_pipeline.md)
- [Backend Policy Baseline Forest 계획](../backend/01_policy_baseline.md)
- [역할과 책임](../../../governance/role_assignment.md)
- [시스템 아키텍처 개요](../../../architecture/overview.md)
- [시스템 흐름](../../../architecture/system_flow.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)
- [정규화 규칙](../../../data/normalization_rules.md)
- [API 문서 안내](../../../api/README.md)

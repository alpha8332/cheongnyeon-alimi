# Policy Data Database Integration Forest 개발 기록

## 작업 정보

- 시작일: 2026-07-29
- 상태: in-progress
- 영역: Data·Backend 공동 통합
- 브랜치: `feature/database/pipeline-integration`
- 관련 계획:
  [`02_policy_data_database_integration.md`](../../develop_plan/integration/02_policy_data_database_integration.md)
- 현재 Slice: D0 review-pending (기술 검토 완료, Frontend 승인 대기)

## 목적

Data 파이프라인의 `NormalizedProgram` 1.0.0과 canonical Seed를 Backend
PostgreSQL 저장·조회 경계 및 Frontend 소비 계약과 공동 확정한다. D0에서는
기존 Backend 검증 증거를 확인하고 Frontend 타입·Mock 인계 경계를 명시한다.

## Forest 범위

- Backend·Frontend의 NormalizedProgram 1.0.0 공동 검토
- 31개 Normalized 필드의 DB 매핑과 손실 검증
- canonical Seed와 Runtime 결과의 PostgreSQL·Policy API 통합
- 적재 idempotency, 품질 분기와 실행 결과 요약
- API 소비 자료와 Frontend 인계

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| D0 | review-pending | Backend 소비 승인·Frontend 타입·Mock 인계 완료, Frontend 승인 대기 |
| D1 | pending | D0 Backend 검토를 바탕으로 DB 매핑 검증 예정 |
| D2 | pending | canonical Seed → PostgreSQL 통합 검증 예정 |
| D3 | pending | Policy API 첫 통합 예정 |
| D4 | pending | Runtime Raw 재처리와 DB 적재 예정 |
| D5 | optional | 최소 실행 이력 구현 여부 협의 예정 |
| D6 | pending | Frontend 최종 인계와 Data 6 종료 예정 |

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
- 현재 Frontend에는 Policy DTO 타입과 Mock 소비 코드가 없으므로 Data
  담당이 이를 대신 구현하거나 승인으로 간주하지 않았다.
- D0는 저장된 합성 Seed와 기존 Backend 증거를 검토하는 단계이므로 외부 API를
  호출하거나 인증키를 사용하지 않았다.
- canonical JSON의 byte 결정성을 위해 `.gitattributes`에서 Fixture, Seed와
  Schema JSON을 `text eol=lf`로 고정하고 공식 재생성 스크립트로 기존 산출물을
  LF byte로 정규화했다.

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

## 설계 결정

### Backend 검증 증거와 Frontend 승인을 분리한다

Backend 02의 실제 PostgreSQL 종단 검증은 Backend 소비 가능성을 승인하기에
충분하다. 그러나 Frontend 담당자 승인이나 타입·Mock 소비 테스트가 없으므로
공동 승인을 완료로 기록하지 않는다. D0와 Forest는 Frontend 증거가 생길
때까지 `in-progress`로 유지한다.

### canonical Seed와 공개 Policy DTO를 같은 타입으로 취급하지 않는다

canonical Seed는 31개 Normalized 필드와 provenance를 포함한다. 공개 Policy
DTO는 provenance를 제외하고 DB `id`, `created_at`, `updated_at`을 추가한다.
Frontend Mock은 Seed 사례를 재사용할 수 있지만 이 노출 경계를 반영해야 한다.

### 계약 버전은 1.0.0을 유지한다

Schema, Fixture, Seed, Backend importer·ORM과 API 사이에서 D0가 해결해야 할
필드 충돌을 발견하지 않았다. 따라서 소비 코드 부재만을 이유로 계약 버전을
변경하지 않는다.

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
- Frontend:
  Node와 npm이 없어 빌드·타입 검사를 실행하지 못했다. Policy DTO 타입과 Mock
  소비 코드도 현재 저장소에 없다.
- 문서 검증기 단위 테스트:
  `python -B -m unittest tests.test_validate_docs -v` 10건 통과
- 문서 검증:
  `python -B scripts/validate_docs.py` 통과
- 공백 검사:
  `git diff --check` 통과

## 남은 작업

- Frontend 담당자가 D0 인계 항목을 반영한 TypeScript 타입·Mock 소비 테스트
  또는 명시적 승인 기록을 제공해야 D0를 완료할 수 있다.
- Frontend `src/routes/index.tsx`는 현재 존재하지 않는
  `pages/user/ProgramListPage`를 import한다. D0 범위 밖 Frontend 빌드 문제로
  수정하지 않았다.
- D1에서 31개 필드의 JSON·DB·API 매핑표와 source-scoped identity를
  구체적으로 검증한다.

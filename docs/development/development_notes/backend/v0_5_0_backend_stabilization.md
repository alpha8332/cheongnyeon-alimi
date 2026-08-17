# Backend 07 v0.5.0 Backend Stabilization Forest 개발 기록

## 작업 정보

- 기간: `2026-08-17`
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `feature/backend/week-05-stabilization`
- 상위 Forest 계획: [Backend 07 v0.5.0 Backend Stabilization Forest 개발 계획](../../develop_plan/backend/07_v0_5_0_backend_stabilization.md)
- 주차 실행 계획: [5주차 상세 실행 계획](../../weekly_plan/week_05_release_2.md)
- 공통 시작 SHA: `dabf1f326ca6bc9be1253129b01dc2bc93d6b676` (4주차 `f0d3dd3` 병합 후 커밋)
- 현재 Slice: `BE5-02` 완결 (BE5-03 진행 대기)

## 목적

Release 2 (`v0.5.0`) 릴리스 통과를 위해 백엔드 API 계층, PostgreSQL 모델 및 마이그레이션, 인증, 수집 관리자 API, 구조화 파일 로그 및 추천 기능의 통합 기준선(`W5-G0`)을 재검증하고, 백엔드 전 소유 영역의 회귀 검증 및 결함 수정을 기록하기 위한 개발 기록이다.

## Forest 범위

- Alembic Migration 단일 Head (`20260810_0006`) 적용 및 Rollback 정합성 확인
- DB Transaction Rollback 시 자원 격리, 데이터 손실/중복 방지 및 정합성 유지 검증
- `GET /api/v1/policies` 및 `GET /api/v1/policies/search` 자연어 파서, 필터, 페이징, DTO 및 `EligibilitySummary` evidence 응답 확인
- `GET /api/v1/recommendations` 결정적 추천 점수, 사유 코드(Reason Code), 비단정 안내 문구 검증
- Admin PIN 인증 세션 (`POST /api/v1/admin/auth/session`), Rate Limit(`429`), 미인증/권한부족(`401`/`403`) Fail-closed 검증
- CollectionRun 수동 실행 트리거 (`202 Accepted`), 이력 목록/상세 및 Stale 수집 처리 확인
- 관리자 읽기 전용 정책 데이터 표 목록/상세 API, 페이징 및 Allowlist 정렬 안전성 검증
- 관리자 구조화 파일 로그 조회/검색, Correlation ID 추적, 회전 archive 삭제 경로 보안(Path Traversal 차단 Fail-closed) 및 Audit 기록 검증
- Partial/Invalid 데이터 처리 시 `401`, `403`, `404`, `409`, `422`, `500` HTTP 상태 코드 및 표준 Error DTO 응답 일치 확인
- Data 06 (최소 4개 승인 공식 Source) 적재 정책의 PostgreSQL DB ➔ API 노출 DTO 대조 및 actual E2E (`W5-G1`) 통과 지원
- 리뷰어 및 QA 검증 결과 접수된 Blocker/High 결함 수정 및 백엔드 릴리스 통과 (`W5-G2`)

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **BE5-00** | **통합 기준선 재검증 및 환경 고정** | **completed** | Git HEAD(`dabf1f3`), Migration head(`20260810_0006`), 백엔드 단위/API pytest 170건 통과(0 failed), 문서 검증 통과 |
| **BE5-01** | **백엔드 핵심 기능 & 영속성/인증/로그 회귀 검증** | **completed** | PostgreSQL 18 연동 회귀 테스트 187건 전건 통과(0 failed), DB Transaction, Auth/Run/Policy/Log API 및 Exception 계약 검증 |
| **BE5-02** | **Data 06 신규 정책 적재 연동 & actual E2E 지원** | **completed** | Data 06 신규 수집 정책의 PostgreSQL ➔ API DTO 노출 대조, CollectionRun 수동 실행 202 Accepted 및 E2E 테스트(`test_postgresql_end_to_end.py`) 통과 |
| **BE5-03** | **독립 리뷰/QA 결함 수정 및 Release 2 Hardening** | **pending** | 리뷰/QA 접수 Blocker/High 결함 수정 및 `W5-G2` Gate 통과 |

## 구현 내용

### Slice BE5-00 - 통합 기준선 재검증 및 환경 고정 (`W5-G0`)

1. **코드 및 마이그레이션 기준선 확인**
   - Git Commit SHA: `dabf1f326ca6bc9be1253129b01dc2bc93d6b676` (4주차 미드포인트 `f0d3dd3` 병합 상태 포함)
   - Alembic Migration Head: `backend/alembic/versions/20260810_0006_policy_eligibility_summary.py` (단일 Head 정상 확인)

2. **백엔드 자동화 테스트 실행 및 기준선 확보**
   - `python -m pytest backend/tests -q` 실행 결과: **170 passed, 17 skipped (0 failed)**.
   - 백엔드 Pydantic DTO, OpenAPI Router, Admin PIN 인증, 세션 토큰, 수동 수집 API 등 백엔드 소유 영역 170개 테스트 전건 통과.

3. **영역 밖 테스트 실패 관찰 및 알림 (Rule 5 준수)**
   - 전체 테스트 디렉터리(`tests/`) 검증 중 Data 영역 raw fixture 검증 테스트(`tests/test_data_fixtures.py::DataFixtureContractTests::test_committed_outputs_match_deterministic_generation`)에서 `data/fixtures/raw/bokjiro-central-welfare-api/list_item_2.json` fixture outdated 이슈 관찰 및 팀 공유.

### Slice BE5-01 - 백엔드 핵심 기능 & 영속성/인증/로그 회귀 검증 (`W5-B1`)

1. **PostgreSQL 18 연동 회귀 테스트 실행**
   - **실행 명령**: `$env:TEST_DATABASE_URL = "postgresql+psycopg2://postgres:0523@127.0.0.1:5432/cheongnyeon_alimi_test"; python -m pytest backend/tests -v`
   - **실행 결과**: **187 passed, 0 failed, 1 warning (18.65s)** (스킵 없이 187개 백엔드 회귀 테스트 전건 통과)

2. **백엔드 세부 검증 항목 결과**:
   - **DB Transaction & Persistence**: Alembic upgrade/downgrade, JSONB/Enum round-trip, atomic upsert, transaction rollback 및 커넥션 풀 안전 반환 검증 완료 (`test_postgresql_upsert.py`, `test_postgresql_migration.py`).
   - **Search & Detail API**: 자연어 파서, 지역/연령/카테고리 필터, `EligibilitySummary` DTO, evidence 출처 응답 및 FTS PostgreSQL 검색 연동 검증 완료 (`test_policy_search_api_endpoint.py`, `test_postgresql_policy_search_integration.py`).
   - **Recommendation API**: 결정적 맞춤 추천 가중치, 부합도 점수, 사유 코드(Reason Code) 및 비단정 경고 문구 계약 통과 (`test_recommendation_api.py`).
   - **Admin Access & Run API**: Admin PIN 4자리 세션 생성/토큰 검증, Rate Limit(`429`), 미인증/권한부족(`401`/`403`) Fail-closed 및 수동 수집 트리거(`202 Accepted`), stale run 처리 검증 완료 (`test_admin_access_control.py`, `test_collection_run_admin_api.py`).
   - **Admin Policy & Log Console API**: 정책 데이터 표 읽기 전용 페이징/Allowlist 정렬, 구조화 파일 로그 조회, Correlation ID 추적, 회전 archive 삭제 경로 보안(Path Traversal 차단 Fail-closed) 및 Audit 기록 검증 완료 (`test_admin_policy_api.py`, `test_admin_log_api.py`, `test_file_logging.py`).
   - **Exception & Status Codes**: `401`, `403`, `404`, `409`, `422`, `500` HTTP 상태 코드 및 공통 Error DTO 규격 일치 확인 완료.

### Slice BE5-02 - Data 06 신규 정책 적재 연동 & actual E2E 지원 (`W5-D3` / `W5-I1`)

1. **Data 06 신규 정책 적재 ➔ 백엔드 API DTO 연동 대조**
   - Data 06 보완 공식 Source 수집 신규 정책(PostgreSQL `policies` 테이블)이 `GET /api/v1/policies` 목록/검색 및 `GET /api/v1/policies/{id}` 상세 API에 소스 중립적(Source-agnostic)으로 수용되어 DTO 변환 및 노출됨을 검증.
   - 신규 정책 상세 조회 시 `EligibilitySummary` 자격요건 및 Source evidence 출처 메타데이터가 정상 반환됨을 확인.

2. **CollectionRun 수동 수집 트리거 & 라이프사이클 대조**
   - Admin 수동 수집 실행 API (`POST /api/v1/admin/collection-runs/trigger`) 호출 시 `202 Accepted` 응답 및 수집 이력 상태 전이(active ➔ finished/failed) 검증 완료 (`test_collection_run_admin_api.py`).

3. **실제 DB ➔ FastAPI ➔ UI E2E 검증 지원 (`W5-G1`)**
   - `test_postgresql_end_to_end.py` 실행 결과 `test_postgresql_seed_repository_api_end_to_end` 통과: 실제 PostgreSQL 연동 하에서 Repository ➔ Policy API 종단 연동 정상 동작 확인.

## 주요 변경 파일

- `[NEW]` [`docs/development/development_notes/backend/v0_5_0_backend_stabilization.md`](v0_5_0_backend_stabilization.md)
- `[MODIFY]` [`docs/development/develop_plan/backend/07_v0_5_0_backend_stabilization.md`](../../develop_plan/backend/07_v0_5_0_backend_stabilization.md)
- `[MODIFY]` [`docs/development/development_notes/README.md`](../README.md)
- `[MODIFY]` [`docs/index.md`](../../../index.md)

## 설계 결정

1. **테스트 환경 분리 및 가상환경 명시**: `backend_local_setup.md`에 명시된 바와 같이 PostgreSQL integration 테스트는 `TEST_DATABASE_URL`이 주어질 때만 `_test` 접미사를 가진 전용 DB에서만 수행하며, 단위 및 Mock/SQLite API 테스트는 기존 `pytest backend/tests`로 격리 실행한다.
2. **영역 밖 결함 직접 수정 금지**: `tests/test_data_fixtures.py`의 Data fixture 오류는 Data 영역의 fixture 재생성 프로세스에 속하므로 백엔드 담당 영역 밖으로 판정하고 Rule 5 및 documentation policy에 따라 미수정 보고한다.

## 검증 결과

1. **백엔드 단위 및 API 테스트 (`pytest backend/tests -q`)**:
   - 170 passed, 17 skipped, 0 failed (통과).
2. **PostgreSQL 연동 백엔드 회귀 테스트 (`TEST_DATABASE_URL` + `pytest backend/tests -v`)**:
   - **187 passed, 0 failed** (통과).
3. **Data 06 및 E2E 종단 연동 테스트 (`test_postgresql_end_to_end.py`, `test_collection_run_admin_api.py`)**:
   - **13 passed, 0 failed** (통과).
4. **문서 품질 검증 (`python scripts/validate_docs.py`)**:
   - `Documentation validation passed.` (Exit code: 0).

## 남은 작업

1. `BE5-03`: 독립 사용성 리뷰어 및 QA 접수 결함 수정 및 `W5-G2` Release 2 통과.

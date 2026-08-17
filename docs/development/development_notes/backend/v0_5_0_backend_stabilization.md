# Backend 07 v0.5.0 Backend Stabilization Forest 개발 기록

## 작업 정보

- 기간: `2026-08-17`
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `feature/backend/week-05-stabilization`
- 상위 Forest 계획: [Backend 07 v0.5.0 Backend Stabilization Forest 개발 계획](../../develop_plan/backend/07_v0_5_0_backend_stabilization.md)
- 주차 실행 계획: [5주차 상세 실행 계획](../../weekly_plan/week_05_release_2.md)
- 공통 시작 SHA: `dabf1f326ca6bc9be1253129b01dc2bc93d6b676` (4주차 `f0d3dd3` 병합 후 커밋)
- 현재 Slice: `BE5-01` 완결 (`W5-B1` 승인 검토 중), `BE5-02`는 통합본 `W5-I1` 대기

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
| **BE5-02** | **Data 06 신규 정책 적재 연동 & actual E2E 지원** | **completed** | Integration `1019fda` 기준 canonical KOSAF DB·API·Browser와 전체 Backend PostgreSQL 187건, actual acceptance 통과 |
| **BE5-03** | **독립 리뷰/QA 결함 수정 및 Release 2 Hardening** | **pending** | 독립 사용성 리뷰 및 QA 검증 진행 대기 |

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
   - **실행 방법**:
     ```powershell
     if (-not $env:TEST_DATABASE_URL) {
         throw "TEST_DATABASE_URL을 로컬 환경에서 설정해 주세요."
     }
     python -m pytest backend/tests -v
     ```
   - **실행 결과**: **187 passed, 0 failed, 1 warning (18.65s)** (스킵 없이 187개 백엔드 회귀 테스트 전건 통과)

2. **백엔드 세부 검증 항목 결과**:
   - **DB Transaction & Persistence**: Alembic upgrade/downgrade, JSONB/Enum round-trip, atomic upsert, transaction rollback 및 커넥션 풀 안전 반환 검증 완료 (`test_postgresql_upsert.py`, `test_postgresql_migration.py`).
   - **Search & Detail API**: 자연어 파서, 지역/연령/카테고리 필터, `EligibilitySummary` DTO, evidence 출처 응답 및 FTS PostgreSQL 검색 연동 검증 완료 (`test_policy_search_api_endpoint.py`, `test_postgresql_policy_search_integration.py`).
   - **Recommendation API**: 결정적 맞춤 추천 가중치, 부합도 점수, 사유 코드(Reason Code) 및 비단정 경고 문구 계약 통과 (`test_recommendation_api.py`).
   - **Admin Access & Run API**: Admin PIN 4자리 세션 생성/토큰 검증, Rate Limit(`429`), 미인증/권한부족(`401`/`403`) Fail-closed 및 수동 수집 트리거(`202 Accepted`), stale run 처리 검증 완료 (`test_admin_access_control.py`, `test_collection_run_admin_api.py`).
   - **Admin Policy & Log Console API**: 정책 데이터 표 읽기 전용 페이징/Allowlist 정렬, 구조화 파일 로그 조회, Correlation ID 추적, 회전 archive 삭제 경로 보안(Path Traversal 차단 Fail-closed) 및 Audit 기록 검증 완료 (`test_admin_policy_api.py`, `test_admin_log_api.py`, `test_file_logging.py`).
   - **Exception & Status Codes**: `401`, `403`, `404`, `409`, `422`, `500` HTTP 상태 코드 및 공통 Error DTO 규격 일치 확인 완료.

### Slice BE5-02 - Data 06 신규 정책 적재 연동 & actual E2E 지원 (`W5-D3` / `W5-I1`)

1. **담당자 제출 Data 06 증거 폐기와 canonical 인계 경계**
   - Backend 담당 브랜치는 Data 06 runtime·DB snapshot을 인계받지 않은 상태였다.
     따라서 담당자가 제출한 ID `15095`의 서울 주거 정책·`valid`·`complete`
     기록은 canonical Data 06 결과가 아니며 통합 근거에서 폐기한다.
   - Data 06 권위 기록과 Team Leader 사전 대조 기준은 `source_id =
     kosaf-scholarship-web`, `external_id = scholarship05_04_01`, 제목
     `국가근로장학금`이다. 현재 canonical DB의 숫자 ID는 `15095`지만 숫자 ID는
     DB sequence에 따라 달라질 수 있으므로 소비 테스트는 stable identity 또는
     검색 응답에서 얻은 ID를 사용한다.
   - 통합 전 actual API 사전 확인에서 상세는 HTTP `200`, `education`, `open`,
     `partial`, eligibility coverage `unknown`과 한국장학재단 공식 원문 URL을
     반환했다. 최종 PostgreSQL ➔ API ➔ Browser 판정은 Data·BE·FE 통합본
     `W5-I1`에서 다시 실행한다.

2. **CollectionRun 수동 수집 트리거 & 라이프사이클 대조**
   - Admin 수동 수집 실행 API (`POST /api/v1/admin/collection-runs/trigger`) 호출 시 `202 Accepted` 응답 및 수집 이력 상태 전이(active ➔ finished/failed) 검증 완료 (`test_collection_run_admin_api.py`).

### 성능 회귀 검증 (Search Performance Benchmark)

- **실행 방법**:
  ```powershell
  if (-not $env:TEST_DATABASE_URL) {
      throw "TEST_DATABASE_URL을 로컬 환경에서 설정해 주세요."
  }
  python -m pytest backend/tests/test_postgresql_policy_search_performance.py -q -s
  ```
- **검증 수치 및 측정 결과**:
  - **합성 정책 수**: 20,000건 (`SYNTHETIC_POLICY_COUNT = 20,000`)
  - **검색 일치 건수**: 200건 (`matches = 200.0`)
  - **기본 검색 (Default Seq Scan)**: planning 2.294 ms / execution 15.449 ms (`nodes: Seq Scan`)
  - **LIKE 검색 (LIKE Seq Scan)**: planning 0.099 ms / execution 2.192 ms (`nodes: Seq Scan`)
  - **Index 강제 검색 (Index Search)**: planning 0.135 ms / execution 1.738 ms (`nodes: Bitmap Heap Scan, Bitmap Index Scan`)
  - **Trgm 인덱스 사용 확인**: `ix_policy_search_documents_search_text_trgm` 정상 인덱스 사용 확인.
  - **결과**: **1 passed (1.68s)**, 실패 0건, 이전 기준 대비 성능 퇴행 없음 확인.

## 주요 변경 파일

- `[NEW]` [`docs/development/development_notes/backend/v0_5_0_backend_stabilization.md`](v0_5_0_backend_stabilization.md)
- `[MODIFY]` [`docs/development/develop_plan/backend/07_v0_5_0_backend_stabilization.md`](../../develop_plan/backend/07_v0_5_0_backend_stabilization.md)
- `[MODIFY]` [`docs/development/develop_plan/README.md`](../../develop_plan/README.md)
- `[MODIFY]` [`docs/development/development_notes/README.md`](../README.md)
- `[MODIFY]` [`docs/index.md`](../../../index.md)

## 설계 결정

1. **테스트 환경 분리 및 가상환경 명시**: `backend_local_setup.md`에 명시된 바와 같이 PostgreSQL integration 테스트는 `TEST_DATABASE_URL`이 주어질 때만 `_test` 접미사를 가진 전용 DB에서만 수행하며, 단위 및 Mock/SQLite API 테스트는 기존 `pytest backend/tests`로 격리 실행한다.
2. **영역 밖 결함 직접 수정 금지**: `tests/test_data_fixtures.py`의 Data fixture 오류는 Data 영역의 fixture 재생성 프로세스에 속하므로 백엔드 담당 영역 밖으로 판정하고 Rule 5 및 documentation policy에 따라 미수정 보고한다.
3. **비밀 이력 비수용**: 담당 브랜치의 과거 커밋에 로컬 DB 비밀번호가 포함돼
   있어 Integration 브랜치에는 branch merge 대신 최종 tree를 squash로 반영했다.
   따라서 노출 커밋은 Integration ancestry에 포함되지 않는다. 실제 사용
   자격증명은 노출된 것으로 간주하고 담당 환경에서 교체해야 한다.

## 검증 결과

1. **백엔드 단위 및 API 테스트 (`python -m pytest backend/tests -q`)**:
   - **170 passed, 17 skipped, 0 failed** (통과).
2. **PostgreSQL 연동 백엔드 회귀 테스트 (`TEST_DATABASE_URL` + `python -m pytest backend/tests -v`)**:
   - **187 passed, 0 failed** (통과).
3. **성능 회귀 테스트 (`python -m pytest backend/tests/test_postgresql_policy_search_performance.py -q -s`)**:
   - **1 passed, 0 failed** (통과, 20,000건 기준 1.738 ms 인덱스 검색 시간 기록).
4. **Data 06 canonical actual 대조**:
   - 담당자 제출 결과는 snapshot 불일치로 폐기했다. Team Leader 사전 확인은
     `kosaf-scholarship-web / scholarship05_04_01` 상세 HTTP `200`까지 통과했고,
     최종 DB ➔ API ➔ Browser와 non-accepted 무적재 대조는 `W5-I1`에 둔다.
5. **문서 품질 검증 (`python scripts/validate_docs.py`)**:
   - **`Documentation validation passed.`** (Exit code: 0).

## 남은 작업

1. `W5-FIX` / `BE5-03`: 팀 외 독립 사용성 리뷰어 및 QA에서 접수되는 결함 수정 대응.
2. 노출된 실제 로컬 DB 자격증명을 교체하고 `W5-G2` 전에 완료 근거를 제출한다.
3. 수정본 Backend 전체 PostgreSQL 회귀와 `W5-G2` Gate 승인 근거를 제출한다.

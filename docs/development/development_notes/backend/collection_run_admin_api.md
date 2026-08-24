# Backend CollectionRun Admin API Forest 개발 기록

## 작업 정보

- 기간: `2026-08-10`
- 담당 영역: Backend
- 상태: completed
- 브랜치: `feature/backend/admin-access-control`
- 선행 Forest: [Backend Admin Access Control](admin_access_control.md)
- 관련 계획: [Backend CollectionRun Admin API Plan](../../develop_plan/backend/05_collection_run_admin_api.md)
- 현재 Slice: C3 completed (`2026-08-10`)

## 목적

기존 `CollectionRun` DB 스키마와 관리자 접근 제어 기준선(`get_current_admin_payload`) 위에 수집 실행 이력 목록/상세 조회 및 안전한 수동 수집 실행(`202 Accepted`) API 기준선을 구축하기 위한 개발 기록이다.

## Forest 범위

- 관리자 전용 CollectionRun 목록·상세 DTO와 endpoint (`GET /api/v1/admin/collection-runs`, `GET /api/v1/admin/collection-runs/{id}`)
- pagination, source·status·run_type·trigger_type·기간 필터와 4단계 정렬
- 오래 지속된 `running` 실행의 `stale` 판정 규칙 (2시간 초과 시 stale)
- 수동 수집 실행 요청 (`POST /api/v1/admin/collection-runs`), 중복/동시 실행 방지 (`409 Conflict`)
- 인증·권한·오류·PostgreSQL 통합 테스트
- OpenAPI·운영·CollectionRun 기준 문서 동기화

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **C0** | **관리자 API·상태 계약 확정 (Contract & Specification)** | **completed** | DTO 명세(`collection_run_admin.py`), API 계약서(`admin_collection_runs.md`), 401/403/404/409/422 상태코드 및 2시간 Stale 판정 규칙 확정 완료 |
| **C1** | **실행 이력 목록·상세 API 구현 (Run History List & Detail)** | **completed** | `CollectionRunAdminRepository`, `CollectionRunAdminService`, `GET /api/v1/admin/collection-runs`, `GET /api/v1/admin/collection-runs/{id}` 엔드포인트, 페이징/필터/정렬/404/401/403 및 Stale 감지 테스트 완료 (7 passed) |
| **C2** | **수동 실행과 stale 판정 구현 (Manual Execution & Stale Handling)** | **completed** | `POST /api/v1/admin/collection-runs` 수동 수집 `202 Accepted` 반환, 2시간 미만 활성 running 존재 시 `409 Conflict` 중복 방지, 2시간 이상 stale 시 새 기동 허용 및 유효성 422 테스트 완료 (11 passed) |
| **C3** | **PostgreSQL·권한·문서 통합 검증 (PostgreSQL & Documentation Integration)** | **completed** | PostgreSQL 환경 연결 구조 검증, OpenAPI securityScheme (`HTTPBearer`) 등록 확인, Frontend 인계 계약(`BE-ADMIN-RUN-HISTORY`) 확정 및 문서 무결성 통과 |

## 구현 내용

### Slice C0 - 관리자 API·상태 계약 확정

1. **API 계약서 작성 ([admin_collection_runs.md](../../../api/admin_collection_runs.md))**
   - `GET /api/v1/admin/collection-runs`: 목록 조회, Pagination(`page`, `size`), 필터(`source_id`, `status`, `run_type`, `trigger_type`, `start_date`, `end_date`), 정렬(`started_at DESC`) 계약 확정.
   - `GET /api/v1/admin/collection-runs/{run_id}`: 단건 상세 조회 DTO 및 404 Not Found 계약 확정.
   - `POST /api/v1/admin/collection-runs`: 수동 수집 실행 요청 `202 Accepted` 및 중복 실행 중일 때 `409 Conflict` 반환 계약 확정.

2. **관리자 CollectionRun DTO 정의 ([collection_run_admin.py](../../../../backend/app/schemas/collection_run_admin.py))**
   - `CollectionRunAdminItem`, `CollectionRunAdminDetail`, `CollectionRunAdminListResponse`, `CollectionRunTriggerRequest`, `CollectionRunTriggerResponse` 작성.

### Slice C1 - 실행 이력 목록·상세 API 구현

1. **CollectionRun Repository 및 Service ([collection_run_admin.py](../../../../backend/app/repositories/collection_run_admin.py), [collection_run_admin.py](../../../../backend/app/services/collection_run_admin.py))**
   - `get_admin_collection_runs`: source_id, status, run_type, trigger_type, start_date, end_date 필터링 및 `started_at DESC` 페이징 조회 구현.
   - `get_admin_collection_run_by_id`: run_id 기준 단건 상세 DB 조회 구현.
   - `check_is_stale`: 2시간(7,200초) 이상 `running` 상태 유지 시 동적 `is_stale = true` 계산.

2. **API 엔드포인트 및 권한 연동 ([collection_run_admin.py](../../../../backend/app/api/v1/endpoints/collection_run_admin.py))**
   - `GET /api/v1/admin/collection-runs` 및 `GET /api/v1/admin/collection-runs/{run_id}` 라우트 구현.
   - `get_current_admin_payload` dependency 연동으로 토큰 미제공 시 `401 Unauthorized`, 비관리자 접근 시 `403 Forbidden`, 존재하지 않는 run_id 시 `404 Not Found` 반환.

### Slice C2 - 수동 실행과 stale 판정 구현

1. **수동 수집 기동 및 중복 방지 Service ([collection_run_admin.py](../../../../backend/app/services/collection_run_admin.py))**
   - `trigger_manual_collection_run_service`: 동일 `source_id`에 진행 중인 active (`is_stale == False`) running 수집이 존재하는지 `get_active_running_collection_run()`으로 검사.
   - 진행 중인 active running 수집이 있으면 `409 Conflict` 사유 반환.
   - active running이 없거나 기존 running이 Stale(2시간 초과)인 경우 `create_admin_collection_run()`으로 새로운 `running` 상태 수집건을 생성하고 `202 Accepted` 트리거 응답 반환.

2. **수동 수집 트리거 엔드포인트 ([collection_run_admin.py](../../../../backend/app/api/v1/endpoints/collection_run_admin.py))**
   - `POST /api/v1/admin/collection-runs`: `CollectionRunTriggerRequest` 수신 시 `202 Accepted` 응답 처리.
   - Conflict 409 반환 시 `error` 객체 및 `active_run_id`, `started_at` 세부 정보 포함.

### Slice C3 - PostgreSQL·권한·문서 통합 검증 및 Frontend 인계

1. **Frontend 인계 계약 (`BE-ADMIN-RUN-HISTORY`) 확정**
   - Frontend CollectionRun Admin UI (`Frontend 03`)에 전달할 백엔드 API 계약을 확정함.
   - `GET /api/v1/admin/collection-runs`: 페이지네이션 목록 및 Stale 감지 데이터 제공
   - `GET /api/v1/admin/collection-runs/{run_id}`: 단건 수집 카운트 및 오류 타입 상세 데이터 제공
   - `POST /api/v1/admin/collection-runs`: 수동 수집기 트리거 (`202 Accepted` / `409 Conflict`)
2. **OpenAPI Security & 문서 무결성 동기화**
   - FastAPI `custom_openapi()`에 `HTTPBearer` securityScheme 노출 확인
   - `python scripts/validate_docs.py` 통과

## 2026-08-23 Docker actual 결함 수정

기존 C2 구현은 `202`와 `running` 행만 만들고 실제 Collector를 시작하지 않아
완료 기준의 “실행 결과가 CollectionRun과 연결됨”을 충족하지 못했다. DEP5 격리
환경에서 이 차이를 확인해 등록된 live Collector → Runtime Raw replay → DB import를
process 내부 background task로 연결하고, 성공·부분 실패·실패를 같은 `run_id`의
terminal 상태와 count로 기록하도록 수정했다. 등록되지 않은 Source와 500건 초과
요청은 `422`이며, 외부 실패도 `running`에 방치하지 않는다.

공개 천안 Source PostgreSQL actual은 `202 → succeeded`, Raw 3건, accepted 1건,
unchanged 1건, failed 0건이었다. 관련 Backend 회귀는 `177 passed, 17 skipped`다.
새 receipt 기반 역할 검증 전이므로 이 기록만으로 Docker Gate를 PASS 처리하지
않는다.

## 주요 변경 파일

- `backend/app/schemas/collection_run_admin.py`: CollectionRun 관리자 DTO 정의
- `backend/app/repositories/collection_run_admin.py`: CollectionRun DB 목록/상세/활성조회/생성 Repository 구현
- `backend/app/services/collection_run_admin.py`: Stale 판정 계산 및 수동 기동 202 / 중복 409 서비스 구현
- `backend/app/api/v1/endpoints/collection_run_admin.py`: CollectionRun 목록, 상세, 수동 실행 엔드포인트 구현
- `backend/app/api/v1/api.py`: `/admin/collection-runs` 라우터 등록
- `backend/tests/test_collection_run_admin_api.py`: Slice C0~C3 단위/통합 테스트 (11 passed)
- `docs/api/admin_collection_runs.md`: CollectionRun 관리자 API 계약서 작성
- `docs/development/develop_plan/backend/05_collection_run_admin_api.md`: Forest 상태 completed 갱신
- `docs/development/development_notes/backend/collection_run_admin_api.md`: Forest 마감 개발 기록 작성

## 설계 결정

1. **Stale 상태의 보존성 (Non-destructive Stale Handling)**:
   - 오래 지연된 `running` 수집건을 서버가 임의로 `failed`나 `succeeded`로 변경하지 않고, `is_stale: true` 플래그로 판단 근거를 보존하여 관리자 운영 확인 지점을 명확히 제공함.
2. **동일 Source 중복 실행 방지 (`409 Conflict`)**:
   - 수동 실행 시 동일 수집원에 이미 정상 진행 중인 `running` 수집이 존재할 경우 `409 Conflict`를 반환하여 리소스 낭비 및 경쟁 상태(Race Condition)를 방지함.

## 검증 결과

- **CollectionRun 관리자 전용 단위/통합 테스트**: `pytest backend/tests/test_collection_run_admin_api.py` 실행 -> **11 Passed**
- **문서화 무결성 검증**: `python scripts/validate_docs.py` 실행 -> **Pass**
- **기존 백엔드 회귀 테스트**: `pytest backend/tests` 실행 -> **141 Passed, 15 Skipped**

## 남은 작업

- 없음 (Backend 05 CollectionRun Admin API Forest 완료)
- 후속 Forest: [Frontend CollectionRun Admin UI](../../develop_plan/frontend/03_collection_run_admin_ui.md)

# Backend CollectionRun Admin API Forest 개발 기록

## 작업 정보

- 기간: `2026-08-10`
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `feature/backend/admin-access-control`
- 선행 Forest: [Backend Admin Access Control](admin_access_control.md)
- 관련 계획: [Backend CollectionRun Admin API Plan](../../develop_plan/backend/05_collection_run_admin_api.md)
- 현재 Slice: C0 completed (`2026-08-10`)

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
| **C1** | 실행 이력 목록·상세 API 구현 | draft | Repository, Service 및 GET 엔드포인트 구현 예정 |
| **C2** | 수동 실행 및 Stale 판정 구현 | draft | 수동 수집 202 Trigger, 409 중복 실행 방지 및 Stale 서비스 구현 예정 |
| **C3** | PostgreSQL·권한·문서 통합 검증 | draft | 실제 DB 회귀 검증, OpenAPI 동기화 및 Forest completed 마감 예정 |

## 구현 내용

### Slice C0 - 관리자 API·상태 계약 확정

1. **API 계약서 작성 ([admin_collection_runs.md](../../../api/admin_collection_runs.md))**
   - `GET /api/v1/admin/collection-runs`: 목록 조회, Pagination(`page`, `size`), 필터(`source_id`, `status`, `run_type`, `trigger_type`, `start_date`, `end_date`), 정렬(`started_at DESC`) 계약 확정.
   - `GET /api/v1/admin/collection-runs/{run_id}`: 단건 상세 조회 DTO 및 404 Not Found 계약 확정.
   - `POST /api/v1/admin/collection-runs`: 수동 수집 실행 요청 `202 Accepted` 및 중복 실행 중일 때 `409 Conflict` 반환 계약 확정.

2. **관리자 CollectionRun DTO 정의 ([collection_run_admin.py](../../../../backend/app/schemas/collection_run_admin.py))**
   - `CollectionRunAdminItem`, `CollectionRunAdminDetail`, `CollectionRunAdminListResponse`, `CollectionRunTriggerRequest`, `CollectionRunTriggerResponse` 작성.

3. **Stale 및 중복 실행 판정 규칙 확정**
   - `status == 'running'` 이고 `finished_at == null` 인 수집건이 `started_at` 기준 2시간(7,200초) 이상 지연되면 `is_stale = true`로 판정.
   - 동일 `source_id`에 Stale이 아닌 `running` 수집건이 진행 중일 때 수동 실행 요청 시 `409 Conflict` 반환.

## 주요 변경 파일

- `backend/app/schemas/collection_run_admin.py`: CollectionRun 관리자 API 전용 DTO 스마 정의
- `docs/api/admin_collection_runs.md`: CollectionRun 관리자 API 계약 명세서 작성
- `docs/development/develop_plan/backend/05_collection_run_admin_api.md`: Slice C0 completed 갱신
- `docs/development/development_notes/backend/collection_run_admin_api.md`: Backend 05 개발 기록 작성

## 설계 결정

1. **Stale 상태의 보존성 (Non-destructive Stale Handling)**:
   - 오래 지연된 `running` 수집건을 서버가 임의로 `failed`나 `succeeded`로 변경하지 않고, `is_stale: true` 플래그로 판단 근거를 보존하여 관리자 운영 확인 지점을 명확히 제공함.
2. **동일 Source 중복 실행 방지 (`409 Conflict`)**:
   - 수동 실행 시 동일 수집원에 이미 정상 진행 중인 `running` 수집이 존재할 경우 `409 Conflict`를 반환하여 리소스 낭비 및 경쟁 상태(Race Condition)를 방지함.

## 검증 결과

- **문서화 무결성 검증**: `python scripts/validate_docs.py` 실행 -> **Pass**
- **기존 백엔드 회귀 테스트**: `pytest backend/tests` 실행 -> **124 Passed, 15 Skipped**

## 남은 작업

- Slice C1: CollectionRun Repository, Service 및 목록/상세 GET 엔드포인트 구현
- Slice C2: 수동 실행 `202 Accepted` Trigger 서비스, 중복 실행 `409` 방지 및 Stale 판정 로직 구현
- Slice C3: 실제 PostgreSQL DB 통합 테스트, OpenAPI security 연동, 문서 최종 검증 및 Forest 마감

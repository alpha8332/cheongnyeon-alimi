# Integration 09 Admin Data and Log Console Forest 개발 기록

## 작업 정보

- 기간: `2026-08-11`
- 담당 영역: Backend·Frontend
- 상태: in-progress
- 브랜치: `feature/backend/policy-recommendation`
- 선행 Forest: Backend 04 Admin Access Control, Integration 05 Contract Baseline
- 관련 계획: [Integration 09 Admin Data Log Console Plan](../../develop_plan/integration/09_admin_data_log_console.md)
- 현재 Slice: AO1 completed (`2026-08-11`)

## 목적

인증된 관리자가 PostgreSQL에 적재된 정책 데이터를 CSV형 표 형식으로 안전하게 탐색하고 row 상세를 읽기 전용(Read-Only)으로 조회하기 위한 관리자 데이터 탐색 API 기준선을 구축하기 위한 개발 기록이다.

## Forest 범위

- 관리자 읽기 전용 정책 데이터 표 DTO (`AdminPolicyItem`, `AdminPolicyDetail`, `AdminPolicyListResponse`)
- 서버 페이징, Allowlist 기반 정렬(`id`, `created_at`, `updated_at`, `title`, `collected_at`) 및 필터링 (`category`, `region`, `status`, `data_quality_status`, `source_id`)
- 최대 page size 100 강제 및 임의 SQL 주입 차단
- 관리자 권한 인증 세션(`get_current_admin_payload`) 검증 (`401 Unauthorized`, `403 Forbidden`)
- API 엔드포인트 (`GET /api/v1/admin/policies`, `GET /api/v1/admin/policies/{policy_id}`)
- 단위·통합 테스트 및 문서화

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **AO0** | **DB·logging inventory 및 계약** | **completed** | `AdminPolicyItem` DTO 및 API 계약 명세(`admin_policies.md`) 확정 |
| **AO1** | **Backend 정책 데이터 탐색 API** | **completed** | `get_admin_policies` 레포지토리, `list_admin_policies_service`, `GET /api/v1/admin/policies`, `GET /api/v1/admin/policies/{id}` 구현, 5개 테스트 100% 통과 |
| **AO2** | Backend 구조화 파일 logging | draft | UTF-8 파일 로거, Log Rotation, Redaction 구현 예정 |
| **AO3** | Backend 로그 조회·삭제·감사 API | draft | `GET/DELETE /api/v1/admin/logs` 및 Audit 감사 기록 구현 예정 |
| **AO4** | Frontend 데이터·로그 관리자 UI | draft | `/admin/data` CSV형 데이터 표 UI 구현 예정 |
| **AO5** | 실제 진단 E2E | draft | 실제 DB -> FastAPI -> React 관리자 진단 E2E 검증 예정 |

## 구현 내용

### Slice AO1 - Backend 정책 데이터 탐색 API (Read-Only)

1. **관리자 정책 데이터 DTO 스키마 구현 ([admin_policy.py](../../../../backend/app/schemas/admin_policy.py))**
   - `AdminPolicyItem`: 관리자 표 Row 전용 DTO (`id`, `source_id`, `source_name`, `external_id`, `title`, `organization`, `categories`, `regions`, `data_quality_status`, `application_status`, `collected_at`, `created_at`, `updated_at`).
   - `AdminPolicyDetail`: 단건 상세 읽기 전용 DTO.
   - `AdminPolicyListResponse`: `total`, `page`, `limit`, `items[]`.

2. **읽기 전용 Repository 및 서비스 ([admin_policy.py](../../../../backend/app/repositories/admin_policy.py), [admin_policy.py](../../../../backend/app/services/admin_policy.py))**
   - `ALLOWLIST_SORT_FIELDS`: `id`, `created_at`, `updated_at`, `title`, `collected_at` 컬럼으로 정렬 범위 제한.
   - 최대 `limit` 100 강제 적용 및 임의 SQL 문 입력 원천 차단.

3. **관리자 전용 API 엔드포인트 ([admin_policy.py](../../../../backend/app/api/v1/endpoints/admin_policy.py))**
   - `GET /api/v1/admin/policies` 및 `GET /api/v1/admin/policies/{policy_id}` 구현 및 `api.py` 라우터 등록.
   - `get_current_admin_payload` 인증 적용으로 세션 검증 보장.

## 주요 변경 파일

- `backend/app/schemas/admin_policy.py`: 관리자 정책 데이터 표 DTO 정의
- `backend/app/repositories/admin_policy.py`: 읽기 전용 레포지토리 및 Allowlist 정렬 구현
- `backend/app/services/admin_policy.py`: 읽기 전용 정책 데이터 서비스 구현
- `backend/app/api/v1/endpoints/admin_policy.py`: 관리자 정책 데이터 API 라우터 구현
- `backend/app/api/v1/api.py`: `/admin/policies` 라우터 등록
- `backend/tests/test_admin_policy_api.py`: 401, 404, 페이징, Allowlist 정렬 및 상세 테스트 (5 passed)
- `docs/api/admin_policies.md`: 관리자 읽기 전용 정책 데이터 표 API 계약 명세서

## 설계 결정

1. **완전 읽기 전용 계약 (Strict Read-Only Contract)**:
   - 데이터 수정, 생성, 삭제 경로가 일체 존재하지 않도록 하여 오직 데이터 탐색 목적으로만 사용되도록 설계함.
2. **Allowlist 기반 정렬 (Allowlist Sort Protection)**:
   - 클라이언트 쿼리 파라미터(`sort_by`)에 승인된 컬럼만 적용하여 arbitrary SQL 주입 및 오탐 위험을 원천 차단함.

## 검증 결과

- **관리자 정책 API 단위/통합 테스트**: `pytest backend/tests/test_admin_policy_api.py` ➔ **5 Passed**
- **백엔드 전체 회귀 테스트**: `pytest backend/tests` ➔ **152 Passed, 15 Skipped**
- **문서 무결성 검증**: `python scripts/validate_docs.py` ➔ **Pass**

## 남은 작업

- `Slice AO2`: Backend 구조화 UTF-8 파일 logging, Rotation & Redaction 구현
- `Slice AO3`: Backend 로그 파일/이벤트 조회 및 Archive 삭제 감사 API 구현

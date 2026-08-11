# Integration 09 Admin Data and Log Console Forest 개발 기록

## 작업 정보

- 기간: `2026-08-11`
- 담당 영역: Backend·Frontend
- 상태: in-progress
- 브랜치: `feature/backend/policy-recommendation`
- 선행 Forest: Backend 04 Admin Access Control, Integration 05 Contract Baseline
- 관련 계획: [Integration 09 Admin Data Log Console Plan](../../develop_plan/integration/09_admin_data_log_console.md)
- 현재 Slice: AO1, AO2 completed (`2026-08-11`)

## 목적

인증된 관리자가 PostgreSQL에 적재된 정책 데이터를 CSV형 표 형식으로 안전하게 탐색하고 row 상세를 읽기 전용(Read-Only)으로 조회하며, 백엔드 서버에서 발생하는 이벤트를 UTF-8 JSON Lines 구조화 파일 로그로 보존 및 개인정보/비밀 마스킹(Redaction)을 적용하기 위한 개발 기록이다.

## Forest 범위

- 관리자 읽기 전용 정책 데이터 표 DTO (`AdminPolicyItem`, `AdminPolicyDetail`, `AdminPolicyListResponse`)
- 서버 페이징, Allowlist 기반 정렬 및 필터링
- 백엔드 구조화 UTF-8 파일 로거 (`RedactingJsonFormatter`, `RotatingFileHandler`)
- Log Rotation (10MB 기준, 최대 5개 백업) 및 비밀번호/토큰/PIN 마스킹 (`***REDACTED***`)
- 관리자 권한 인증 세션(`get_current_admin_payload`) 검증
- 단위·통합 테스트 및 문서화

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **AO0** | **DB·logging inventory 및 계약** | **completed** | `AdminPolicyItem` DTO 및 API 계약 명세(`admin_policies.md`) 확정 |
| **AO1** | **Backend 정책 데이터 탐색 API** | **completed** | `get_admin_policies` 레포지토리, `list_admin_policies_service`, `GET /api/v1/admin/policies`, `GET /api/v1/admin/policies/{id}` 구현, 5개 테스트 100% 통과 |
| **AO2** | **Backend 구조화 파일 logging** | **completed** | `RedactingJsonFormatter`, `setup_file_logging`, `RotatingFileHandler` 구현, 2개 파일 로깅 테스트 100% 통과 |
| **AO3** | Backend 로그 조회·삭제·감사 API | draft | `GET/DELETE /api/v1/admin/logs` 및 Audit 감사 기록 구현 예정 |
| **AO4** | Frontend 데이터·로그 관리자 UI | draft | `/admin/data` CSV형 데이터 표 UI 구현 예정 |
| **AO5** | 실제 진단 E2E | draft | 실제 DB -> FastAPI -> React 관리자 진단 E2E 검증 예정 |

## 구현 내용

### Slice AO1 - Backend 정책 데이터 탐색 API (Read-Only)

1. **관리자 정책 데이터 DTO 스키마 구현 ([admin_policy.py](../../../../backend/app/schemas/admin_policy.py))**
   - `AdminPolicyItem`, `AdminPolicyDetail`, `AdminPolicyListResponse` DTO 구축.

2. **읽기 전용 Repository 및 서비스 ([admin_policy.py](../../../../backend/app/repositories/admin_policy.py), [admin_policy.py](../../../../backend/app/services/admin_policy.py))**
   - `ALLOWLIST_SORT_FIELDS` 컬럼 정렬 제한 및 최대 `limit` 100 강제 적용.

3. **관리자 전용 API 엔드포인트 ([admin_policy.py](../../../../backend/app/api/v1/endpoints/admin_policy.py))**
   - `GET /api/v1/admin/policies` 및 `GET /api/v1/admin/policies/{policy_id}` 구현.

### Slice AO2 - Backend 구조화 파일 logging & Redaction

1. **구조화 JSON Lines 파일 로거 ([logging_config.py](../../../../backend/app/core/logging_config.py))**
   - `RedactingJsonFormatter`: `timestamp`, `level`, `component`, `event` 및 correlation 필드 구조화.
   - `sanitize_value`: `pin`, `token`, `password`, `secret`, `api_key` 키워드가 들어간 민감 정보를 `***REDACTED***`로 마스킹.

2. **Log Rotation 및 UTF-8 인코딩 설정**
   - `RotatingFileHandler`: `backend/logs/app.log` 경로에 10MB 기준 rotation 및 백업 5개 보존.
   - `setup_file_logging()`을 FastAPI `main.py` 시작 시 호출하여 stdout과 병행 작동.

## 주요 변경 파일

- `backend/app/core/logging_config.py`: 구조화 파일 로거 및 마스킹 포맷터 구현
- `backend/app/main.py`: `setup_file_logging()` 초기화 연동
- `backend/tests/test_file_logging.py`: 파일 로거 생성 및 Redaction 마스킹 테스트 (2 passed)
- `backend/app/schemas/admin_policy.py`: 관리자 정책 데이터 표 DTO 정의
- `backend/app/repositories/admin_policy.py`: 읽기 전용 레포지토리 및 Allowlist 정렬 구현
- `backend/app/services/admin_policy.py`: 읽기 전용 정책 데이터 서비스 구현
- `backend/app/api/v1/endpoints/admin_policy.py`: 관리자 정책 데이터 API 라우터 구현
- `backend/app/api/v1/api.py`: `/admin/policies` 라우터 등록
- `backend/tests/test_admin_policy_api.py`: 관리자 정책 API 테스트 (5 passed)
- `docs/api/admin_policies.md`: 관리자 읽기 전용 정책 데이터 표 API 계약 명세서

## 설계 결정

1. **JSON Lines 표준 직렬화 (JSON Lines Format)**:
   - 한 이벤트 당 한 줄의 UTF-8 JSON 개체로 저장하여 대용량 파일 로그 파싱 및 검색이 용이하도록 설계함.
2. **이중 마스킹 필터 (Double-Layer Redaction)**:
   - 딕셔너리 구조체 탐색과 정규 표현식 패턴을 함께 적용하여 로그에 어떠한 비밀 키워드(PIN, token, password 등)도 노출되지 않도록 원천 마스킹함.

## 검증 결과

- **파일 로깅 테스트**: `pytest backend/tests/test_file_logging.py` ➔ **2 Passed**
- **백엔드 전체 회귀 테스트**: `pytest backend/tests` ➔ **154 Passed, 15 Skipped**
- **문서 무결성 검증**: `python scripts/validate_docs.py` ➔ **Pass**

## 남은 작업

- `Slice AO3`: Backend 로그 파일/이벤트 조회 및 Archive 삭제 감사 API 구현

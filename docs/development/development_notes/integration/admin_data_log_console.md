# Integration 09 Admin Data and Log Console Forest 개발 기록

## 작업 정보

- 기간: `2026-08-11`~`2026-08-14`
- 담당 영역: Backend·Frontend
- 상태: in-progress
- 브랜치: `feature/backend/policy-recommendation`
- 선행 Forest: Backend 04 Admin Access Control, Integration 05 Contract Baseline
- 관련 계획: [Integration 09 Admin Data Log Console Plan](../../develop_plan/integration/09_admin_data_log_console.md)
- 현재 Slice: AO1~AO4 completed, AO5 pending (`2026-08-14` DTL4-5 parity)

## 목적

인증된 관리자가 PostgreSQL에 적재된 정책 데이터를 CSV형 표 형식으로 안전하게 탐색하고 row 상세를 읽기 전용(Read-Only)으로 조회하며, 백엔드 서버에서 발생하는 이벤트를 UTF-8 JSON Lines 구조화 파일 로그로 보존하고, 회전 완료된 Archive 로그 파일을 안전하게 삭제하며 Audit 감사 이력을 생성하기 위한 개발 기록이다.

## Forest 범위

- 관리자 읽기 전용 정책 데이터 표 DTO (`AdminPolicyItem`, `AdminPolicyDetail`, `AdminPolicyListResponse`)
- 서버 페이징, Allowlist 기반 정렬 및 필터링
- 백엔드 구조화 UTF-8 파일 로거 (`RedactingJsonFormatter`, `RotatingFileHandler`)
- Log Rotation (10MB 기준, 최대 5개 백업) 및 비밀번호/토큰/PIN 마스킹 (`***REDACTED***`)
- 로그 파일/이벤트 조회 API (`GET /api/v1/admin/logs/files`, `GET /api/v1/admin/logs/events`)
- 회전 완료된 Archive 로그 파일 삭제 API (`DELETE /api/v1/admin/logs/archives/{file_id}`) 및 별도 감사 기록(`AdminAuditEvent`) 생성
- 활성 파일(`app.log`) 직접 삭제 차단 및 Path Traversal 방어
- 단위·통합 테스트 및 문서화

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **AO0** | **DB·logging inventory 및 계약** | **completed** | `AdminPolicyItem` DTO 및 API 계약 명세(`admin_policies.md`, `admin_logs.md`) 확정 |
| **AO1** | **Backend 정책 데이터 탐색 API** | **completed** | `get_admin_policies` 레포지토리, `list_admin_policies_service`, `GET /api/v1/admin/policies`, `GET /api/v1/admin/policies/{id}` 구현, 7개 테스트 100% 통과 |
| **AO2** | **Backend 구조화 파일 logging** | **completed** | `RedactingJsonFormatter`, `setup_file_logging`, `RotatingFileHandler` 구현, 2개 파일 로깅 테스트 100% 통과 |
| **AO3** | **Backend 로그 조회·삭제·감사 API** | **completed** | 파일·event 조회, archive 삭제와 현재 로그 rotate 정리, path 보호·감사 테스트 통과 |
| **AO4** | **Frontend 데이터·로그 관리자 UI** | **completed** | 실제 Backend endpoint·DTO 기준 TypeScript·Mock·소비 테스트 정렬 |
| **AO5** | 실제 진단 E2E | draft | 실제 DB -> FastAPI -> React 관리자 진단 E2E 검증 예정 |

## 구현 내용

### Slice AO1 - Backend 정책 데이터 탐색 API (Read-Only)

1. **관리자 정책 데이터 DTO 스키마 구현 ([admin_policy.py](../../../../backend/app/schemas/admin_policy.py))**
2. **읽기 전용 Repository 및 서비스 ([admin_policy.py](../../../../backend/app/repositories/admin_policy.py), [admin_policy.py](../../../../backend/app/services/admin_policy.py))**
3. **관리자 전용 API 엔드포인트 ([admin_policy.py](../../../../backend/app/api/v1/endpoints/admin_policy.py))**

### Slice AO2 - Backend 구조화 파일 logging & Redaction

1. **구조화 JSON Lines 파일 로거 ([logging_config.py](../../../../backend/app/core/logging_config.py))**
2. **Log Rotation 및 UTF-8 인코딩 설정 ([main.py](../../../../backend/app/main.py))**

### Slice AO3 - Backend 로그 조회·삭제·감사 API

1. **로그 관리 DTO 스키마 구현 ([admin_log.py](../../../../backend/app/schemas/admin_log.py))**
   - `LogFileItem`, `LogFileListResponse`: 로그 파일 메타데이터 목록.
   - `LogEventItem`, `LogEventListResponse`: JSON Lines 파싱 이벤트 목록.
   - `LogDeleteResponse`, `LogRotateResponse`: 삭제·현재 로그 정리 결과와 `audit_id`.

2. **로그 서비스 및 감사 저장소 ([admin_log.py](../../../../backend/app/services/admin_log.py))**
   - `list_log_files_service`: `LOG_DIR` 스캔 및 파일 메타데이터 추출.
   - `get_log_events_service`: JSON Lines 파싱 및 `level`, `component`, `q` 검색어 필터링.
   - `delete_archived_log_file_service`: 회전된 Archive 파일만 삭제 허용, `app.log` 활성 파일 삭제 시도 시 차단, 성공/실패 감사 이력 저장.
   - `rotate_current_log_service`: 열린 handler를 기존 numbered archive와 충돌하지 않는 고유 임시 archive로 안전하게 rotate하고 그 작업으로 생성된 archive만 삭제하며 기존 archive는 이름과 내용까지 보존.

3. **관리자 로그 API 엔드포인트 ([admin_log.py](../../../../backend/app/api/v1/endpoints/admin_log.py))**
   - `GET /api/v1/admin/logs/files`: 파일 목록 조회
   - `GET /api/v1/admin/logs/events`: 파싱된 이벤트 페이징 및 필터 조회
   - `DELETE /api/v1/admin/logs/archives/{file_id}`: Archive 삭제 및 감사 기록
   - `POST /api/v1/admin/logs/rotate-current`: 현재 로그 rotate 정리 및 감사 기록

### DTL4-5 Backend·Frontend 계약 대조 (`2026-08-14`)

- Backend의 `/api/v1/admin/policies` `page`·`limit`·`sort_by`·`order`와
  `{items,total,page,limit}`를 Frontend TypeScript·Mock에 그대로 반영했다.
- 로그는 `/api/v1/admin/logs/files`, `/events`, `/archives/{file_id}`와
  `/rotate-current`로 통일했다. 파일 응답은 `{files}`, 이벤트 응답은
  `{events,total,page,limit}`이며 API에 없는 event/file 상세 ID를 제거했다.
- request·CollectionRun·Source correlation producer를 연결했고 PIN·token·Raw·
  SQL parameter 비노출 회귀를 보강했다.
- 관련 Backend 35건, Frontend 전체 161건과 production build가 통과했다.

## 주요 변경 파일

- `backend/app/schemas/admin_log.py`: 로그 파일, 이벤트, 삭제 응답 DTO 정의
- `backend/app/services/admin_log.py`: 로그 스캔, 파싱, archive 삭제 및 감사 이력 서비스 구현
- `backend/app/api/v1/endpoints/admin_log.py`: 로그 목록/이벤트/삭제 API 라우터 구현
- `backend/app/api/v1/api.py`: `/admin/logs` 라우터 등록
- `backend/tests/test_admin_log_api.py`: 401, 400, 활성 파일 보호, archive 보존, 삭제 및 감사 테스트 (9 passed)
- `docs/api/admin_logs.md`: 관리자 로그 및 감사 API 계약 명세서

## 설계 결정

1. **활성 파일 직접 삭제 방지 (Active File Safety)**:
   - 현재 로깅 기록 중인 `app.log` 파일의 핸들 파손 및 데이터 유실을 막기 위해 활성 파일은 직접 삭제를 원천 금지하고(`400 Bad Request`), 회전 완료된 Archive(`app.log.1` 등)만 삭제하도록 제약함.
2. **별도 비삭제 감사 기록 (Independent Audit Trail)**:
   - 로그 삭제 작업이 수행될 경우 삭제 성공 여부와 시각, 담당자, 대상 파일명을 독립된 `AUDIT_TRAIL` 감사 저장소에 기록하여 운영 투명성을 보장함.

## 검증 결과

- **DTL4-5 관리자 보안·로그 집중 테스트**: **36 Passed**
- **Frontend 전체 소비 테스트**: **161 Passed**
- **Frontend production build**: **Passed**
- **관리자 observability Mock Browser E2E**: **19 Passed, 1 Skipped**
- **백엔드 전체 회귀 테스트**: `pytest backend/tests` ➔ **160 Passed, 15 Skipped**
- **문서 무결성 검증**: `python scripts/validate_docs.py` ➔ **Pass**

## 남은 작업

- 실제 PostgreSQL·Runtime log·Real API Browser 진단 E2E (`Slice AO5`)
- 현재 `AUDIT_TRAIL`은 process-local이므로 재시작 간 영속 감사 저장소는 AO5
  완료 조건으로 남아 있다.

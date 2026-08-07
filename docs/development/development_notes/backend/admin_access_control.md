# Backend Admin Access Control Forest 개발 기록

## 작업 정보

- 기간: `2026-08-07`
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `feature/backend/admin-access-control`
- 선행 Forest: [Backend Policy Runtime Safety](policy_runtime_safety.md)
- 관련 계획: [Backend Admin Access Control Plan](../../develop_plan/backend/04_admin_access_control.md)
- 현재 Slice: A2 completed (`2026-08-07`)

## 목적

비밀번호(4자리 PIN) 기반 단일 관리자 세션 생성 및 접근 제어 기준선을 구축하기 위한 개발 기록이다. 로컬 개발 환경에서는 최초 PIN `0000`을 제공하되, 프로덕션 배포 환경에서는 명시적 해시/시크릿 미설정 시 자동 거부(fail-closed)하도록 보안 계약을 준수하며 점진적 락아웃(5, 10, 30, 60, 120, 300초) 및 공통 관리자 권한 검증 Dependency(`get_current_admin_payload`)를 구축한다.

## Forest 범위

- 아이디 없이 4자리 숫자 PIN만 받는 관리자 session endpoint (`POST /api/v1/admin/session`)
- `development`·localhost 전용 최초 PIN `0000` 경계
- 배포 환경의 관리자 PIN hash·서명 secret 필수 설정과 fail-closed
- 검증 성공 시 짧은 수명의 서명 관리자 token 발급 및 검증 서비스
- 실패 횟수 제한·단계별 점진적 락아웃 (5회 이상 실패 시 5초 ➔ 10초 ➔ 30초 ➔ 60초 ➔ 120초 ➔ 300초 순차 적용)
- 관리자 권한 판정 경계와 공통 FastAPI dependency (`get_current_admin_payload`)
- 인증 실패 `401`과 권한 부족 `403`, rate limit `429`, 파라미터 유효성 `422` 계약
- 비밀정보·credential의 설정·로그·오류 비노출 및 보호 라우트 누락 방지 테스트

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **A0** | **인증·권한 계약 결정 (Contract & Specification)** | **completed** | `POST /api/v1/admin/session` DTO, HTTP 401/403/429/422 상태코드 및 로컬 `0000` / production fail-closed 계약 구현 및 테스트 완료 |
| **A1** | **관리자 인증 경계 구현 (Admin Authentication Boundary)** | **completed** | PIN 해시 검증, HMAC-SHA256 세션 토큰 생성/검증 서비스(`create_admin_session_token`, `verify_admin_session_token`), 점진적 Rate Limit 락아웃(5->10->30->60->120->300초) 및 Credential 비노출 테스트 완료 |
| **A2** | **관리자 권한 경계 구현 (Admin Authorization Boundary)** | **completed** | 공통 관리자 권한 검증 FastAPI Dependency (`get_current_admin_payload`), `GET /api/v1/admin/me` 샘플 라우트, HTTP 401/403 구분 및 라우트 보호 누락 탐지 테스트 완료 (19 passed) |
| **A3** | OpenAPI·회귀·문서 동기화 | draft | 보안 정의 명세 및 README/env 가이드 작성 예정 |

## 구현 내용

### Slice A0 - 인증·권한 계약 결정

1. **관리자 세션 요청 및 응답 DTO ([admin_access.py](../../../../backend/app/schemas/admin_access.py))**
   - `AdminSessionCreate`: `pin` 4자리 숫자 Regex(`^\d{4}$`) 검증
   - `AdminSessionResponse`: `access_token`, `token_type`("bearer"), `expires_in`(초 단위), `role`("admin")

2. **환경별 PIN 인증 및 Fail-closed 로직 ([admin_access.py](../../../../backend/app/services/admin_access.py))**
   - 로컬/개발 환경(`development`, `local`, `test`)에서 `ADMIN_PIN_HASH` 미설정 시 `0000` 해시(`9af15b33...`)를 기본 사용.
   - 프로덕션 환경(`production`)에서 `ADMIN_PIN_HASH` 미설정 시 `None` 반환하여 fail-closed 처리.

3. **엔드포인트 및 라우터 등록 ([admin_access.py](../../../../backend/app/api/v1/endpoints/admin_access.py))**
   - `POST /api/v1/admin/session` 엔드포인트 구현 및 `api_router`에 `/admin` prefix로 포함.

### Slice A1 - 관리자 인증 경계 구현

1. **`pydantic-settings` 설정 확충 ([config.py](../../../../backend/app/core/config.py))**
   - `ADMIN_TOKEN_SECRET` 추가 (미지정 시 `SECRET_KEY`를 서명 시크릿으로 보조 사용).

2. **서명 토큰 생성 및 검증 서비스 ([admin_access.py](../../../../backend/app/services/admin_access.py))**
   - `create_admin_session_token()`: HMAC-SHA256 기반 `admin.<expires_at>.<signature>` 생성.
   - `verify_admin_session_token()`: 서명 무결성(`hmac.compare_digest`) 및 만료시간(`time.time() > expires_at`) 검증.

3. **단계별 점진적 Rate Limit 락아웃 구현**
   - 5회 이상 실패 시 `[5, 10, 30, 60, 120, 300]` 초 순차 락아웃 적용.

### Slice A2 - 관리자 권한 경계 구현

1. **공통 관리자 권한 검증 Dependency ([deps.py](../../../../backend/app/api/deps.py))**
   - `get_current_admin_payload`: `Authorization: Bearer <token>` 헤더를 추출하여 서명 및 만료시간, 역할(`role == 'admin'`) 검증.
   - 토큰 누락/만료/변조 시 `HTTP 401 Unauthorized`, 권한 부족(`role != 'admin'`) 시 `HTTP 403 Forbidden` 반환.

2. **관리자 보호 라우트 샘플 ([admin_access.py](../../../../backend/app/api/v1/endpoints/admin_access.py))**
   - `GET /api/v1/admin/me`: `get_current_admin_payload` 의존성을 적용하여 라우터 보호 및 토큰 정보 조회 기능 제공.

## 주요 변경 파일

- `backend/app/api/deps.py`: 공통 관리자 권한 검증 Dependency (`get_current_admin_payload`) 구현
- `backend/app/api/v1/endpoints/admin_access.py`: `GET /api/v1/admin/me` 보호 라우트 추가 및 `get_current_admin_payload` 연동
- `backend/tests/test_admin_access_control.py`: Slice A2 보호 라우트 테스트 (401 헤더누락/토큰오류, 403 비관리자, 200 성공 및 dependency 누락 탐지 테스트) (19 passed)
- `docs/api/admin_access.md`: `GET /api/v1/admin/me` 및 401/403 계약 명세 추가
- `docs/development/develop_plan/backend/04_admin_access_control.md`: Slice A2 completed 갱신

## 설계 결정

1. **FastAPI Dependency 기반 공통 권한 제어**:
   - 개별 라우터 내부에서 토큰 검증 로직을 중복 구현하지 않고 `app/api/deps.py`의 `get_current_admin_payload` dependency로 분리하여 후속 Backend 05(CollectionRun Admin API)에서 즉시 재사용할 수 있도록 설계함.
2. **HTTP 401과 403의 명확한 경계 구분**:
   - 토큰 누락/변조/만료는 `401 Unauthorized`로, 토큰은 유효하나 관리자 권한이 없는 접근은 `403 Forbidden`으로 명확히 구분하여 디버깅 및 프론트엔드 처리 용이성을 보장함.
3. **보호 라우트 누락 탐지 테스트**:
   - 관리자 라우트 등록 시 `get_current_admin_payload` 의존성이 누락되어 관리자 기능이 실수로 공개되는 것을 방지하기 위해 파이썬 inspect 기반의 라우트 의존성 탐지 테스트를 추가함.

## 검증 결과

- **단위 및 통합 테스트**: `pytest backend/tests/test_admin_access_control.py` 실행
  - 19개 테스트 케이스 전원 통과 (Pass)
  - `test_protected_route_missing_token_401` (토큰 누락 401 반환 검증)
  - `test_protected_route_invalid_token_401` (변조 토큰 401 반환 검증)
  - `test_protected_route_non_admin_role_403` (비관리자 403 Forbidden 거부 검증)
  - `test_protected_route_valid_admin_token_200` (정상 토큰 200 OK 성공 검증)
  - `test_protected_route_dependency_leak_detection` (라우트 보호 dependency 누락 탐지 검증)
- **전체 백엔드 회귀 테스트**: `pytest backend/tests` 실행 -> **123 Passed, 15 Skipped**

## 남은 작업

- Slice A3: OpenAPI security scheme 명세 업데이트, README 가이드 및 문서 최종 검증

# Backend Admin Access Control Forest 개발 기록

## 작업 정보

- 기간: `2026-08-07`
- 담당 영역: Backend
- 상태: completed
- 브랜치: `feature/backend/admin-access-control`
- 선행 Forest: [Backend Policy Runtime Safety](policy_runtime_safety.md)
- 관련 계획: [Backend Admin Access Control Plan](../../develop_plan/backend/04_admin_access_control.md)
- 현재 Slice: Forest completed (`2026-08-07`)

## 목적

비밀번호(4자리 PIN) 기반 단일 관리자 세션 생성 및 접근 제어 기준선을 구축하기 위한 개발 기록이다. 로컬 개발 환경에서는 최초 PIN `0000`을 제공하되, 프로덕션 배포 환경에서는 명시적 해시/시크릿 미설정 시 자동 거부(fail-closed)하도록 보안 계약을 준수하며 점진적 락아웃(5, 10, 30, 60, 120, 300초) 및 공통 관리자 권한 검증 Dependency(`get_current_admin_payload`)를 완료했다.

## Forest 범위

- 아이디 없이 4자리 숫자 PIN만 받는 관리자 session endpoint (`POST /api/v1/admin/session`)
- `development`·localhost 전용 최초 PIN `0000` 경계
- 배포 환경의 관리자 PIN hash·서명 secret 필수 설정과 fail-closed
- 검증 성공 시 짧은 수명의 서명 관리자 token 발급 및 검증 서비스
- 실패 횟수 제한·단계별 점진적 락아웃 (5회 이상 실패 시 5초 ➔ 10초 ➔ 30초 ➔ 60초 ➔ 120초 ➔ 300초 순차 적용)
- 관리자 권한 판정 경계와 공통 FastAPI dependency (`get_current_admin_payload`)
- 인증 실패 `401`과 권한 부족 `403`, rate limit `429`, 파라미터 유효성 `422` 계약
- 비밀정보·credential의 설정·로그·오류 비노출 및 보호 라우트 누락 방지 테스트
- OpenAPI Bearer Security Scheme 표기 및 전체 백엔드 회귀 검증

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **A0** | **인증·권한 계약 결정 (Contract & Specification)** | **completed** | `POST /api/v1/admin/session` DTO, HTTP 401/403/429/422 상태코드 및 로컬 `0000` / production fail-closed 계약 구현 및 테스트 완료 |
| **A1** | **관리자 인증 경계 구현 (Admin Authentication Boundary)** | **completed** | PIN 해시 검증, HMAC-SHA256 세션 토큰 생성/검증 서비스(`create_admin_session_token`, `verify_admin_session_token`), 점진적 Rate Limit 락아웃(5->10->30->60->120->300초) 및 Credential 비노출 테스트 완료 |
| **A2** | **관리자 권한 경계 구현 (Admin Authorization Boundary)** | **completed** | 공통 관리자 권한 검증 FastAPI Dependency (`get_current_admin_payload`), `GET /api/v1/admin/me` 샘플 라우트, HTTP 401/403 구분 및 라우트 보호 누락 탐지 테스트 완료 |
| **A3** | **OpenAPI·회귀·문서 동기화 (OpenAPI, Regression & Docs Sync)** | **completed** | OpenAPI HTTPBearer Security Scheme 표기, `.env.example` 갱신, 백엔드 전체 회귀 테스트 통과(124 passed) 및 Forest 최종 마감 완료 |

## 구현 내용

### Slice A0 - 인증·권한 계약 결정

1. **관리자 세션 요청 및 응답 DTO ([admin_access.py](../../../../backend/app/schemas/admin_access.py))**
   - `AdminSessionCreate`: `pin` 4자리 숫자 Regex(`^\d{4}$`) 검증
   - `AdminSessionResponse`: `access_token`, `token_type`("bearer"), `expires_in`(초 단위), `role`("admin")

2. **환경별 PIN 인증 및 Fail-closed 로직 ([admin_access.py](../../../../backend/app/services/admin_access.py))**
   - 로컬/개발 환경(`development`, `local`, `test`)이고 요청 client가 loopback일 때만 `ADMIN_PIN_HASH` 미설정 시 `0000` 해시(`9af15b33...`)를 기본 사용.
   - 프로덕션 환경(`production`)에서 `ADMIN_PIN_HASH` 미설정 시 `None` 반환하여 fail-closed 처리.

3. **엔드포인트 및 라우터 등록 ([admin_access.py](../../../../backend/app/api/v1/endpoints/admin_access.py))**
   - `POST /api/v1/admin/session` 엔드포인트 구현 및 `api_router`에 `/admin` prefix로 포함.

### Slice A1 - 관리자 인증 경계 구현

1. **`pydantic-settings` 설정 확충 ([config.py](../../../../backend/app/core/config.py))**
   - `ADMIN_TOKEN_SECRET` 추가. `SECRET_KEY` 보조 사용은 local/test로 제한하고 production은 전용 secret 미설정 시 fail-closed 처리.

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

### Slice A3 - OpenAPI·회귀·문서 동기화

1. **FastAPI OpenAPI Security Scheme 등록 ([main.py](../../../../backend/app/main.py))**
   - `custom_openapi()`를 적용하여 OpenAPI JSON 및 Swagger UI(`/docs`)에 `HTTPBearer` securityScheme 등록.
2. **환경변수 가이드 문서화 ([.env.example](../../../../backend/.env.example))**
   - `ADMIN_PIN_HASH`, `ADMIN_TOKEN_SECRET`, `ADMIN_SESSION_EXPIRE_MINUTES` 관련 안내 추가.

## 주요 변경 파일

- `backend/app/main.py`: custom_openapi()를 통한 HTTPBearer Security Scheme 등록
- `backend/app/api/deps.py`: 공통 관리자 권한 검증 Dependency (`get_current_admin_payload`) 구현
- `backend/app/core/config.py`: ADMIN_TOKEN_SECRET 등 Pydantic Settings 추가
- `backend/app/services/admin_access.py`: PIN 해시 비교, fail-closed, HMAC 세션 토큰 생성/검증, 점진적 rate limit (5->10->30->60->120->300s)
- `backend/app/api/v1/endpoints/admin_access.py`: `POST /api/v1/admin/session` 및 `GET /api/v1/admin/me` 구현
- `backend/tests/test_admin_access_control.py`: 22개 관리자 접근 제어 단위/통합 테스트 (OpenAPI 등록 검증 포함)
- `backend/.env.example`: 관리자 PIN 및 토큰 관련 샘플 설정 추가
- `docs/api/admin_access.md`: 관리자 API 계약 전체 명세서 작성
- `docs/development/develop_plan/backend/04_admin_access_control.md`: Forest completed 갱신

## 설계 결정

1. **FastAPI Dependency 기반 공통 권한 제어**:
   - `app/api/deps.py`의 `get_current_admin_payload` dependency로 분리하여 후속 Backend 05(CollectionRun Admin API)에서 즉시 재사용할 수 있도록 함.
2. **점진적 락아웃 (Progressive Lockout)**:
   - 로그인 5회 연속 실패 시 바로 고정 300초 락아웃을 적용하지 않고 5초 ➔ 10초 ➔ 30초 ➔ 60초 ➔ 120초 ➔ 300초로 점진적으로 대기 시간을 증가시켜 브루트포스 대입 공격을 차단함.
3. **OpenAPI Security Scheme 명시**:
   - Swagger UI (`/docs`)에서 `Authorization: Bearer <token>` 헤더를 인터랙티브하게 시험할 수 있도록 OpenAPI 명세에 `HTTPBearer` 스키마를 동적으로 구성함.

## 검증 결과

### DTL4-5 보안 경계 재검토 (`2026-08-14`)

- 기본 `0000`은 환경 이름뿐 아니라 실제 loopback client 경계를 함께 만족해야
  동작하도록 보강했다. FastAPI `TestClient` 식별자는 test 환경에서만 허용한다.
- production은 `ADMIN_TOKEN_SECRET`이 없을 때 `SECRET_KEY`나 기본 문자열로
  fallback하지 않으며 로그인·token 검증 모두 닫힌다.
- `backend/tests/test_admin_access_control.py`: **22 passed**.

- **단위 및 통합 테스트**: `pytest backend/tests/test_admin_access_control.py` 실행
  - 기존 20개와 DTL4-5 경계 2개 테스트 전원 통과
  - `test_openapi_security_scheme_registered` (HTTPBearer 등록 검증)
  - `test_protected_route_valid_admin_token_200` (정상 토큰 200 OK 성공 검증)
  - `test_protected_route_non_admin_role_403` (비관리자 403 Forbidden 거부 검증)
  - `test_admin_session_progressive_rate_limit_429` (5회 실패 시 5초 락아웃 429 적용 검증)
- **전체 백엔드 회귀 테스트**: `pytest backend/tests` 실행 -> **124 Passed, 15 Skipped**
- **문서 무결성 검증**: `python scripts/validate_docs.py` 실행 -> **Pass**

## 남은 작업

- Backend 04 Forest 전체 완료. 후속 Forest인 **Backend 05 CollectionRun Admin API (`feature/backend/collection-run-admin-api`)** 진행 준비.

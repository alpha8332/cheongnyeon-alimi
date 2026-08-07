# Backend Admin Access Control Forest 개발 기록

## 작업 정보

- 기간: `2026-08-07`
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `feature/backend/admin-access-control`
- 선행 Forest: [Backend Policy Runtime Safety](policy_runtime_safety.md)
- 관련 계획: [Backend Admin Access Control Plan](../../develop_plan/backend/04_admin_access_control.md)
- 현재 Slice: A0 completed (`2026-08-07`)

## 목적

비밀번호(4자리 PIN) 기반 단일 관리자 세션 생성 및 접근 제어 기준선을 구축하기 위한 개발 기록이다. 로컬 개발 환경에서는 최초 PIN `0000`을 제공하되, 프로덕션 배포 환경에서는 명시적 해시/시크릿 미설정 시 자동 거부(fail-closed)하도록 보안 계약을 준수한다.

## Forest 범위

- 아이디 없이 4자리 숫자 PIN만 받는 관리자 session endpoint (`POST /api/v1/admin/session`)
- `development`·localhost 전용 최초 PIN `0000` 경계
- 배포 환경의 관리자 PIN hash·서명 secret 필수 설정과 fail-closed
- 검증 성공 시 짧은 수명의 서명 관리자 token 발급
- 실패 횟수 제한·cooldown과 반복 대입 방지
- 관리자 권한 판정 경계와 공통 FastAPI dependency
- 인증 실패 `401`과 권한 부족 `403`, rate limit `429`, 파라미터 유효성 `422` 계약
- 비밀정보·credential의 설정·로그·오류 비노출

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **A0** | **인증·권한 계약 결정 (Contract & Specification)** | **completed** | `POST /api/v1/admin/session` DTO, HTTP 401/403/429/422 상태코드 및 로컬 `0000` / production fail-closed 계약 구현 및 테스트 완료 |
| **A1** | 관리자 인증 경계 구현 | in-progress | PIN 해시 검증, 세션 토큰 생성 서비스 및 Rate Limit 락아웃 검증 |
| **A2** | 관리자 권한 경계 구현 | draft | FastAPI 관리자 권한 검증 Dependency 구현 예정 |
| **A3** | OpenAPI·회귀·문서 동기화 | draft | 보안 정의 명세 및 README/env 가이드 작성 예정 |

## 구현 내용

### Slice A0 - 인증·권한 계약 결정

1. **관리자 세션 요청 및 응답 DTO ([admin_access.py](../../../../backend/app/schemas/admin_access.py))**
   - `AdminSessionCreate`: `pin` 4자리 숫자 Regex(`^\d{4}$`) 검증
   - `AdminSessionResponse`: `access_token`, `token_type`("bearer"), `expires_in`(초 단위), `role`("admin")

2. **환경별 PIN 인증 및 Fail-closed 로직 ([admin_access.py](../../../../backend/app/services/admin_access.py))**
   - 로컬/개발 환경(`development`, `local`, `test`)에서 `ADMIN_PIN_HASH` 미설정 시 `0000` 해시(`9af15b33...`)를 기본 사용.
   - 프로덕션 환경(`production`)에서 `ADMIN_PIN_HASH` 미설정 시 `None` 반환하여 fail-closed 처리.
   - 5회 이상 로그인 실패 시 IP 기준 락아웃(300초 Cooldown) 및 `429 Too Many Requests` 반환.

3. **엔드포인트 및 라우터 등록 ([admin_access.py](../../../../backend/app/api/v1/endpoints/admin_access.py))**
   - `POST /api/v1/admin/session` 엔드포인트 구현 및 `api_router`에 `/admin` prefix로 포함.

## 주요 변경 파일

- `backend/app/schemas/admin_access.py`: AdminSessionCreate, AdminSessionResponse DTO 정의
- `backend/app/core/config.py`: ADMIN_PIN_HASH, ADMIN_SESSION_EXPIRE_MINUTES 등 설정 추가
- `backend/app/services/admin_access.py`: verify_admin_pin, fail-closed 규칙 및 rate limiting 서비스 구현
- `backend/app/api/v1/endpoints/admin_access.py`: `POST /api/v1/admin/session` 엔드포인트 구현
- `backend/app/api/v1/api.py`: admin_access 라우터 등록
- `backend/tests/test_admin_access_control.py`: Slice A0 단위/통합 테스트 (10 passed)
- `docs/api/admin_access.md`: 관리자 인증 API 계약 명세 문서 작성

## 설계 결정

1. **단일 PIN 및 비밀번호-only 식별**:
   - 관리자 아이디 입력 없이 4자리 숫자 PIN만으로 세션을 발급하여 관리자 접근을 단순화함.
2. **Fail-closed 보안 원칙**:
   - 프로덕션 환경에서 `ADMIN_PIN_HASH` 미설정 시 `0000` 기본값을 인가하지 않고 모든 요청을 `401 Unauthorized`로 거부하도록 구현함.
3. **오류 메시지 최소화**:
   - 보안 유출을 방지하기 위해 PIN 불일치 및 authentication disabled 사유를 구분하지 않고 `401 Unauthorized`로 캡슐화함.

## 검증 결과

- **단위 및 통합 테스트**: `pytest backend/tests/test_admin_access_control.py` 실행
  - 10개 테스트 케이스 전원 통과 (Pass)
  - `test_admin_session_success_local_default_pin` (개발 환경 0000 성공)
  - `test_admin_session_invalid_pin_401` (잘못된 PIN 401 거부)
  - `test_admin_session_invalid_format_422` (4자리 미만/초과/문자 422 거부)
  - `test_admin_session_production_fail_closed` (프로덕션 0000 401 거부)
  - `test_admin_session_custom_hash_success` (커스텀 PIN 해시 성공)
  - `test_admin_session_rate_limit_429` (5회 실패 시 429 락아웃 적용)
- **전체 백엔드 회귀 테스트**: `pytest backend/tests` 실행 -> **114 Passed, 15 Skipped**

## 남은 작업

- Slice A1: 관리자 인증 경계 및 토큰 검증 미들웨어/의존성 고도화
- Slice A2: 라우터별 관리자 권한 보호 dependency (`require_admin_role`) 및 `403` 검증
- Slice A3: OpenAPI security scheme 명세 업데이트, README 가이드 및 문서 최종 검증

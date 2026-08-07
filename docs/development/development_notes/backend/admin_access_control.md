# Backend Admin Access Control Forest 개발 기록

## 작업 정보

- 기간: `2026-08-07`
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `feature/backend/admin-access-control`
- 선행 Forest: [Backend Policy Runtime Safety](policy_runtime_safety.md)
- 관련 계획: [Backend Admin Access Control Plan](../../develop_plan/backend/04_admin_access_control.md)
- 현재 Slice: A1 completed (`2026-08-07`)

## 목적

비밀번호(4자리 PIN) 기반 단일 관리자 세션 생성 및 접근 제어 기준선을 구축하기 위한 개발 기록이다. 로컬 개발 환경에서는 최초 PIN `0000`을 제공하되, 프로덕션 배포 환경에서는 명시적 해시/시크릿 미설정 시 자동 거부(fail-closed)하도록 보안 계약을 준수하며 점진적 락아웃(5, 10, 30, 60, 120, 300초)을 지원한다.

## Forest 범위

- 아이디 없이 4자리 숫자 PIN만 받는 관리자 session endpoint (`POST /api/v1/admin/session`)
- `development`·localhost 전용 최초 PIN `0000` 경계
- 배포 환경의 관리자 PIN hash·서명 secret 필수 설정과 fail-closed
- 검증 성공 시 짧은 수명의 서명 관리자 token 발급 및 검증 서비스
- 실패 횟수 제한·단계별 점진적 락아웃 (5회 이상 실패 시 5초 ➔ 10초 ➔ 30초 ➔ 60초 ➔ 120초 ➔ 300초 순차 적용)
- 관리자 권한 판정 경계와 공통 FastAPI dependency
- 인증 실패 `401`과 권한 부족 `403`, rate limit `429`, 파라미터 유효성 `422` 계약
- 비밀정보·credential의 설정·로그·오류 비노출

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **A0** | **인증·권한 계약 결정 (Contract & Specification)** | **completed** | `POST /api/v1/admin/session` DTO, HTTP 401/403/429/422 상태코드 및 로컬 `0000` / production fail-closed 계약 구현 및 테스트 완료 |
| **A1** | **관리자 인증 경계 구현 (Admin Authentication Boundary)** | **completed** | PIN 해시 검증, HMAC-SHA256 세션 토큰 생성/검증 서비스(`create_admin_session_token`, `verify_admin_session_token`), 점진적 Rate Limit 락아웃(5->10->30->60->120->300초) 및 Credential 비노출 테스트 완료 (14 passed) |
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

4. **Credential 비노출 가드**
   - 예외 및 응답 메시지에 원문 PIN과 Secret이 절대 노출되지 않도록 가드 보장.

## 주요 변경 파일

- `backend/app/core/config.py`: ADMIN_TOKEN_SECRET 설정 추가
- `backend/app/services/admin_access.py`: HMAC 토큰 생성/검증 서비스 구현 및 점진적 락아웃 (5->10->30->60->120->300초)
- `backend/app/api/v1/endpoints/admin_access.py`: 엔드포인트 토큰 발급 및 점진적 cooldown 응답 연동
- `backend/tests/test_admin_access_control.py`: 점진적 락아웃 계단 검증 및 서명 토큰 검증, Credential 비노출 테스트 (14 passed)
- `docs/api/admin_access.md`: 토큰 인증 구조 및 점진적 락아웃 명세 보완
- `docs/development/develop_plan/backend/04_admin_access_control.md`: Slice A1 completed 갱신

## 설계 결정

1. **점진적 락아웃 단계 (Progressive Lockout)**:
   - 로그인 5회 연속 실패 시 바로 고정 300초 락아웃을 적용하지 않고 5초 ➔ 10초 ➔ 30초 ➔ 60초 ➔ 120초 ➔ 300초로 점진적으로 대기 시간을 증가시켜 사용자 편의성과 Brute-force 대입 방지를 모두 충족함.
2. **HMAC-SHA256 기반 경량 세션 토큰**:
   - 별도 데이터베이스 테이블 저장 없이 서버 시크릿으로 검증 가능한 `admin.<expires_at>.<sig>` 타임스탬프 서명 구조를 채택함.

## 검증 결과

- **단위 및 통합 테스트**: `pytest backend/tests/test_admin_access_control.py` 실행
  - 14개 테스트 케이스 전원 통과 (Pass)
  - `test_progressive_lockout_calculation` (5, 10, 30, 60, 120, 300초 계단 계산 검증)
  - `test_admin_session_progressive_rate_limit_429` (5회 실패 시 5초 락아웃 429 적용 검증)
  - `test_admin_session_success_local_default_pin` (개발 환경 0000 성공)
  - `test_admin_token_verification_cases` (서명 토큰 검증, 만료 -5분 검증, 변조 서명 탐지)
- **전체 백엔드 회귀 테스트**: `pytest backend/tests` 실행 -> **118 Passed, 15 Skipped**

## 남은 작업

- Slice A2: 라우터별 관리자 권한 보호 dependency (`require_admin_role`) 및 `403` 검증
- Slice A3: OpenAPI security scheme 명세 업데이트, README 가이드 및 문서 최종 검증

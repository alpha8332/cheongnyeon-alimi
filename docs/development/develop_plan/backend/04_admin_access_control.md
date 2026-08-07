# Backend Admin Access Control Forest 개발 계획

## 계획 정보

- 번호: Backend 04
- 담당 영역: Backend
- 상태: in-progress
- 작업 브랜치: `feature/backend/admin-access-control`
- 공통 선행 계약:
  [Integration 05 v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- 공유 Forest:
  [CollectionRun Admin API](05_collection_run_admin_api.md),
  [Frontend CollectionRun Admin UI](../frontend/03_collection_run_admin_ui.md)
- 선행 Forest:
  [Backend Policy Runtime Safety](03_policy_runtime_safety.md),
  [Integration 05 v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- 후속 Forest:
  [CollectionRun Admin API](05_collection_run_admin_api.md)

## 목적

현재 인증·권한 기반이 없는 Backend에 비밀번호만 입력하는 단일 관리자
접근 제어 기준선을 마련한다. 로컬 개발 최초 PIN은 `0000`으로 시작하되
외부 배포 기본값으로 사용하지 않고, 인증 실패와 권한 부족 및 보호 endpoint
우회를 자동 테스트로 검증한다.

## 범위

- 아이디 없는 4자리 숫자 PIN만 받는 관리자 session endpoint
- `development`·localhost 전용 최초 PIN `0000` 경계
- 배포 환경의 관리자 PIN hash·서명 secret 필수 설정과 fail-closed
- 검증 성공 시 짧은 수명의 서명 관리자 token 발급
- 실패 횟수 제한·cooldown과 반복 대입 방지
- 관리자 권한 판정 경계와 공통 FastAPI dependency
- 인증 실패 `401`과 권한 부족 `403` 계약
- 테스트용 관리자·비관리자 identity 주입 경계
- PIN hash 생성 helper와 `.env` 설정·교체·전체 token 폐기 절차
- 비밀정보·credential의 설정·로그·오류 비노출
- OpenAPI 보안 정의와 Backend 보안 문서

## 범위 밖

- CollectionRun 목록·상세·수동 실행 API
- Frontend 로그인·관리자 화면
- 관리자 PIN 변경 화면과 다중 관리자 계정
- 일반 사용자 계정·프로필·소셜 로그인 전체 기능
- 외부 identity provider 운영과 production 배포 자동화

## 선행 조건

- 관리자 기능의 운영 주체와 최소 권한을 합의한다.
- 최초 `0000`은 `development`와 localhost에서만 허용하고 외부 bind 또는
  production 환경에서는 명시적 PIN hash가 없으면 관리자 인증을 활성화하지
  않는다.
- `.env.example`에는 안전한 placeholder만 기록한다.

## 공통 설계 원칙

- 기본적으로 관리자 endpoint 접근을 거부한다.
- PIN 원문은 DB·파일·로그·오류·token payload에 저장하지 않는다.
- 저장소에는 `0000`의 재사용 가능한 hash나 실제 token secret을 커밋하지 않는다.
- PIN은 정확히 숫자 4자리로 검증하되 반복 실패에는 동일한 오류와 rate limit을
  적용한다.
- 인증과 권한 판정을 route마다 복제하지 않고 공통 dependency로 제공한다.
- `401`과 `403`의 의미와 응답 계약을 구분한다.
- 로그·예외·OpenAPI 예시에 실제 credential을 포함하지 않는다.
- 테스트 편의를 위한 우회 설정이 production 기본값이 되지 않도록 한다.

## Slice 계획

### A0 - 인증·권한 계약 결정

- 상태: completed
- 목적:
  비밀번호-only 단일 관리자 identity, 4자리 PIN과 role 판정 경계를 확정한다.
- 산출물:
  - `POST /admin/session` PIN 요청·token 응답과 관리자 권한 계약
  - 최초 `0000` 허용 환경, hash·secret 설정과 `401`·`403`·`429` 오류 기준
- 선행 조건:
  - 운영·보안 요구 확인
- 완료 기준:
  - 구현 가능한 최소 계약과 범위 밖 항목 합의

### A1 - 관리자 인증 경계 구현

- 상태: completed
- 목적:
  Backend가 PIN hash를 검증하고 단일 관리자 주체를 안전하게 식별하게 한다.
- 산출물:
  - PIN hash·token secret 설정, 검증 service와 session endpoint
  - 짧은 수명 token과 FastAPI dependency
  - 인증 성공·실패·rate-limit 테스트
- 선행 조건:
  - A0 완료
- 완료 기준:
  - 누락·형식 오류·잘못된 PIN은 외부에서 구분되지 않는 `401`
  - 반복 실패는 비밀을 노출하지 않는 `429`와 cooldown
  - production에서 기본 `0000` 또는 설정 누락은 fail-closed
  - credential 비노출 테스트 통과

### A2 - 관리자 권한 경계 구현

- 상태: completed
- 목적:
  인증된 비관리자의 관리자 API 접근을 차단한다.
- 산출물:
  - 관리자 권한 dependency와 우회 방지 테스트
- 선행 조건:
  - A1 완료
- 완료 기준:
  - 비관리자 접근은 `403`
  - 보호 dependency 누락을 탐지하는 route 테스트 존재

### A3 - OpenAPI·회귀·문서 동기화

- 상태: draft
- 목적:
  보안 계약과 실제 Backend 동작을 일치시키고 후속 API가 사용할 기준선을
  확정한다.
- 산출물:
  - OpenAPI 보안 정의와 Backend 개발 기록
  - `.env.example`의 안전한 placeholder와 README PIN hash 생성·설정·교체 방법
  - 전체 Backend 회귀 결과
- 선행 조건:
  - A1·A2 완료
- 완료 기준:
  - 인증·권한·비노출 테스트와 전체 Backend 회귀 통과
  - README에 실제 PIN·hash·secret 없이 최초 로컬 `0000`, 배포 설정과 교체
    절차가 재현 가능하게 기록됨
  - `python scripts/validate_docs.py` 통과

## 검증 계획

- credential 누락·오류·정상 인증 테스트
- 4자리 숫자 형식, 개발 localhost `0000`과 production 거부 테스트
- 반복 실패 rate limit·cooldown과 성공 후 초기화 테스트
- token 만료·서명 오류·로그아웃 후 Frontend 폐기 테스트
- 관리자·비관리자 권한 테스트
- route 보호 dependency 누락 회귀 테스트
- 오류·로그·OpenAPI의 credential 비노출 검사
- Backend 전체 테스트
- `python scripts/validate_docs.py`
- `git diff --check`

## Forest 완료 기준

- 공통 관리자 인증·권한 dependency 제공
- 아이디 없는 4자리 PIN 로그인과 짧은 수명 관리자 token 제공
- 최초 `0000`은 development·localhost에만 한정되고 배포 설정 누락은 fail-closed
- `401`·`403` 계약과 OpenAPI 일치
- 권한 우회와 credential 노출 0건
- 후속 CollectionRun 관리자 API가 재사용할 테스트 가능한 기준선 제공
- 관련 기준 문서와 개발 기록 동기화
- README·`.env.example`에 실제 secret 없이 관리자 PIN 설정 방법 제공

## 위험과 미확정 사항

- 4자리 PIN은 가능한 값이 10,000개뿐이므로 외부 공개 인증에는 충분히 강하지
  않다. 현재 결정은 로컬·시연 편의를 위한 것이며 배포 노출 경계와 rate limit을
  함께 강제해야 한다.
- 장기 production identity provider와 다중 관리자 계정은 아직 결정되지 않았다.
- 수동 실행 API는 권한 외에도 CSRF·재실행·감사 경계를 추가로 요구할 수
  있다.

## 관련 문서

- [역할과 책임](../../../governance/role_assignment.md)
- [Policy API 계약](../../../api/policies.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [후속 CollectionRun Admin API 계획](05_collection_run_admin_api.md)

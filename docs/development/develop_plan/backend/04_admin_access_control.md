# Backend Admin Access Control Forest 개발 계획

## 계획 정보

- 번호: Backend 04
- 담당 영역: Backend
- 상태: draft
- 작업 브랜치: `feature/backend/admin-run-management`
- 공유 Forest:
  [CollectionRun Admin API](05_collection_run_admin_api.md),
  [Frontend CollectionRun Admin UI](../frontend/03_collection_run_admin_ui.md)
- 선행 Forest:
  [Backend Policy Runtime Safety](03_policy_runtime_safety.md)
- 후속 Forest:
  [CollectionRun Admin API](05_collection_run_admin_api.md)

## 목적

현재 인증·권한 기반이 없는 Backend에 관리자 API가 공통으로 사용할 최소
접근 제어 기준선을 마련한다. 인증 실패와 권한 부족을 구분하고, 보호된
endpoint가 우회되지 않음을 자동 테스트로 검증한다.

## 범위

- 관리자 API를 위한 인증 주체와 credential 전달 방식 결정
- 관리자 권한 판정 경계와 공통 FastAPI dependency
- 인증 실패 `401`과 권한 부족 `403` 계약
- 테스트용 관리자·비관리자 identity 주입 경계
- 비밀정보·credential의 설정·로그·오류 비노출
- OpenAPI 보안 정의와 Backend 보안 문서

## 범위 밖

- CollectionRun 목록·상세·수동 실행 API
- Frontend 로그인·관리자 화면
- 일반 사용자 계정·프로필·소셜 로그인 전체 기능
- 외부 identity provider 운영과 production 배포 자동화

## 선행 조건

- 관리자 기능의 운영 주체와 최소 권한을 합의한다.
- credential 저장·전달 방식이 정해지지 않으면 임의의 고정 관리자 키를
  구현하지 않는다.
- `.env.example`에는 안전한 placeholder만 기록한다.

## 공통 설계 원칙

- 기본적으로 관리자 endpoint 접근을 거부한다.
- 인증과 권한 판정을 route마다 복제하지 않고 공통 dependency로 제공한다.
- `401`과 `403`의 의미와 응답 계약을 구분한다.
- 로그·예외·OpenAPI 예시에 실제 credential을 포함하지 않는다.
- 테스트 편의를 위한 우회 설정이 production 기본값이 되지 않도록 한다.

## Slice 계획

### A0 - 인증·권한 계약 결정

- 상태: draft
- 목적:
  관리자 identity, credential와 role 판정 경계를 확정한다.
- 산출물:
  - 인증 방식과 관리자 권한 계약
  - `401`·`403` 오류 기준
- 선행 조건:
  - 운영·보안 요구 확인
- 완료 기준:
  - 구현 가능한 최소 계약과 범위 밖 항목 합의

### A1 - 관리자 인증 경계 구현

- 상태: draft
- 목적:
  Backend가 credential을 검증하고 인증 주체를 안전하게 식별하게 한다.
- 산출물:
  - 설정·검증 서비스와 FastAPI dependency
  - 인증 성공·실패 테스트
- 선행 조건:
  - A0 완료
- 완료 기준:
  - 누락·잘못된 credential은 `401`
  - credential 비노출 테스트 통과

### A2 - 관리자 권한 경계 구현

- 상태: draft
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
  - 전체 Backend 회귀 결과
- 선행 조건:
  - A1·A2 완료
- 완료 기준:
  - 인증·권한·비노출 테스트와 전체 Backend 회귀 통과
  - `python scripts/validate_docs.py` 통과

## 검증 계획

- credential 누락·오류·정상 인증 테스트
- 관리자·비관리자 권한 테스트
- route 보호 dependency 누락 회귀 테스트
- 오류·로그·OpenAPI의 credential 비노출 검사
- Backend 전체 테스트
- `python scripts/validate_docs.py`
- `git diff --check`

## Forest 완료 기준

- 공통 관리자 인증·권한 dependency 제공
- `401`·`403` 계약과 OpenAPI 일치
- 권한 우회와 credential 노출 0건
- 후속 CollectionRun 관리자 API가 재사용할 테스트 가능한 기준선 제공
- 관련 기준 문서와 개발 기록 동기화

## 위험과 미확정 사항

- production identity provider와 배포 방식은 아직 결정되지 않았다.
- 임시 관리자 credential 방식은 장기 사용자 인증 구조와 충돌할 수 있다.
- 수동 실행 API는 권한 외에도 CSRF·재실행·감사 경계를 추가로 요구할 수
  있다.

## 관련 문서

- [역할과 책임](../../../governance/role_assignment.md)
- [Policy API 계약](../../../api/policies.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [후속 CollectionRun Admin API 계획](05_collection_run_admin_api.md)

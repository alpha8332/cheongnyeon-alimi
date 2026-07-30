# Frontend CollectionRun Admin UI Forest 개발 계획

## 계획 정보

- 번호: Frontend 03
- 담당 영역: Frontend
- 상태: draft
- 권장 브랜치: `feature/frontend/collection-run-admin-ui`
- 선행 Forest:
  [Backend Admin Access Control](../backend/04_admin_access_control.md),
  [Backend CollectionRun Admin API](../backend/05_collection_run_admin_api.md)
- 대상 인계사항: `BE-ADMIN-RUN-HISTORY`의 Frontend 소비

## 목적

인증된 관리자가 CollectionRun 실행 이력을 조회하고 안전하게 수동 실행을
요청할 수 있는 관리자 UI를 구현한다. Backend DTO·pagination·권한·상태
계약을 그대로 소비하고 loading·empty·error·동시 실행 상태를 명확히
표시한다.

## 범위

- 관리자 실행 이력 목록·상세 route와 API Client
- pagination, source·status·기간 필터와 기본 정렬 소비
- 상태·집계·안전한 오류 정보 표시
- loading·empty·error·401·403·404 UI
- 수동 실행 확인, 진행 중 비활성화와 중복 제출 방지
- stale·중단 실행 표시
- Backend DTO 소비 테스트, lint·build와 실제 브라우저 검증

## 범위 밖

- 관리자 인증·권한 Backend 구현
- CollectionRun DB·Backend API 계약 변경
- Raw payload·정책 본문·provenance·credential 표시
- Scheduler·실시간 WebSocket·알림 시스템
- 디자이너급 관리자 디자인 시스템 전면 구축

## 선행 조건

- Backend Admin Access Control과 CollectionRun Admin API Forest 완료
- 실제 OpenAPI·DTO·pagination·오류 계약 제공
- Frontend에서 관리자 인증 상태를 소비할 경계 합의
- Mock을 사용하면 실제 API와 동일한 공개 관리자 DTO만 사용

## 공통 설계 원칙

- 관리자 route는 인증·권한 상태를 명시적으로 처리한다.
- API DTO에 없는 내부 DB·provenance 필드를 화면 타입에 추가하지 않는다.
- 수동 실행은 명시적인 사용자 확인과 중복 제출 방지를 요구한다.
- `running`, terminal, stale 상태를 임의로 합치지 않는다.
- 오류에는 Backend가 제공한 안전한 정보만 표시한다.
- Mock·실제 API Client와 소비 테스트가 같은 계약을 사용한다.

## Slice 계획

### U0 - 관리자 DTO·라우팅 소비 계약

- 상태: draft
- 목적:
  Backend OpenAPI를 기준으로 TypeScript DTO와 route·권한 경계를 확정한다.
- 산출물:
  - DTO·API Client·route·Mock 계약
- 선행 조건:
  - Backend CollectionRun Admin API 완료
- 완료 기준:
  - 목록·상세·pagination·오류·권한 계약이 OpenAPI와 일치

### U1 - 실행 이력 목록·상세 UI

- 상태: draft
- 목적:
  관리자 실행 이력의 검색·목록·상세 상태를 구현한다.
- 산출물:
  - 목록·상세·필터·pagination 화면
  - loading·empty·error·권한 상태 컴포넌트
- 선행 조건:
  - U0 완료
- 완료 기준:
  - 상태·집계·stale·안전 오류 정보 표시
  - 내부·민감 필드 비노출

### U2 - 수동 실행 상호작용

- 상태: draft
- 목적:
  확인 가능한 중복 방지 수동 실행 UI를 구현한다.
- 산출물:
  - 실행 확인·요청·진행·성공·실패 상태
  - 중복 클릭·재제출 방지 테스트
- 선행 조건:
  - U1 완료
- 완료 기준:
  - 실행 중 중복 제출 불가
  - Backend가 반환한 CollectionRun 결과로 화면 갱신
  - `401`·`403`·validation·충돌 오류 표시

### U3 - 실제 API·브라우저 검증과 인계 종료

- 상태: draft
- 목적:
  실제 Backend·PostgreSQL 경로에서 관리자 UI 소비를 확인한다.
- 산출물:
  - 자동 소비 테스트와 실제 브라우저 증거
  - Frontend 개발 기록과 인계 보드 갱신
- 선행 조건:
  - U1·U2 완료
- 완료 기준:
  - `npm ci`, 소비 테스트, lint와 build 통과
  - 실제 API 목록·상세·수동 실행 브라우저 검증
  - 권한과 민감정보 비노출 확인
  - `python scripts/validate_docs.py` 통과
  - `BE-ADMIN-RUN-HISTORY` 종료

## 검증 계획

- DTO·Mock·API Client 소비 테스트
- pagination·filter·status 표시 테스트
- loading·empty·error·401·403·404 UI 테스트
- 수동 실행 확인·중복 제출 방지 테스트
- `npm ci`
- `npm test`
- `npm run lint`
- `npm run build`
- 실제 Backend·PostgreSQL 기반 브라우저 검증
- `python scripts/validate_docs.py`
- `git diff --check`

## Forest 완료 기준

- 관리자 실행 이력 목록·상세·필터·pagination 제공
- 수동 실행 확인과 중복 제출 방지
- Backend DTO·권한·상태 계약과 Frontend 타입 일치
- 민감정보·내부 provenance 비노출
- 자동 검증과 실제 API 브라우저 검증 통과
- 개발 기록·인계 보드 동기화

## 위험과 미확정 사항

- 관리자 인증 UX와 credential 보관 방식은 Backend Access Control 결정에
  의존한다.
- 수동 실행이 장시간 작업이면 polling·timeout·재접속 상태가 추가로 필요할
  수 있다.
- Backend API가 확정되기 전에 Mock을 일반화하면 계약 불일치가 생길 수 있다.

## 관련 문서

- [Backend Admin Access Control 계획](../backend/04_admin_access_control.md)
- [Backend CollectionRun Admin API 계획](../backend/05_collection_run_admin_api.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [공동 확인 및 인계 보드](../../../index.md#공동-확인-및-인계-보드)

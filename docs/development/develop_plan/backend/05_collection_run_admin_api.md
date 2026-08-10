# Backend CollectionRun Admin API Forest 개발 계획

## 계획 정보

- 번호: Backend 05
- 담당 영역: Backend
- 상태: draft
- 작업 브랜치: `feature/backend/admin-run-management`
- 공통 선행 계약:
  [Integration 05 v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- 공유 Forest:
  [Backend Admin Access Control](04_admin_access_control.md),
  [Frontend CollectionRun Admin UI](../frontend/03_collection_run_admin_ui.md)
- 선행 Forest:
  [Backend Admin Access Control](04_admin_access_control.md)
- 후속 Forest:
  [Frontend CollectionRun Admin UI](../frontend/03_collection_run_admin_ui.md)
- 대상 인계사항: `BE-ADMIN-RUN-HISTORY`

## 목적

기존 `CollectionRun` DB 계약과 관리자 접근 제어 기준선 위에 실행 이력
목록·상세와 안전한 수동 실행 API를 제공한다. pagination, 상태·집계,
중단된 `running` 판정, 중복 실행과 권한 경계를 Backend 계약으로 확정한다.

## 범위

- 관리자 전용 CollectionRun 목록·상세 DTO와 endpoint
- pagination, source·status·기간 필터와 기본 정렬
- 안전한 집계·오류 정보만 노출하는 API 경계
- 오래 지속된 `running` 실행의 stale·중단 판정 규칙
- 수동 실행 요청, 중복·동시 실행 방지와 결과 연결
- 인증·권한·오류·PostgreSQL 통합 테스트
- OpenAPI·운영·CollectionRun 기준 문서 동기화

## 범위 밖

- 관리자 인증 방식 자체의 구현
- Frontend 관리자 화면과 사용자 알림
- Scheduler·분산 queue·worker 플랫폼 전면 도입
- Raw payload, 정책 본문, provenance와 credential 노출
- CollectionRun 이외의 범용 감사 로그

## 선행 조건

- Backend Admin Access Control Forest 완료
- 현재 `CollectionRunWriter`와 Migration 계약 검토
- 수동 실행 대상, 실행 주체와 허용 source 합의
- 동시 실행·stale 판정 정책을 구현 전에 확정

## 공통 설계 원칙

- 모든 endpoint는 관리자 접근 제어 dependency를 요구한다.
- 응답에는 안전한 상태·집계·분류된 오류만 포함한다.
- 목록은 안정적인 정렬과 pagination을 제공한다.
- 수동 실행 요청은 중복 클릭·재전송·동시 실행에 안전해야 한다.
- `running`을 임의로 성공 또는 실패로 바꾸지 않고 판정 근거를 보존한다.
- DB transaction과 실제 collection/import 실행의 실패 경계를 구분한다.

## Slice 계획

### C0 - 관리자 API·상태 계약 확정

- 상태: completed
- 목적:
  목록·상세·수동 실행과 stale 판정의 API 계약을 정의한다.
- 산출물:
  - DTO·endpoint·pagination·오류 초안
  - stale·중복 실행 결정
- 선행 조건:
  - Admin Access Control 완료
- 완료 기준:
  - Backend·Frontend 소비 가능 계약과 보안 경계 합의

### C1 - 실행 이력 목록·상세 구현

- 상태: draft
- 목적:
  관리자에게 안전한 CollectionRun 조회 기능을 제공한다.
- 산출물:
  - Repository·Service·목록·상세 endpoint
  - 필터·정렬·pagination 테스트
- 선행 조건:
  - C0 완료
- 완료 기준:
  - 관리자만 목록·상세 조회 가능
  - 상태·집계·오류 정보가 DB 계약과 일치
  - raw·credential·민감 parameter 비노출

### C2 - 수동 실행과 stale 판정 구현

- 상태: draft
- 목적:
  중복·동시 실행에 안전한 관리자 수동 실행 경계를 제공한다.
- 산출물:
  - 수동 실행 Service·endpoint
  - idempotency·동시 실행·stale 판정 테스트
- 선행 조건:
  - C1 완료
- 완료 기준:
  - 중복 요청이 중복 작업을 만들지 않음
  - 실행 결과가 CollectionRun과 연결됨
  - 실패가 안전한 상태·오류 정보로 기록됨

### C3 - PostgreSQL·권한·문서 통합 검증

- 상태: draft
- 목적:
  실제 PostgreSQL과 관리자 권한 경계에서 전체 기능을 검증한다.
- 산출물:
  - 실제 DB·API 통합 결과와 개발 기록
  - API·Architecture·Operations 문서
- 선행 조건:
  - C1·C2 완료
- 완료 기준:
  - 실제 PostgreSQL 목록·상세·수동 실행 회귀 통과
  - `401`·`403`·`404`·validation·동시 실행 테스트 통과
  - Frontend 인계 계약 기록
  - `python scripts/validate_docs.py` 통과

## 검증 계획

- CollectionRun Repository·Service 단위 테스트
- 관리자 권한과 오류 API 테스트
- pagination·filter·stable ordering 테스트
- 수동 실행 idempotency·동시 실행·실패 회귀
- 실제 PostgreSQL Migration·조회·실행 통합 테스트
- Backend 전체 회귀
- `python scripts/validate_docs.py`
- `git diff --check`

## Forest 완료 기준

- 인증된 관리자 목록·상세·수동 실행 API 제공
- pagination·상태·집계·stale·중복 실행 계약 확정
- 권한 우회와 민감정보 노출 0건
- 실제 PostgreSQL과 Backend 전체 회귀 통과
- OpenAPI·DB·운영 문서와 개발 기록 동기화
- Frontend Admin UI가 소비할 계약 인계

## 위험과 미확정 사항

- 실행이 process 내부 동기 호출인지 별도 worker인지 아직 확정되지 않았다.
- stale 판정은 배포 topology와 heartbeat 제공 여부에 영향을 받는다.
- 수동 실행의 idempotency key 저장 경계가 새 DB 필드를 요구할 수 있다.
- DB 계약 변경 시 Migration과 Backend·Frontend DTO를 함께 검토해야 한다.

## 관련 문서

- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [Backend Admin Access Control 계획](04_admin_access_control.md)
- [Integration 개발 기록](../../development_notes/integration/policy_data_database_integration.md)
- [Frontend CollectionRun Admin UI 계획](../frontend/03_collection_run_admin_ui.md)

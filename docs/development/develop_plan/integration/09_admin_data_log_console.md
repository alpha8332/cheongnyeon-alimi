# Integration 09 Admin Data and Log Console Forest 개발 계획

## 계획 정보

- 번호: Integration 09
- 담당 영역: Backend·Frontend
- 상태: draft
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 선행 Forest: Backend 04 Admin Access Control, Integration 05 Contract Baseline
- 연계 Forest: Backend 05 CollectionRun Admin API, Frontend 03 Admin UI
- 후속 Forest: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/backend/admin-observability`,
  `feature/frontend/admin-observability`

## 목적

인증된 관리자가 PostgreSQL에 적재된 정책 데이터를 CSV처럼 안전하게 살펴보고,
수집·API·DB 처리 중 발생한 로그를 파일로 보존해 화면에서 검색·확인·정리할 수
있게 한다. 운영 상태를 확인하기 위해 터미널과 DB 도구에만 의존하지 않는 최소
관리자 진단 기준선을 제공한다.

## 범위

### 정책 데이터 탐색

- 승인된 Policy projection의 읽기 전용 표 형식 조회
- 서버 pagination, allowlist 기반 정렬·필터와 전체 건수
- 컬럼 표시·숨김, 긴 값 펼치기와 단일 row 상세
- 정책 identity, Source, 상태, 기간, 지역·연령·자격요건·품질·수집 시각 표시
- loading·empty·error·partial과 실제 PostgreSQL Browser 검증

### 영속 로그와 관리자 진단

- 현재 stdout 로그를 유지하면서 UTF-8 구조화 파일 로그 추가
- 날짜 또는 크기 기반 rotation, 보존 기간·파일 수·용량 상한
- `timestamp`, `level`, `component`, `event`, `request_id`,
  `collection_run_id`, `source_id`, `duration_ms`, 안전한 오류 유형
- API 요청, 수집 단계, 정규화·검증·DB 적재와 관리자 작업 correlation
- 컴포넌트별 로그 level 설정과 기본값
- 로그 파일 목록, 시간·level·component·run/request ID·문자열 필터 조회 API
- 관리자 로그 목록·상세·필터·새로고침 UI
- 회전 완료된 로그 파일의 확인 절차가 있는 삭제 UI·API
- 활성 로그 정리 요청은 새 파일로 rotate한 뒤 직전 archive만 삭제
- 로그 파일 삭제 관리자 작업의 별도 감사 기록

## 범위 밖

- 임의 SQL 입력·실행, DDL·DML과 범용 DB 관리 도구
- 정책 데이터의 UI 수정·삭제·승인
- PostgreSQL system catalog, 사용자·credential·Raw payload 직접 노출
- 로그 원문에 request body, API key, token, DB password 또는 SQL parameter 기록
- 브라우저에서 서버의 임의 파일 경로 열기·삭제
- 활성 로그 파일 handle의 직접 삭제; 정리는 rotate 후 archive 삭제로 처리
- 감사 기록의 같은 UI 삭제
- ELK·OpenSearch·Grafana·외부 SaaS와 분산 tracing 플랫폼
- WebSocket 기반 실시간 tail; 초기 버전은 명시적 새로고침 또는 polling

## 선행 조건

- Backend 04의 관리자 인증·권한과 `401`·`403` 계약이 완료돼야 한다.
- 관리자 UI는 Backend 04의 아이디 없는 4자리 PIN session과 짧은 수명 token을
  재사용한다.
- W4-G0에서 공개 가능한 Policy 컬럼, 로그 directory·format·rotation·retention,
  삭제 권한과 감사 경계를 승인해야 한다.
- Backend 03의 SQL statement logging 기본 off와 parameter 비노출을 유지한다.
- Runtime 로그 directory는 Git 제외 경로이고 서버가 시작할 때 안전하게 생성할
  수 있어야 한다.

## 공통 설계 원칙

- DB 화면은 승인된 Repository·DTO만 사용하며 table name, column name이나 SQL을
  사용자 입력에서 조합하지 않는다.
- 대량 DB row와 로그 파일을 한 번에 메모리에 올리지 않고 cursor 또는 제한된
  pagination으로 읽는다.
- 로그는 오류 위치를 추적할 correlation 정보를 제공하되 비밀정보와 정책 Raw를
  기록하지 않는다.
- 예외 stack은 운영자 진단에 필요한 범위에서만 파일에 기록하고 API·UI에는
  승인된 안전한 필드만 제공한다.
- 삭제 요청은 서버가 발급한 log file ID만 받고 resolved path가 승인 log
  directory와 파일명 규칙 안에 있는지 다시 검증한다.
- Windows에서 열린 파일을 삭제할 수 없는 경계를 고려해 활성 파일은 먼저
  rotate한 뒤 archive만 삭제한다.
- 로그 삭제 사실은 삭제 대상 파일 밖의 `AdminAuditEvent` 또는 별도 비삭제
  감사 저장소에 관리자·시각·대상·결과로 남긴다.

## W4-G0 계약 후보

다음은 승인 전 제안이며 현재 API·DB 계약이 아니다.

| 항목 | 제안 기준선 |
| --- | --- |
| DB 탐색 대상 | `Policy` 승인 projection 한 종류; arbitrary table 제외 |
| DB 동작 | 읽기 전용 목록·row 상세, 서버 pagination·allowlist 정렬·필터 |
| 로그 형식 | 한 event당 한 줄인 UTF-8 JSON Lines |
| 기본 로그 level | 앱 `INFO`, 오류 `ERROR`, SQL statement off, parameter 항상 숨김 |
| 세부 level | API·collector·extractor·normalizer·validator·persistence별 환경설정 |
| correlation | request ID, CollectionRun ID와 Source ID를 가능한 범위에서 연결 |
| rotation | 활성 파일 1개와 날짜·크기 기준 archive, 상한 초과 자동 정리 |
| 조회 | archive·current의 bounded pagination과 안전한 필드 검색 |
| 삭제 | 회전 완료 archive만, 명시 확인·재인증 또는 승인 보호절차 뒤 삭제 |
| 현재 로그 정리 | 먼저 rotate하고 생성된 직전 archive를 같은 보호절차로 삭제 |
| 감사 | 삭제 성공·실패를 operational log와 분리해 보존 |

정확한 파일명, 보존 기간, 용량 상한, endpoint와 DTO는 Backend OpenAPI와
Frontend TypeScript 소비 초안을 대조한 뒤 확정한다.

## Slice 계획

### AO0 - 현재 DB·logging inventory와 계약

- Policy model·API projection과 관리자에게 필요한 컬럼을 대조한다.
- 현재 stdout logger, SQL logging·redaction과 수집 단계의 log coverage를
  조사한다.
- 데이터 조회, 파일 보존·rotation·조회·삭제·감사 계약을 공동 승인한다.

### AO1 - Backend 정책 데이터 탐색 API

- 관리자 전용 읽기 Repository·Service·목록·상세 DTO를 구현한다.
- pagination, allowlist filter·sort와 최대 page size를 강제한다.
- arbitrary SQL·table·column 주입과 민감 필드 노출을 테스트한다.

### AO2 - Backend 구조화 파일 logging

- stdout과 구조화 file handler를 중복 event 없이 구성한다.
- rotation·retention·UTF-8·size cap과 컴포넌트별 level 설정을 구현한다.
- request·CollectionRun·Source correlation과 단계별 안전 event를 연결한다.
- credential·token·Raw·SQL parameter redaction 회귀를 추가한다.

### AO3 - Backend 로그 조회·삭제·감사 API

- 안전한 log file ID와 bounded list/detail·filter API를 구현한다.
- archive 삭제 전에 권한·확인·path containment·active 여부를 검증한다.
- 현재 로그 정리는 원자적인 rotate → 대상 archive 확인 → 삭제 순서를 사용한다.
- 삭제 결과를 별도 감사 저장소에 기록하고 실패해도 감사 흔적을 남긴다.

### AO4 - Frontend 데이터·로그 관리자 UI

- `/admin/data`에 CSV형 정책 표·필터·pagination·row 상세를 구현한다.
- `/admin/logs`에 파일·event 목록, level·component·ID·기간 필터와 상세를
  구현한다.
- archive 삭제는 대상 파일명·기간·크기를 다시 보여주고 명시 확인을 요구한다.
- 활성 파일 선택 시 직접 삭제하지 않고 `현재 로그 정리`가 rotate 후 삭제됨을
  안내한다.
- 삭제 성공·실패, 파일이 이미 없음, 활성 파일 보호와 권한 상태를 표시한다.

### AO5 - 실제 진단 E2E

- 실제 PostgreSQL 정책 row가 관리자 표와 상세에 일치하는지 검증한다.
- 의도된 API·수집 실패를 발생시켜 file log → 조회 API → UI correlation을
  확인한다.
- archive rotation·삭제·감사 기록을 실제 Runtime directory에서 검증한다.
- 기존 콘솔 로그, SQL parameter 비노출과 Release 1 검색 회귀를 수행한다.

## 검증 계획

- Backend Policy 관리자 Repository·pagination·filter·sort 단위 테스트
- PostgreSQL 실제 row count·row detail 통합 테스트
- 관리자 `401`·`403`, 입력 allowlist와 page size 경계 테스트
- file handler 중복 방지, UTF-8, rotation·retention·size cap 테스트
- request/run/source correlation과 level filter 테스트
- credential·token·Raw·SQL parameter redaction 테스트
- path traversal·임의 파일 ID·active file·동시 삭제·이미 삭제됨 테스트
- 삭제 성공·실패 감사 기록과 rollback 경계 테스트
- Frontend 데이터 표·로그 필터·상세·삭제 확인 UI 테스트
- 실제 PostgreSQL·Runtime log directory·FastAPI·React Browser E2E
- Backend·Frontend 전체 회귀, `python scripts/validate_docs.py`,
  `git diff --check`

## Forest 완료 기준

- 관리자가 정책 데이터를 CSV형 표와 row 상세로 읽기 전용 조회할 수 있음
- 임의 SQL·table 접근과 정책 데이터 수정·삭제 경로가 존재하지 않음
- API·수집·DB 오류가 구조화된 UTF-8 파일 로그로 rotation·보존됨
- request·CollectionRun·Source ID로 오류 발생 단계를 추적할 수 있음
- 관리자 UI에서 로그를 필터·상세 조회할 수 있음
- archive 로그 삭제가 확인·권한·path 보호를 거치고 감사 기록을 남김
- 현재 로그 정리가 rotate 후 삭제돼 실행 중 file handle을 훼손하지 않음
- 활성 파일·감사 기록·임의 서버 파일은 UI에서 삭제할 수 없음
- 실제 PostgreSQL·file log·API·Browser E2E와 보안 회귀가 통과함
- API·DB·운영·환경설정 문서와 개발 기록이 실제 구현과 일치함

## 위험과 미확정 사항

- 모든 DB table을 그대로 노출하면 credential·내부 Schema·Raw가 유출될 수 있어
  첫 범위는 승인 Policy projection으로 제한한다.
- 로그 파일을 API 요청마다 처음부터 스캔하면 메모리·응답시간 문제가 생길 수
  있어 page·시간 범위·파일 크기를 제한하고 필요 시 offset index를 후속
  결정한다.
- 상세 stack trace는 공격 정보나 비밀을 포함할 수 있어 파일 redaction과 UI
  공개 수준을 별도로 승인해야 한다.
- 로그 삭제는 복구가 어려운 작업이다. 회전 archive만 대상으로 하고 명시 확인,
  감사 기록과 실제 Runtime backup 정책을 함께 검증해야 한다.
- 여러 Backend process가 같은 파일에 쓰는 배포 구조가 생기면 단일 process용
  file handler를 그대로 사용할 수 없으므로 v1.0.0 배포 Forest에서 재검토한다.

## 관련 문서

- [v0.5.0 Contract Baseline](05_v0_5_0_contract_baseline.md)
- [Backend Admin Access Control](../backend/04_admin_access_control.md)
- [CollectionRun Admin API](../backend/05_collection_run_admin_api.md)
- [CollectionRun Admin UI](../frontend/03_collection_run_admin_ui.md)
- [Backend Policy Runtime Safety](../backend/03_policy_runtime_safety.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)

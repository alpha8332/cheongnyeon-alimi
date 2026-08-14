# Integration 07 Release 2 Feature Acceptance Forest 개발 계획

## 계획 정보

- 번호: Integration 07
- 담당 영역: Team Leader - Integration
- 상태: draft
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 선행 Forest: Backend 04·05, Frontend 03·05, Data 03·04·05·06,
  Integration 06·08·09
- 참여·검증: Data·Backend·Frontend, 보고서·사용성 리뷰어·QA
- 작업 브랜치: 착수 전에 현재 브랜치 전략에 맞는 cross-area domain 합의 필요

## 목적

4주차 공식 웹 Source·자격요건·지역 정책·사용자·관리자 기본 기능을 실제
PostgreSQL → FastAPI → React 흐름으로 중간 인수하고, 5주차 Data 06 구현·독립
리뷰·QA·결함 수정·UI/UX 최적화와 Release 2 Gate까지 하나의 목표 기반
Forest에서 관리한다.

## 범위

- W4-G0 승인 계약과 각 Forest 소비 일치 확인
- 관리자 로그인 → 이력 → 수동 실행 → 상태·품질 통계 E2E
- 관리자 로그인 → 정책 데이터 표·row 상세 → 로그 검색·correlation → 회전
  archive 삭제·감사 E2E
- 공식 HTTPS Source → Raw·정규화·DB → 핵심 신청 조건 상세 UI E2E
- 지역 공식 Source → 지역 고유성·온통청년/복지로 중복 제외 → DB·검색·상세 E2E
- 중앙·공공기관 보완 Source → 중복·마감·근거 부족 제외 → DB·검색·상세 E2E
- 사용자 조건 → 추천 → 이유 → 즐겨찾기 → D-Day·알림·`.ics` E2E
- 기존 검색·상세·Release 1 golden 회귀
- 실제·경계·실패 데이터와 loading·empty·error·partial 상태
- 4주차 midpoint 판정과 5주차 리뷰어·QA 결함 triage
- Release 2 증거와 최종 `v0.5.0` 판정

## 범위 밖

- 각 담당 Forest의 기능 구현을 대신하는 작업
- Production Docker·Nginx·CI와 clean-room 배포
- 승인되지 않은 신규 기능 추가
- `v0.5.0` tag를 4주차 midpoint에서 생성하는 작업

## 선행 조건

- Integration 05 `W4-G0_APPROVED`와 각 기능 Forest의 실행 가능한 계약이
  필요하다.
- 실제 PostgreSQL 테스트 DB, 승인 snapshot과 Frontend actual API 모드를
  준비한다.
- 사용성 리뷰어·QA·보고서 역할과 증거 양식을 5주차 전에 확정한다.

## 공통 설계 원칙

- 기능 구현 담당자의 자체 테스트와 독립 QA·사용성 근거를 구분한다.
- Mock·Seed만으로 실제 통합 통과를 대신하지 않는다.
- 실패한 첫 실행을 숨기지 않고 원인·재실행·최종 결과를 함께 기록한다.
- 4주차 midpoint를 Release 2 최종 통과나 tag 생성으로 해석하지 않는다.

## Slice 계획

### A0 - 인수 계약과 환경

- 공통 시작 SHA, Migration, snapshot과 실제 API 모드를 고정한다.
- 역할별 테스트 명령·지원 환경·증거 양식을 확정한다.

### A1 - 4주차 승인 기본 기능 midpoint acceptance

- 관리자 실행·데이터·영속 로그, 웹 Source·자격요건·지역 고유 정책 수집,
  추천·즐겨찾기·D-Day·알림·`.ics` E2E와 기존 검색 회귀를 실제 환경에서
  실행한다.
- 일정 재승인으로 Data 06은 A1 완료 조건에서 제외하고 A2의 첫 기능 Gate로
  이동한다. 다른 4주차 미완료 기능은 같은 방식으로 이월하지 않는다.
- Data 06을 제외한 4주차 승인 기본 기능 중 하나라도 미구현이면 W4-G4를
  통과시키지 않는다.
- 미완성·결함·계약 충돌을 blocker 또는 5주차 수정 대상으로 분류한다.
- 기능 연결이 확인되면 `W4-G4_MIDPOINT_PASS`를 기록한다.

### A2 - 5주차 추가 기능·최적화와 리뷰어·QA hardening

- Data 06 SOP0~SOP5와 actual·Forest 판정을 먼저 완료하고 기존 기능 전체와
  함께 W5-G1 기능 동결을 판정한다.
- 5주차 오류 수정·UI/UX 최적화와 담당자 자체 검증이 끝난 뒤
  팀 외 사용성 시나리오와 QA 전체 회귀를 수행한다.
- 재현 가능한 결함을 수정 담당·심각도·재검증 조건과 연결한다.
- 보고서 담당은 이 단계의 결정·화면·테스트와 미실행 검증을 대조한다.

### A3 - Release 2 Gate

- 수정본 재검증, 보고서 근거와 릴리스 체크리스트를 대조한다.
- Team Leader가 `pass`, `conditional` 또는 `blocked`를 근거와 함께 판정한다.

## Forest 완료 기준

- 웹 Source·자격요건·지역 고유·보완 공식 정책, 사용자·관리자 E2E와 기존 검색 회귀가
  Release 2 Gate
  전 실제 환경에서 통과함
- 관리자 데이터가 읽기 전용이고 로그 archive 삭제가 path 보호·감사를 거침
- 사용성 리뷰·QA·수정·재검증 증거가 서로 독립적으로 기록됨
- 비밀정보·Runtime Raw·DB 파일이 Git에 포함되지 않음
- Release 2 완료 조건과 알려진 제약이 문서·CHANGELOG에 일치함
- `develop`의 검증된 릴리스 커밋만 `main` PR과 `v0.5.0` tag 후보가 됨

## 검증 계획

- Data 전체 단위·통합, Backend PostgreSQL, Frontend unit·lint·build·Browser
  명령을 각 Forest의 확정 명령으로 실행한다.
- 실제 웹 Source·자격요건·지역 고유·보완 공식 정책, 사용자·관리자 데이터·로그 E2E와
  Release 1 golden
  검색 회귀를 수행한다.
- `python scripts/validate_docs.py`, 증거 JSON parse와 `git diff --check`를
  실행한다.

## 위험과 미확정 사항

- cross-area Forest에 맞는 branch domain이 현재 브랜치 전략에 정의되지 않아
  착수 전 브랜치명 합의가 필요하다.
- 한 주 안에 모든 기능을 확장형으로 구현하면 Backend가 병목이 되므로 W4-G0
  범위 밖 기능을 다시 끌어오지 않는다.
- actual snapshot은 외부 데이터 변화의 영향을 받으므로 고정 contract 회귀와
  최신 데이터 관찰을 별도 증거로 관리해야 한다.

## 관련 문서

- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [5주차 상세 실행 계획](../../weekly_plan/week_05_release_2.md)
- [Release와 Milestone 계획](../release_roadmap.md)
- [Recommendation Vertical Slice](06_recommendation_vertical_slice.md)
- [User Service Features](../frontend/05_user_service_features.md)
- [Data Quality Operations](../data/03_recurrent_collection_quality_operations.md)
- [Public HTTPS Policy Ingestion](../data/04_public_https_policy_ingestion.md)
- [Regional Youth Policy Ingestion](../data/05_regional_youth_policy_ingestion.md)
- [Supplemental Official Policy Ingestion](../data/06_supplemental_official_policy_ingestion.md)
- [Eligibility Evidence and Summary](08_eligibility_evidence_summary.md)
- [Admin Data and Log Console](09_admin_data_log_console.md)
- [Backend Admin Access Control](../backend/04_admin_access_control.md)
- [CollectionRun Admin API](../backend/05_collection_run_admin_api.md)
- [CollectionRun Admin UI](../frontend/03_collection_run_admin_ui.md)

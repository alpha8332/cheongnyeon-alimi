# Integration 05 v0.5.0 Contract Baseline Forest 개발 계획

## 계획 정보

- 번호: Integration 05
- 담당 영역: Team Leader - Integration
- 상태: draft
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 공통 시작점: `2b33ed7` (`v0.1.0`)
- 권장 브랜치: `docs/docs/v0-5-contract-baseline`
- 후속 Forest: Backend 04·05, Frontend 03·05, Data 03·04,
  Integration 06·07·08

## 목적

4주차 구현 전에 사용자 저장 경계, 관리자 인증·권한, 웹 Source, 자격요건 요약,
추천 의미, 수동 수집과 품질 노출 계약을 공동 승인한다. 승인 전에는 각 담당자가
서로 다른 인증, DTO, 저장 위치, Source 우선순위나 알림 주체를 구현하지 않는다.

## 범위

- 일반 사용자 계정과 개인정보 범위
- 사용자 조건·즐겨찾기 저장 위치와 버전·초기화 규칙
- 관리자 credential, 로그인, 토큰 수명, `401`·`403` 의미
- 추천 점수·이유·제외·미확정 조건의 의미와 UI 노출 경계
- 공식 HTTPS Source 선정, 허용 수집 범위와 Source별 identity
- 신청 조건·제외·우대·서류·확인 필요의 구조와 evidence 계약
- API·웹 원문 충돌, partial·unknown과 자격 비단정 문구
- D-Day의 `Asia/Seoul` 계산과 날짜 미상 처리
- 앱 내부 알림과 `.ics` 생성 주체
- 수동 수집 요청, 실행 ID, 동시 실행과 stale 판정
- 실패·partial·invalid·중복·수정 통계의 안전한 관리자 노출
- Backend OpenAPI 초안과 Frontend TypeScript 소비 초안의 상호 검토

## 범위 밖

- 승인된 계약의 실제 기능 구현
- 일반 사용자 가입·서버 프로필·다중 기기 동기화
- 외부 푸시·이메일·SMS 알림
- OAuth·외부 identity provider와 refresh token
- Scheduler·분산 queue·worker 플랫폼 도입
- ML·LLM·벡터 기반 추천
- 로그인·CAPTCHA 우회와 임의 사이트 범용 크롤링
- Source 근거가 없는 생성형 자격요건 요약

## 선행 조건

- Release 1 publication과 `develop` fast-forward가 완료돼야 한다.
- 현재 Policy·Search·CollectionRun 계약과 기존 관리자 Forest를 확인한다.
- Data·Backend·Frontend 담당자가 W4-G0 소비 검토에 참여한다.

## 공통 설계 원칙

- 승인 전 제안을 현재 API·DB 계약이나 완료 기능으로 기록하지 않는다.
- 일반 사용자 개인정보와 서버 저장은 필요한 근거가 없으면 추가하지 않는다.
- 인증·추천·품질 의미는 한 영역이 단독으로 확정하지 않는다.
- 비밀정보, Raw payload와 stack trace는 계약 예시에도 포함하지 않는다.
- 정책 상세는 핵심 조건을 읽기 쉽게 제공하되 수혜·선정 가능성을 확정하지
  않는다.

## W4-G0 결정 후보

다음은 승인 전 제안이며 현재 API·DB 계약이 아니다.

| 항목 | 제안 기준선 |
| --- | --- |
| 일반 사용자 | 계정 가입 없이 사용 |
| 조건·즐겨찾기 | versioned `localStorage`, 개인정보 최소화와 전체 삭제 제공 |
| 앱 내부 알림 | 즐겨찾기와 마감일을 브라우저에서 계산, 외부 전송 없음 |
| 관리자 | 환경변수 credential을 로그인 시 검증하고 짧은 수명 서명 토큰 발급 |
| 관리자 역할 | `admin`을 명시하고 미인증 `401`, 권한 부족 `403` 구분 |
| 추천 | 기존 결정적 검색·판정 primitive 재사용, 이유·미확정 조건 제공 |
| 추천 점수 | 요청 내부 정렬용이며 자격 확률이 아님; UI는 이유와 구간을 우선 |
| 웹 Source | 승인된 공식 HTTPS 사이트 한 곳, 정적 HTML·허용된 공개 요청 우선 |
| 조건 요약 | 필수·제외·우대·서류·확인 필요와 필드별 Source evidence 제공 |
| 개인 비교 | `조건상 일치`, `조건상 불일치`, `추가 확인 필요`; 최종 자격 단정 금지 |
| D-Day | 신청 종료일과 `Asia/Seoul` 날짜 기준, 날짜 미상은 계산하지 않음 |
| 캘린더 | 정책별 `.ics` 다운로드, 서버 캘린더 계정 연동 없음 |
| 수동 수집 | `202`와 `collection_run_id`, Source별 활성 실행 1개, polling |
| 품질 오류 | 원문·credential·stack trace 없이 분류·건수·안전한 메시지만 노출 |

## Slice 계획

### C0 - 현재 계약 inventory

- Policy·CollectionRun·검색 DTO와 인증 부재 상태를 확인한다.
- Release 1에서 이관된 API 오류 UX, 긴 지역 목록과 보고서 검토를 연결한다.

### C1 - 사용자·추천 계약

- localStorage key·version·migration·삭제 규칙을 확정한다.
- 정책 상세의 핵심 신청 조건 구조, evidence와 자격 비단정 문구를 확정한다.
- 추천 request·response, 이유·미확정 조건과 자격 비확정 문구를 확정한다.
- D-Day, 내부 알림과 `.ics`의 날짜 미상·마감 경계를 확정한다.

### C2 - 웹 Source·수집·품질 계약

- 대표 공식 HTTPS Source, 허용 경로·빈도·보존 범위와 Source ID를 확정한다.
- API·웹 원문의 identity·충돌·partial·provenance 의미를 확정한다.
- selector drift, 실패 격리와 Runtime HTML 비추적 경계를 확정한다.

### C3 - 관리자·수동 실행 계약

- credential 주입, 토큰, 역할과 오류 계약을 확정한다.
- 수동 실행의 `202`, run ID, 중복·동시 실행·stale 의미를 확정한다.
- 관리자에게 노출 가능한 품질 통계와 오류 redaction을 확정한다.

### C4 - 소비자 검토와 Gate

- Data·Backend·Frontend 초안을 대조하고 Schema·API·UI 충돌을 해소한다.
- 미확정 사항의 차단 여부, 담당과 재검토 조건을 기록한다.
- 모두 합의되면 Team Leader가 `W4-G0_APPROVED`를 기록한다.

## Forest 완료 기준

- 인증·저장·추천·날짜·수동 실행·품질 노출의 권위와 책임이 정해짐
- 대표 웹 Source와 자격요건 요약·evidence·비단정 의미가 정해짐
- Backend OpenAPI와 Frontend TypeScript 초안을 작성할 만큼 계약이 명확함
- 일반 사용자 계정, 외부 알림, worker가 현재 범위 밖임이 명시됨
- 기존 Backend 04·05와 Frontend 03 계획의 미확정 경계가 해소됨
- Data·Backend·Frontend 소비 검토와 `W4-G0_APPROVED`가 기록됨
- `python scripts/validate_docs.py`와 `git diff --check` 통과

## 검증 계획

- 현재 API·Schema·DB 문서와 제안 계약의 필드·상태 의미를 대조한다.
- Backend OpenAPI와 Frontend TypeScript 소비 초안의 누락·충돌을 확인한다.
- `python scripts/validate_docs.py`와 `git diff --check`를 실행한다.

## 위험과 미확정 사항

- 관리자 credential 저장·검증 방식과 token library는 W4-G0 승인 전 미확정이다.
- 대표 공식 HTTPS 사이트가 아직 선정되지 않아 Data 04 구현은 W4-G0 승인 전
  시작할 수 없다.
- 수동 수집을 API process 안에서 실행할지 별도 process로 실행할지 결정이
  필요하며 worker 도입은 현재 범위 밖이다.
- cross-area Acceptance Forest의 브랜치 domain이 현재 브랜치 전략에 없어
  Integration 07 착수 전에 팀 합의가 필요하다.

## 관련 문서

- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [전체 Forest 로드맵](../forest_roadmap.md)
- [Backend Admin Access Control](../backend/04_admin_access_control.md)
- [Backend CollectionRun Admin API](../backend/05_collection_run_admin_api.md)
- [Frontend CollectionRun Admin UI](../frontend/03_collection_run_admin_ui.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [Public HTTPS Policy Ingestion](../data/04_public_https_policy_ingestion.md)
- [Eligibility Evidence and Summary](08_eligibility_evidence_summary.md)

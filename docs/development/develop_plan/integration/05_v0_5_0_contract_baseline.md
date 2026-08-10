# Integration 05 v0.5.0 Contract Baseline Forest 개발 계획

## 계획 정보

- 번호: Integration 05
- 담당 영역: Team Leader - Integration
- 상태: approved
- 진행: `C0`~`C4` 완료, Team Leader가 `W4-G0_APPROVED` 판정
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 공통 시작점: `2b33ed7` (`v0.1.0`)
- 권장 브랜치: `docs/docs/v0-5-contract-baseline`
- 후속 Forest: Backend 04·05, Frontend 03·05, Data 03·04,
  Integration 06·07·08·09

## 실행 기준

- DTL4-0 확인일: `2026-08-10`
- 실제 시작 SHA: `e5ff8c81e0e902723c5b79dee1267be7e5e2e66c`
- 시작 브랜치·merge target: `develop`
- 현재 작업 브랜치: `docs/docs/v0-5-contract-baseline`
- Release 기준: `main`·`origin/main`·`v0.1.0`은
  `2b33ed7d8d4e281487b5734bd88cfd73b6d60175`, `develop`·
  `origin/develop`은 실제 시작 SHA와 일치
- DTL4-0 환경·담당·브랜치 확인 결과:
  [Integration 05 개발 기록](../../development_notes/integration/v0_5_0_contract_baseline.md)

Backend 04는 공통 계약 승인 전에 별도 브랜치
`origin/feature/backend/admin-access-control`의
`f7ffca4254a52cc94666a575567cbf73b7cb92de`까지 구현됐다. 이 결과는
승인 전에는 Backend 제안 구현으로 취급했다. 브랜치명과 선행 구현 시점은
계약 차이가 아니며, 아래 승인 계약과의 구현 적합성은 `W4-G1`에서 대조한다.

## 목적

4주차 구현 전에 사용자 저장 경계, 관리자 인증·권한, 웹 Source, 자격요건 요약,
추천 의미, 수동 수집, 관리자 데이터 탐색과 영속 로그 계약을 공동 승인한다.
승인 전에는 각 담당자가 서로 다른 인증, DTO, 저장 위치, Source 우선순위,
로그 보존·삭제 방식이나 알림 주체를 구현하지 않는다.

## 범위

- 일반 사용자 계정과 개인정보 범위
- 사용자 조건·즐겨찾기 저장 위치와 버전·초기화 규칙
- 아이디 없는 4자리 관리자 PIN, 최초 `0000` 경계, token 수명과
  `401`·`403`·`429` 의미
- 추천 점수·이유·제외·미확정 조건의 의미와 UI 노출 경계
- 공식 HTTPS Source 선정, 허용 수집 범위와 Source별 identity
- 신청 조건·제외·우대·서류·확인 필요의 구조와 evidence 계약
- API·웹 원문 충돌, partial·unknown과 자격 비단정 문구
- D-Day의 `Asia/Seoul` 계산과 날짜 미상 처리
- 앱 내부 알림과 `.ics` 생성 주체
- 수동 수집 요청, 실행 ID, 동시 실행과 stale 판정
- 실패·partial·invalid·중복·수정 통계의 안전한 관리자 노출
- 관리자 Policy 데이터의 읽기 전용 projection·pagination·filter·sort
- 구조화 파일 로그의 directory·format·level·rotation·retention·redaction
- 관리자 로그 조회·archive 삭제·별도 감사 기록과 path 보호
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
- arbitrary SQL·table 탐색과 관리자 UI의 정책 데이터 수정·삭제
- 활성 로그·감사 기록·임의 서버 파일의 관리자 UI 삭제

## 선행 조건

- Release 1 publication과 `develop` fast-forward가 완료돼야 한다.
- 현재 Policy·Search·CollectionRun 계약과 기존 관리자 Forest를 확인한다.
- Team Leader가 Data inventory와 Backend 구현 대조를 근거로 W4-G0을 승인한다.
- Frontend TypeScript·Mock과 Backend 구현 적합성은 W4-G1에서 확인한다.

## 공통 설계 원칙

- 승인 전 제안을 현재 API·DB 계약이나 완료 기능으로 기록하지 않는다.
- 일반 사용자 개인정보와 서버 저장은 필요한 근거가 없으면 추가하지 않는다.
- 인증·추천·품질 의미는 한 영역이 단독으로 확정하지 않는다.
- 비밀정보, Raw payload와 stack trace는 계약 예시에도 포함하지 않는다.
- 로그는 오류 위치를 찾을 correlation을 제공하되 credential·Raw·SQL
  parameter를 기록하지 않는다.
- 정책 상세는 핵심 조건을 읽기 쉽게 제공하되 수혜·선정 가능성을 확정하지
  않는다.

## W4-G0 승인 기준선

다음 계약은 `2026-08-10` Team Leader가 `W4-G0_APPROVED`로 승인했다.

| 항목 | 제안 기준선 |
| --- | --- |
| 일반 사용자 | 계정 가입 없이 사용 |
| 조건·즐겨찾기 | versioned `localStorage`, 개인정보 최소화와 전체 삭제 제공 |
| 앱 내부 알림 | 즐겨찾기와 마감일을 브라우저에서 계산, 외부 전송 없음 |
| 관리자 입력 | 아이디 없이 4자리 숫자 PIN 한 칸 |
| 최초 PIN | `development`·localhost에서만 `0000`; 외부·production 기본값 금지 |
| 관리자 설정 | 명시적 PIN hash와 별도 token secret, 미설정 배포는 fail-closed |
| 관리자 session | PIN hash 검증 뒤 짧은 수명 서명 token 발급, 반복 실패 rate limit |
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
| DB 데이터 화면 | 승인 Policy projection만 읽기 전용 표·상세로 제공, arbitrary SQL 제외 |
| 파일 로그 | UTF-8 JSON Lines, stdout 병행, component level·rotation·retention |
| 로그 삭제 | 회전 archive만 확인 절차 뒤 삭제, path containment와 별도 감사 기록 |

## DTL4-1 승인 계약 (`2026-08-10`)

현재 Gate 상태는 `W4-G0_APPROVED`다. Team Leader가 Data inventory, Backend
구현 대조와 공식 웹 Source preflight를 근거로 승인했다. Frontend 미착수로
TypeScript·Mock 소비 대조는 실행하지 않았으며 `W4-G1` 적합성 확인으로
이관한다. 이후 구현이 이 기준선과 다르면 계약을 먼저 변경한다.

### 반복 수집·품질 의미

| 결과 | 검토안 |
| --- | --- |
| `inserted` | `(source_id, external_id)`가 없는 새 Policy identity를 처음 저장 |
| `updated` | 승인한 business field 또는 검색 projection이 기존 값과 다름 |
| `unchanged` | business field와 검색 projection이 같음. `collected_at`, Raw hash·ID, run ID, 저장 시각만 달라진 경우 포함 |
| `duplicate` | 한 실행 또는 같은 snapshot에 같은 source-scoped identity가 반복됨. 첫 canonical 후보 외에는 저장하지 않고 별도 집계 |
| `partial` | Policy는 저장 가능하지만 필수 검색·조건 coverage 일부가 근거 부족이며 사용자에게 partial로 노출 |
| `invalid` | Normalized Schema 또는 값 불변식을 위반해 저장 불가 |
| `rejected` | invalid 또는 승인하지 않은 identity 경계로 import 대상에서 제외 |
| `failed` | fetch·extract·normalize·validate·persist 단계의 실행 실패. 안전한 stage·error type만 노출 |

현재 importer는 `collected_at`과 provenance도 mutable 비교에 포함하므로 동일
business payload의 재수집이 거짓 `updated`가 될 수 있다. Data 03은 business
비교 field와 실행 metadata를 분리하고 `duplicate_count`·`rejected_count`의
CollectionRun 저장 여부를 Backend 05 소비 계약과 함께 확정한다.

### 공식 웹 Source와 identity

| 항목 | 검토안 |
| --- | --- |
| 사이트 | [천안청년센터 이음 공지](https://www.ch2030youth.kr/bbs/board.php?bo_table=notice&wr_id=674), 천안시 청년지원기관 공개 게시판 |
| Source ID | `cheonan-youthcenter-web` |
| 목록 | `/bbs/board.php?bo_table=notice`, 익명 공개 공지 목록 1회만 허용 |
| 상세 | `/bbs/board.php?bo_table=notice&wr_id={positive_integer}`, 승인 표본은 `wr_id=674` 1건 |
| identity | `notice:{wr_id}`; 표본 external ID는 `notice:674` |
| 충돌 | API와 자동 병합하지 않고 source-scoped identity를 유지하며 내용·기간 불일치는 conflict로 보존 |
| 허용 경계 | 동시 요청 1개, 목록 1회와 승인 상세 1건, 요청 시작 간격 최소 2초, pagination·대량 순회 금지 |
| 제외 | 로그인·회원·신청·CAPTCHA·첨부·이미지·이메일·전화번호·개인정보 페이지 |
| 보존 | actual HTML은 `runtime/html/`에만 보존하고 Git에는 원문 복제 대신 합성·최소 구조 fixture만 허용 |

`2026-08-10` 익명 공개 화면에서 게시물 제목·게시일·지원 대상·지원 내용·
제출서류·유의사항을 확인했다. `/robots.txt`는 directive가 아닌 HTTP 404
페이지를 반환했고 별도 사이트 이용약관은 찾지 못했으며 footer는
`all rights reserved`를 표시한다. 따라서 공개 사실만 최소 추출하고 원문 HTML,
이미지, 연락처와 첨부는 Git에 재배포하지 않는 위 경계를 Team Leader가 승인했다.

표본은 `2026-07-24` 게시됐지만 본문 신청기간은
`2026-04-22`~`2026-05-06 23:00`이고 제목에는 “곧 마감”이 있어 서로 충돌한다.
수집 시 값을 임의 보정하지 않고 `data_quality_status=partial`, 신청 상태는
`unknown`과 확인 필요 evidence로 기록한다. 신청 방법의 회원가입·로그인은
수집기가 따라가지 않는다.

### 자격요건 evidence 호환 확장

기존 `eligibility_text`, `required_conditions`, `preferred_conditions`,
`excluded_conditions`는 유지한다. 새 구조는 기존 소비자를 깨지 않는
`eligibility_summary` 후보로 검토한다.

| 필드 | 의미 |
| --- | --- |
| `coverage` | `complete`, `partial`, `unknown` |
| `requirements` | 필수 조건 evidence item 배열 |
| `exclusions` | 참여 제한·제외 evidence item 배열 |
| `preferences` | 우대 조건 evidence item 배열 |
| `documents` | 제출 서류 evidence item 배열 |
| `unknowns` | 자동 구조화·비교하지 못한 원문 evidence item 배열 |

각 evidence item은 `category`, 원문을 훼손하지 않은 `text`와 하나 이상의
evidence를 가진다. evidence는 `source_id`, `source_url`, `collected_at`,
`locator_type`(`source_field` 또는 `css_selector`)과 `locator`를 포함한다.
개인 비교 verdict는 저장 Data가 아니라 Backend 응답에서 `match`, `mismatch`,
`unknown`으로 계산하며 UI 문구는 각각 `조건상 일치`, `조건상 불일치`,
`추가 확인 필요`로 제한한다.

Release 1 snapshot의 현재 구조화 배열은 두 Source 모두
`required/preferred/excluded`, education·employment coverage가 0건이다.
`eligibility_text`는 온통청년 2,695건 중 1,024건, 복지로 461건 중 5건만
존재하며 제출 서류 전용 구조와 항목별 evidence는 없다. 따라서 이 확장은
호환 추가 Schema·DB·API 작업이며 기존 문자열을 새 구조로 추정 변환하지 않는다.

### 사용자·추천·날짜 소비 경계

- localStorage 후보 key는 `cheongnyeon-alimi:user-state`, payload `version=1`로
  고정하고 이름·연락처·생년월일·상세 주소를 저장하지 않는다.
- 조건은 나이 정수, canonical 지역 code, 승인 enum과 free-text keyword의 최소
  집합만 저장한다. 즐겨찾기는 source-scoped identity를 저장한다.
- 알 수 없는 version·손상 payload는 별도 migration이 없으면 안전하게 초기화하고
  사용자에게 알린다. 설정 화면에서 조건·즐겨찾기·알림 상태 전체 삭제를 제공한다.
- 추천은 기존 검색·3값 판정 primitive를 재사용하고 점수는 같은 요청 안의
  정렬용이다. 응답은 이유와 `unknown` 조건을 우선하며 자격 확률을 표시하지 않는다.
- D-Day는 `application_end`가 있는 fixed period만 `Asia/Seoul` calendar date로
  계산한다. `always`, `until_budget_exhausted`, null·불일치 기간에는 생성하지 않는다.
- 앱 내부 알림과 정책별 all-day `.ics`는 브라우저가 생성하며 외부 전송·서버
  캘린더 계정 연동을 하지 않는다.

### 관리자 계약 대조 결과

Backend `f7ffca4254a52cc94666a575567cbf73b7cb92de`의 4자리 PIN DTO,
`POST /api/v1/admin/session`, 60분 bearer token, `admin` role,
`401`·`403`·`422`·점진적 `429`와 공통 dependency는 기준선과 일치한다.
브랜치명과 Backend의 구현 시점은 Gate 차단 사유가 아니다.

다음 두 항목은 W4-G1에서 Backend 구현 적합성 확인 또는 수정이 필요하다.

1. 기본 `0000`은 `ENVIRONMENT` 값만 검사하고 실제 localhost host·bind 경계를
   검사하지 않아 development 설정의 외부 bind에서도 허용될 수 있다.
2. `ADMIN_TOKEN_SECRET`이 없으면 `SECRET_KEY`로 fallback하며 기본
   `dev-secret-key-change-in-production`도 사용할 수 있어, production의 별도
   token secret 미설정 fail-closed 기준과 다르다.

IP별 rate limit은 process memory 기준이므로 현재 단일 process 로컬·시연
기준선으로만 검토한다. 다중 worker·reverse proxy production 보장은 범위 밖이며
외부 배포 전 별도 보강 조건으로 기록한다.

### W4-G1 적합성 후속 항목

| ID | 상태 | 다음 담당 | 완료 조건 |
| --- | --- | --- | --- |
| `W4-G1-BE-AUTH` | review-pending | Backend | localhost `0000` 경계와 production 별도 token secret fail-closed 대조·수정 근거 |
| `W4-G1-FE-CONSUMER` | review-pending | Frontend | PIN·관리자·자격요건·추천·localStorage·날짜 TypeScript·Mock 소비 검토 |

두 항목은 W4-G0 승인을 막지 않는다. W4-G1에서 실제 구현과 승인 계약의 parity를
확인하며 차이가 있으면 구현을 임의 정답으로 삼지 않고 계약 변경을 먼저 기록한다.

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

- 4자리 PIN, 최초 `0000` 허용 환경, hash·token secret 주입과 오류 계약을
  확정한다.
- 수동 실행의 `202`, run ID, 중복·동시 실행·stale 의미를 확정한다.
- 관리자에게 노출 가능한 품질 통계와 오류 redaction을 확정한다.
- 관리자 Policy 데이터 projection과 읽기 전용 query allowlist를 확정한다.
- file log format·level·rotation·retention과 조회·삭제·감사 경계를 확정한다.

### C4 - 소비자 검토와 Gate

- Data·Backend·Frontend 초안을 대조하고 Schema·API·UI 충돌을 해소한다.
- 미확정 사항의 차단 여부, 담당과 재검토 조건을 기록한다.
- Team Leader가 근거와 후속 적합성 항목을 구분해 `W4-G0_APPROVED`를 기록한다.

## Forest 완료 기준

- 인증·저장·추천·날짜·수동 실행·품질 노출의 권위와 책임이 정해짐
- 대표 웹 Source와 자격요건 요약·evidence·비단정 의미가 정해짐
- 관리자 DB 탐색과 영속 로그·조회·archive 삭제의 보안 경계가 정해짐
- Backend OpenAPI와 Frontend TypeScript 초안을 작성할 만큼 계약이 명확함
- 일반 사용자 계정, 외부 알림, worker가 현재 범위 밖임이 명시됨
- 기존 Backend 04·05와 Frontend 03 계획의 미확정 경계가 해소됨
- Team Leader 승인과 W4-G1 Backend·Frontend 소비 적합성 항목이 기록됨
- `python scripts/validate_docs.py`와 `git diff --check` 통과

## 검증 계획

- 현재 API·Schema·DB 문서와 제안 계약의 필드·상태 의미를 대조한다.
- Backend OpenAPI와 Frontend TypeScript 소비 초안의 누락·충돌을 확인한다.
- `python scripts/validate_docs.py`와 `git diff --check`를 실행한다.

## 위험과 미확정 사항

- 관리자 credential 구현의 승인 계약 적합성은 W4-G1에서 확인한다.
- 공개 README에는 실제 PIN·hash·secret이 아니라 설정·hash 생성·교체 방법만
  기록한다.
- 천안청년센터 공지 674번을 대표 표본으로 승인했지만 robots directive와 별도
  이용약관을 확인하지 못했다. 승인 요청 예산을 넘는 확대 수집은 제공기관
  확인 또는 별도 계약 변경 전 시작하지 않는다.
- Runtime log directory, 보존 상한과 삭제 감사 저장소의 구현값은 W4-G1에서
  승인 기준선과 대조한다.
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
- [Admin Data and Log Console](09_admin_data_log_console.md)

# 5주차 - 안정화·사용자 검증과 Release 2

## 계획 정보

- 상태: in-progress (`W5-G0_PASS`, `W5-B1`·`W5-F1` 인수와 `W5-I1` 대기)
- 권장 실행 창: `2026-08-17`~`2026-08-21` (달력보다 Gate 순서를 우선)
- 대상 Release: `v0.5.0`
- 수행 역할: Data, Backend, Frontend, Team Leader - Integration
- 독립 검증 역할: 사용성 리뷰어, QA
- 근거 정리 역할: 보고서 담당
- 상위 Forest: [Integration 07 Release 2 Feature Acceptance](../develop_plan/integration/07_release_2_feature_acceptance.md)
- Data·Team Leader 실행 계획:
  [5주차 Data·Team Leader 실행 계획](week_05_data_team_leader.md)
- 공통 시작점: Data 06을 제외한 4주차 기본 기능과 Data 05가 `develop`에
  병합되고 5주차 계획까지 동기화된 `29b2dd5`

5주차는 Team Leader 단독 작업이 아니다. Data·Backend·Frontend가 각 담당
영역의 결함 수정과 자체 회귀를 수행하고, Team Leader는 실제
PostgreSQL → FastAPI → React 통합, 독립 리뷰·QA와 Release 2 Gate를 주관한다.

## 일정 재승인 (`2026-08-14`)

- 4주차 데드라인 경과와 Backend·Frontend 통합 대기 상태를 반영해 Data 06
  구현을 4주차에서 5주차로 이동한다.
- 4주차는 Data 05 완료 결과와 Backend·Frontend 변경을 병합한 뒤 DTL4-5,
  담당자 회귀와 W4-G4 midpoint를 먼저 닫는다.
- Data 06은 범위 삭제가 아니라 실행 시점 변경이다. `2026-08-17` 재승인 기준인
  승인 Source 5개 actual·신규 정책 1개 이상·비accepted 무적재·DB/API/Browser를
  W5-G1 전까지 완료한다.
- Data 06이 지연되면 독립 사용성 리뷰·QA를 먼저 시작하지 않는다. Backend·
  Frontend는 기다리는 동안 자기 영역 회귀와 결함 수정을 병렬로 수행한다.

## 목표

- 4주차에 완성한 사용자·관리자·데이터 기능을 실제 환경에서 안정화한다.
- 실제 데이터, 실패·partial·invalid, 권한과 오류 경계를 영역별로 검증한다.
- 팀 외 사용성 리뷰와 QA에서 발견한 결함을 수정하고 같은 시나리오로
  재검증한다.
- Release 2 완료 조건을 충족한 `develop`만 `main` PR과 `v0.5.0` tag 후보로
  승인한다.

## 시작 조건

- Data 05 완료 결과와 4주차 Backend·Frontend 필수 기능이 `develop`에 병합돼야 한다.
- DTL4-5 실제 PostgreSQL → API → Browser 소비 대조와 `W4-G4_MIDPOINT_PASS`가
  기록돼야 한다.
- Data 06은 일정 재승인에 따라 5주차 구현 범위로 이동하며, 미완료 자체를
  4주차 blocker로 보지 않는다. 다만 `v0.5.0` 최종 Gate 전에는 완료해야 한다.
- `W4-G4_MIDPOINT_PASS`와 공통 시작 SHA, Migration head, 실제 snapshot,
  Frontend actual API mode가 기록돼야 한다.
- 사용성 리뷰어·QA·보고서 역할과 증거 양식이 정해져야 한다.

선행 조건을 충족하지 못하면 5주차 기본 작업으로 이월하지 않고 4주차
blocker로 유지한다.

## 현재 기준선

- `develop`·`origin/develop`은 `29b2dd5ef596286ec2df1ede48398d94c0d010d7`
  (`docs(plan): detail week 5 release acceptance`)에서 일치한다.
- Data 05는 completed다. Data 06은 `W5-D1`~`W5-D3`에서 후보 정제, 승인
  Source 5개 Adapter·actual·offline replay와 KOSAF 신규 정책의
  PostgreSQL·API·Browser 인수를 완료해 `SOP-G5_PASS`다. 다음 단계는
  Data 06을 포함한 전체 actual E2E `W5-I1`이다.
- `v0.5.0` 기능 계약은 Integration 05와 각 담당 Forest를 따른다.
- Release 2 인수·판정은 Integration 07을 따른다.
- 실제 시작 SHA와 테스트 수치는 착수 뒤 해당 개발 기록에만 기록한다.
- 4주차 기준은 실제 DB 3,269건·Migration `20260810_0006`·지역정책 109건과
  검색 Browser 인수를 통과했다. 이 수치는 W5-G0에서 재확인할 기준값이며,
  Data 06 적재 뒤의 기대 최종 건수를 미리 고정하지 않는다.
- `2026-08-17` DTL5-0에서 같은 Migration·DB 기준, 전용 PostgreSQL 테스트,
  local Backend·Frontend readiness와 Chromium 실행을 확인해 `W5-G0_PASS`로
  판정했다. 상세 수치는 Integration 07 개발 기록에 둔다.

## 실행 작업 단위

주차 작업 ID는 일정·인계 추적용이며 각 Forest Slice를 대체하지 않는다.

| 작업 ID | 주 담당 | Forest Slice | 종료 산출물 | 다음 단계 |
| --- | --- | --- | --- | --- |
| `W5-0` | Team Leader | Integration 07 A0 | 시작 SHA·Migration·DB 기준·actual API mode·명령·증거 양식 | 병렬 작업 개방 |
| `W5-D1` | Data | Data 06 SOP0~SOP2 | 정제 inventory·중복 감사·Source preflight와 `SOP-G2` 판정 | `W5-D2` |
| `W5-B1` | Backend | 안정화 회귀 | PostgreSQL·Migration·transaction·권한·API 결함 목록 | `W5-I1` 또는 수정 |
| `W5-F1` | Frontend | 안정화 회귀 | actual API·Browser·오류·접근성·반응형 결함 목록 | `W5-I1` 또는 수정 |
| `W5-D2` | Data | Data 06 SOP3 | Source Adapter·판정 fixture·offline replay와 `SOP-G3` 판정 | `W5-D3` |
| `W5-D3` | Data | Data 06 SOP4~SOP5 | 승인 5개 Source actual·신규 1개 이상·비accepted 무적재·DB/API/Browser·`SOP-G5` | `W5-I1` |
| `W5-I1` | Team Leader | Integration 07 A2 | Data 06 포함 전체 actual E2E와 `W5-G1` 판정 | 독립 검증 |
| `W5-Q1` | 사용성·QA | Integration 07 A2 | 독립 시나리오 결과·결함 심각도·재현 조건 | 영역별 수정 |
| `W5-FIX` | Data·Backend·Frontend | 담당 Forest | 승인 결함 수정과 담당자 자체 재검증 | 독립 재검증 |
| `W5-I2` | Team Leader | Integration 07 A3 | 수정본 독립 재검증·문서 대조·`W5-G2` 판정 | Release 후보 |

## 범위

### Data

- Data 06 SOP0~SOP5 후보 정제·중복 감사·Source 승인·Adapter·actual 구현
- Data 03~05와 완료된 Data 06 범위의 수집·replay·정규화·중복·품질 전체 회귀
- 성공·실패·중단·checkpoint 재개와 동일 Raw `unchanged` 검증
- partial·invalid·마감·중복 후보와 provenance 정확성 확인
- Data 05 비차단 지역의 open 고유 정책 검색 노출과 0건 근거 확인
- Data 06 승인 Source의 신규 정책과 온통청년·복지로·Data 05 중복 제외 확인
- accepted projection 재동기화의 row 유지·prune·반복 실행 안전성 확인

### Backend

- 전체 단위·PostgreSQL 통합 회귀와 주요 API 안정성·성능 확인
- Migration upgrade·rollback, transaction rollback과 기존 데이터 유지 검증
- 정책 검색·상세·추천, 관리자 인증·권한·실행 이력·수동 실행 검증
- 관리자 정책 데이터·영속 로그 조회와 archive 삭제 보호·감사 확인
- partial·invalid 데이터와 `401`·`403`·`404`·`409`·`422`·`500` 오류 계약 검증
- Data 05·06 accepted 결과의 검색·상세 API 노출 대조

### Frontend

- 검색·목록·상세·추천의 actual API 회귀
- 제외 조건·필요 서류·시설 문의처·추가 확인 필요 표시 검증
- 지역 검색, 0건 설명, 즐겨찾기·D-Day·웹 알림·`.ics` 검증
- 관리자 인증·실행 이력·수동 실행·정책 데이터·로그 화면 검증
- loading·empty·partial·error·권한 부족·세션 만료 UX 개선
- 키보드·접근성·모바일·반응형과 주요 지원 Browser 회귀

### Team Leader - Integration

- 공통 시작 SHA·Migration·snapshot·actual API mode 고정
- Data → PostgreSQL → Backend API → Frontend Browser E2E 주관
- 영역 간 계약 충돌과 결함의 담당·심각도·재검증 조건 확정
- 사용성 리뷰와 QA 결과의 릴리스 차단 여부 triage
- 수정본 근거, 문서·CHANGELOG와 Release 체크리스트 대조
- `pass`, `conditional`, `blocked` Release 2 판정

### 사용성 리뷰어·QA·보고서

- 사용성 리뷰어는 팀 외 사용자 관점의 사용자·관리자 시나리오를 수행한다.
- QA는 전체 기능·통합·회귀·경계·실패 탐색 테스트와 수정본 재검증을 수행한다.
- 보고서 담당은 실행한 리뷰·QA·수정·재검증 근거와 미실행 항목을 구분해
  Release 2 결과로 연결한다.

## 범위 밖

- Data 06 외 4주차 기본 기능의 미완료분을 5주차 추가 기능으로 재분류하는 작업
- 승인되지 않은 신규 기능과 계약 확장
- Production Dockerfile·Compose·Nginx·CI와 clean-room 배포
- 이메일 발송이나 Google Calendar 직접 연동
- QA·사용성 검증 없이 담당자 자체 테스트만으로 Release 2를 승인하는 작업

배포 파이프라인과 `v1.0.0` clean-room 검증은 6주차 범위다.

## 실행 원칙

1. 기능 확장보다 결함 수정·UI/UX 최적화·검증을 우선한다.
2. Mock·Seed 성공을 실제 PostgreSQL·API·Browser 통과로 대신하지 않는다.
3. 최초 실패, 원인, 수정과 재검증 결과를 함께 보존한다.
4. 실제 최신 웹 관찰과 고정 snapshot 회귀를 서로 다른 증거로 관리한다.
5. Data·Backend·Frontend는 자기 영역을 수정하고 Team Leader가 계약과 E2E를
   조정한다.
6. 사용성 리뷰와 QA는 구현자의 자체 검증과 구분한다.
7. Runtime Raw·DB 파일·인증정보·개인정보를 Git에 포함하지 않는다.

## 선행 관계와 Critical Path

```text
4주차 DTL4-5·W4-G4 완료·develop 병합
  → W5-G0 통합 기준선 고정
  ├→ Data 06 SOP0~SOP5 구현·actual·Forest Gate
  ├→ Backend 안정화
  └→ Frontend 안정화
  → W5-G1 기능 동결·Data 06 포함 actual E2E
  → 사용성 리뷰·QA
  → 영역별 결함 수정
  → 수정본 독립 재검증
  → W5-G2 Release 2 Gate
  → main PR·v0.5.0 tag 후보
```

영역별 안정화는 공통 기준선 뒤 병렬로 진행할 수 있다. 사용성 리뷰와 QA는
담당자 자체 회귀와 actual E2E가 끝난 뒤 시작한다.

## 권장 5일 배치

| 일차 | Data | Backend | Frontend | Team Leader·독립 검증 |
| --- | --- | --- | --- | --- |
| 1일차 | `W5-D1` SOP0~SOP2 | `W5-B1` Migration·DB·API 기준 | `W5-F1` actual API·Browser 기준 | `W5-0`, W5-G0 판정·증거 양식 고정 |
| 2일차 | `W5-D2` SOP3 Adapter fixture | `W5-B1` 권한·transaction·오류 회귀 | `W5-F1` 사용자·관리자 오류 UX 회귀 | Source Gate·영역별 결함 triage |
| 3일차 | `W5-D3` SOP4~SOP5 actual·Forest 판정 | Data 06 DB·API와 전체 actual 대조 | Data 06 포함 Browser·접근성·반응형 | `W5-I1`, W5-G1 기능 동결 판정 |
| 4일차 | `W5-FIX` 승인 결함 수정·재검증 | `W5-FIX` 승인 결함 수정·재검증 | `W5-FIX` 결함·UX 수정·재검증 | `W5-Q1` 사용성·QA와 재현 근거 |
| 5일차 | 수정본 전체 회귀 | 수정본 전체 회귀 | 수정본 actual Browser 회귀 | 독립 재검증·`W5-I2`, W5-G2 판정 |

## 단계별 Gate

### W5-G0 - 통합 기준선

- Data 06을 제외한 4주차 필수 결과와 Data 05가 `develop`에 병합됨
- 시작 SHA, Migration head, snapshot과 actual API mode가 고정됨
- 영역별 테스트 명령, 지원 환경과 증거 양식이 확정됨
- 기본 기능 미완료가 0건임

현재 Git·4주차 근거는 이 Gate의 입력을 충족하지만, 5주차 작업 환경에서
Migration·DB 기준·actual API mode와 명령을 다시 확인한 뒤에만
`W5-G0_PASS`를 기록한다.

하나라도 충족하지 못하면 `W5-G0_BLOCKED`로 기록하고 4주차 완료 조건으로
돌려보낸다.

### W5-G1 - actual E2E와 독립 검증 준비

- Data 06 `SOP-G5`와 Forest 완료 기준이 통과함
- Data·Backend·Frontend 담당자 전체 회귀가 통과함
- 사용자·관리자 핵심 흐름이 실제 PostgreSQL·API·Browser에서 동작함
- Data 05·06 정책의 lineage와 검색 노출이 대조됨
- 리뷰어·QA에 넘길 알려진 제약과 테스트 환경이 기록됨

`2026-08-17` Data 06 브랜치에서 Migration `20260810_0006`, 실제 정책
3,270건·지역 109건·KOSAF 1건과 전 영역 사전 회귀를 확인했다. 다만 Backend
`W5-B1`과 Frontend `W5-F1` 담당 산출물을 통합하지 않은 결과이므로
`W5-G1_PENDING`을 유지한다. 두 담당 결과를 인수·병합한 뒤 `W5-I1`을 다시
실행하며, `W5-G1_PASS` 전에는 `W5-Q1`을 시작하지 않는다.

### W5-G2 - Release 2 Gate

- 리뷰어 시나리오와 QA 전체 검증이 수행됨
- 릴리스 차단 결함 수정본이 같은 시나리오로 재검증됨
- 낮은 위험 미해결 사항이 릴리스 노트에 기록됨
- 핵심 단위·통합·PostgreSQL·Frontend·Browser·문서 검증이 통과함
- 문서·CHANGELOG·실제 기능과 검증 근거가 일치함

판정은 `W5-G2_PASS`, `W5-G2_CONDITIONAL`, `W5-G2_BLOCKED` 중 하나로
기록한다. `PASS`인 `develop`만 `main` PR과 `v0.5.0` tag 후보가 된다.

## 역할별 산출물

| 역할 | 산출물 |
| --- | --- |
| Data | Data 06 구현·Forest 판정, 수집·replay·품질 회귀와 Data 05·06 actual 근거 |
| Backend | PostgreSQL·Migration·transaction·API·권한 회귀와 결함 수정 근거 |
| Frontend | 사용자·관리자 actual Browser, 접근성·반응형·오류 UX 근거 |
| Team Leader | 시작 기준선, E2E 결과, 결함 triage, Release 2 Gate 결정 |
| 사용성 리뷰어 | 사용자·관리자 시나리오 관찰과 재확인 결과 |
| QA | 전체 기능·통합·회귀·탐색 테스트와 수정본 재검증 결과 |
| 보고서 | Release 2 근거 목록과 문서·화면·테스트 대조 |

## 증거와 결함 기록 규칙

- Data 06 구현 결과는 착수 시 생성하는 Data 06 development note 한 곳에
  Source별 `implemented`·`blocked`·`rejected`, accepted·duplicate·review·
  closed·failed 수치와 replay 결과를 기록한다.
- Integration 07 결과는 A2 착수 시 생성하는 Integration development note에
  시작 SHA, W5-G1·G2, E2E, 독립 검증과 릴리스 후보 SHA를 기록한다.
- 결함은 `ID`, 발견 역할, 시나리오, 심각도, 재현 조건, 기대·실제 결과,
  수정 담당, 수정 SHA, 자체 재검증, 독립 재검증 상태를 가진다.
- 인증 우회·비밀 노출·데이터 손실·Migration 실패·핵심 actual E2E 실패와
  Data 06 재승인 기준(승인 5개 actual·신규 1개 이상·비accepted 무적재·Browser)
  미달은 Release blocker다.
- 낮은 위험의 문구·비차단 UX 문제만 알려진 제약 후보가 될 수 있으며,
  Team Leader가 근거 없이 `conditional`로 낮추지 않는다.

## 테스트와 검증

- Data 전체 단위·통합·Runtime replay·수집 재개 검증
- Backend 전체 단위·PostgreSQL·Migration·transaction·권한 검증
- Frontend unit·lint·build·Browser·접근성·반응형 검증
- 실제 웹 Source → Raw → 결정 → DB → API → Browser E2E
- Release 1 golden 검색과 기존 사용자·관리자 회귀
- `python scripts/validate_docs.py`
- 증거 JSON parse와 `git diff --check`

정확한 명령과 실행 수치는 각 Forest 설정에서 확인하고 실제 실행 결과만
development notes에 기록한다.

## 위험과 결정 필요 사항

- 외부 Source의 최신 상태 변화가 고정 snapshot과 다를 수 있다. 데이터 drift와
  코드 회귀를 분리해 판정한다.
- 리뷰·QA가 늦어지면 담당자 자체 검증만으로 Release 2를 통과시키지 않는다.
- 영역별 변경이 공통 계약을 바꾸면 단독 수정하지 않고 영향 담당자와 다시
  승인한다.
- Integration 07의 cross-area 작업 브랜치는 착수 시점의 `develop` 상태와
  브랜치 전략을 확인한 뒤 하나의 통합 목표 단위로 정한다.

## 인계사항 발생 조건

- Data 결과와 DB row 또는 API projection이 일치하지 않음
- API 오류·권한·null 계약과 Frontend 소비가 충돌함
- 리뷰·QA에서 재현 가능한 릴리스 차단 결함이 발견됨
- Migration·transaction·재실행에서 데이터 손실이나 중복 위험이 발견됨
- 문서 완료 상태와 실제 구현·테스트 결과가 다름

미래 위험이나 예정된 QA 자체는 활성 인계사항으로 등록하지 않는다.

## 완료 체크리스트

- [x] `W5-G0` 통합 기준선 통과
- [ ] Data 06 SOP0~SOP5·SOP-G5와 Forest 완료 판정
- [ ] Data 수집·품질·Data 05·06 actual 회귀 통과
- [ ] Backend PostgreSQL·API·권한·transaction 회귀 통과
- [ ] Frontend 사용자·관리자·오류·접근성·반응형 회귀 통과
- [ ] `W5-G1` 실제 DB → API → Browser E2E 통과
- [ ] 팀 외 사용성 리뷰 수행 및 승인 피드백 반영
- [ ] QA 전체 검증과 릴리스 차단 결함 수정본 재검증
- [ ] Release 2 문서·CHANGELOG·알려진 제약 대조
- [ ] `python scripts/validate_docs.py`와 저장소 전체 관련 회귀 통과
- [ ] `W5-G2` Release 2 판정 기록
- [ ] `PASS`일 때만 `main` PR과 `v0.5.0` tag 후보 지정

## 관련 문서

- [주차별 실행 계획](../develop_plan/weekly_delivery_plan.md)
- [Release와 Milestone 계획](../develop_plan/release_roadmap.md)
- [전체 Forest 로드맵](../develop_plan/forest_roadmap.md)
- [4주차 상세 실행 계획](week_04_v0_5_0.md)
- [5주차 Data·Team Leader 실행 계획](week_05_data_team_leader.md)
- [Integration 07 Release 2 Feature Acceptance](../develop_plan/integration/07_release_2_feature_acceptance.md)
- [역할과 책임](../../governance/role_assignment.md)

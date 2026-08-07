# 주차별 실행 계획

## 문서 정보

- 상태: approved
- 기준일: 2026-08-07
- 범위: 1~6주차 실행 순서
- 역할: Release와 Forest 계획을 주차별 인계 순서로 변환

주차는 고정 달력일이 아니라 작업 순서를 나타낸다. 릴리스 완료 조건을
충족하지 못하면 tag를 미루고 해당 주차의 검증을 이어간다. 실행하지 않은
항목을 일정상 완료로 처리하지 않는다.

## 역할 기준

- Data, Backend와 Frontend 담당은 각 영역 구현과 계약·테스트를 책임진다.
- Team Leader는 Integration과 Deploy를 담당하고 릴리스 게이트를 관리한다.
- 보고서 담당은 주차별 근거를 누적해 최종보고서와 제출 자료로 연결한다.
- 사용성 리뷰어는 팀 외 사용자 관점의 이해도와 불편을 검증한다.
- QA 담당은 `v0.5.0` 기능·회귀와 `v1.0.0` 설치·배포·복구 검증을 주도한다.

역할은 인원 수와 같지 않다. 한 사람이 여러 역할을 맡을 수 있지만 자기
구현만으로 사용성·QA·릴리스 통과를 모두 승인하지 않는다. 상세 원칙은
[역할과 책임](../../governance/role_assignment.md)을 따른다.

## 주차별 역할 배정

| 주차 | Data | Backend | Frontend | Team Leader - Integration·Deploy | 보고서 | 사용성 리뷰어 | QA |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1주차 | Source·Schema·Fixture·Seed 기준선 | FastAPI·DB 기반과 Policy 계약 | React·TypeScript·Mock UI 기반 | 공통 계약·문서 체계와 병렬 개발 조정 | 목표·구조·초기 근거 정리 | 미배정, 사용자 시나리오 후보 검토 | 미배정, 테스트 가능성 검토 |
| 2주차 | 제한 수집·Runtime 재처리 경계 | Migration·Importer·Policy API·안전성 | 실제 API 연결·Browser 회귀 | Seed/Runtime → DB → API → UI 통합 확인 | 완료 Forest·테스트·화면 근거 누적 | Release 1 검색 문장 후보 제공 가능 | 통합 기준과 회귀 항목 초안 |
| 3주차 | 실데이터 근거·Source 검색 필드·지역 정규화·DB bootstrap·품질 보고 | 지역 관계·search projection 공동 기반, 자연어 해석·서버 검색·성능 | 데이터·API 소비 검토, 자연어 조건·검색 이유·미확인 조건 UI | 검색 데이터 기반 Gate, 실제 데이터 E2E, golden query와 `v0.1.0` 결정 | Release 1 데이터·검색·검증 근거 정리 | golden query 결과의 이해도 사전 확인 | Release 1 핵심 검색 smoke와 결함 기록 |
| 4주차 | 반복 수집·중복·수정·품질 운영 | 추천·사용자 기능·관리자 인증·실행 API | 추천·즐겨찾기·알림·캘린더·관리자 UI | 사용자·관리자 계약 조정과 중간 통합 | 4주차 수행 없음 | 4주차 수행 없음 | 4주차 수행 없음 |
| 5주차 | 실패·partial·invalid·품질 결함 재현과 수정 지원 | API·DB·권한·transaction 결함 수정 | UX·접근성·반응형·오류 화면 수정 | 기능 구현·통합 종료, 결함 triage와 `v0.5.0` 결정 | 기능 연결 종료 뒤 리뷰·QA·수정 근거 정리 | 기능 연결 종료 뒤 실제 사용자 시나리오 수행·재확인 | 기능 연결 종료 뒤 전체 기능·통합·회귀·탐색 테스트와 수정본 재검증 |
| 6주차 | 초기 실데이터 절차·Source 라이선스·복구 자료 | Production image·migration·health·로그 지원 | Production build·Nginx·배포 UI 회귀 | Docker·Compose·Nginx·CI, clean-room과 `v1.0.0` 결정 | README·LICENSE·SBOM·최종보고서·시연·제출 정리 | 새 환경 실행·최종 사용성 확인 | clean-room 설치·build·재시작·Volume·보안·복구 검증 |

## 전체 흐름

```text
1주차 기반 계약
  → 2주차 DB·API·UI 통합과 안전성
  → 3주차 검색 데이터 기반·실데이터 검색 MVP
  → v0.1.0
  → 4주차 사용자·관리자 기능
  → 5주차 전체 기능 통합·리뷰어 안정화
  → v0.5.0
  → 6주차 배포·clean-room·최종 정리
  → v1.0.0
```

## 1주차 - 기반 계약과 3개 영역 개발 시작

### 상태

completed

### 실제 완료 기준선

- 문서·거버넌스와 역할 경계
- 온통청년·복지로 Source 조사와 제한 실제 호출
- Raw·Normalized Schema, Fixture와 canonical Seed
- FastAPI·PostgreSQL·Migration 기반
- React·TypeScript 사용자 정책 화면 기반
- Data·Backend·Frontend 공동 계약 검토

세부 증거는 완료된 Docs System, Data Pipeline, Backend Baseline과 Policy
Discovery 개발 기록을 따른다.

## 2주차 - PostgreSQL 통합과 실행 안전성

### 상태

completed

### 실제 완료 기준선

- Policy ORM·Migration·upsert·transaction
- canonical Seed → PostgreSQL → Policy API 통합
- Runtime Raw 재처리와 최소 CollectionRun 이력
- Frontend 실제 Policy API 연결과 Browser 검증
- Policy timestamp와 SQL logging 안전화
- React Router advisory 대응과 회귀 검증

### 남은 차이

- Data 02 DT1에서 `runtime/raw` 실제 표본 25개를 수집했지만 Runtime DB에는
  아직 적재하지 않았다.
- 전체 또는 릴리스 범위 수집과 자동 주기 적재는 미구현이다.
- Backend keyword·age 검색은 미구현이며 Frontend 검색은 client-only다.

이 차이는 3주차 `v0.1.0` 차단 조건으로 이동한다.

## 3주차 - 실데이터 정책 검색과 Release 1

상세 실행 순서, 병렬 작업과 Gate는
[3주차 상세 계획](../weekly_plan/week_03_release_1.md)을 따른다.

### 상태

completed (`Gate G4 pass`, `develop` 병합 `4629a61`)

### 우선순위

`v0.1.0` 완료 조건 외의 관리자·추천 기능을 먼저 추가하지 않는다.

### Data

- 완료된 Integration 03 검색 데이터 기반으로 DT2 actual profile·Data 권고를
  Backend·Frontend 초안과 공동 검토하고 Gate G1을 지원한다.
- Source별 pagination, 할당량과 릴리스 수집 범위를 확정한다.
- 실제 정책 Raw를 수집하고 정규화·검증·PostgreSQL에 초기 적재한다.
- 수동 재수집·재처리의 idempotency와 실패 복구를 검증한다.
- 실제 데이터의 상태·지역·연령·카테고리·품질 분포를 기록한다.
- 실제 Raw, 인증키와 DB 파일이 Git에 포함되지 않음을 확인한다.

### Backend

- 완료된 Source 중립 search projection, 행정구역·정책 관계, Migration과
  3값 판정 primitive를 기준선으로 사용한다.
- Gate G1을 위해 자연어 request·구조화 조건·검색 이유·미확인 조건 API
  초안을 먼저 Data·Frontend와 검토한다.
- 자연어 원문 `q`를 결정적인 한국어 규칙으로 해석해 지역, 나이,
  주거·월세 등 카테고리와 핵심어를 구조화한다.
- `keyword`, region, age, category, status, pagination과 기본 정렬 계약을
  확정하고 PostgreSQL 검색으로 구현한다.
- 전국·상위 지역·시군구와 연령 조건 미상 정책의 검색 의미를 결정한다.
- 진행 중 정책 우선 노출과 마감·예정 표시를 구분한다.
- 구조화된 해석 조건, 관련도순 결과, 검색 이유와 데이터만으로 판정할 수 없는
  미확인 조건을 응답한다.
- 실제 데이터 분포를 기준으로 query plan과 필요한 index를 검토한다.
- API·DB 단위 및 통합 테스트를 추가한다.

### Frontend

- Gate G1을 위해 Backend request·response와 일치하는 TypeScript query·응답,
  해석 조건·검색 이유·미확인 조건 소비 초안을 먼저 검토한다.
- 자연어 원문을 `q`로 Backend에 전달하고 별도 자연어 parser를 두지 않는다.
- Backend가 반환한 해석 조건을 표시하고 수정 가능하게 한다.
- Backend 검색 결과, 검색 이유, 미확인 조건, pagination과 정렬 결과를
  표시한다.
- 실제 데이터의 목록·상세, 빈 결과, 오류와 partial 상태를 검증한다.

### Team Leader - Integration

- [Policy Search Data Foundation](integration/03_policy_search_data_foundation.md)의
  완료된 ADR·Schema·Migration·소비 호환 Gate를 기준선으로 관리한다.
- DT2 Data 권고, Backend 06·Frontend 04 초안을 대조해 Gate G1을 승인하거나
  차단사항과 다음 담당을 기록한다.
- 실제 DB → FastAPI → React 흐름을 로컬 HTTP와 Browser로 검증한다.
- 다음 golden query의 실제 기대 정책과 이유를 snapshot 기준으로 기록한다.

```text
천안 사는 27살 청년 단기숙소 지원 받을 수 있나?
```

- 기대 정책 identity와 순위·unknown·응답시간 예산을 실행 가능한 acceptance
  계약으로 고정하고 actual snapshot에서 재검증한다.
- 단위·통합·Browser 테스트와 `python scripts/validate_docs.py`를 실행한다.

### 보고서·리뷰어·QA

- 보고서 담당은 실제 데이터 건수·품질 분포, golden query 기대 결과와
  실행한 검증을 Release 1 근거로 정리한다.
- 사용성 리뷰어는 검색 문장, Backend 해석 조건과 결과 이유가 이해되는지 사전
  확인한다.
- QA는 검색 정상·빈 결과·경계값·API 실패 smoke를 수행하고 재현 가능한
  결함만 기록한다.

### 완료

[Release 1 완료 조건](release_roadmap.md#릴리스-완료-조건)을 모두 충족한
`develop`만 `main` 릴리스 PR과 `v0.1.0` tag 후보로 삼는다.

`2026-08-06` Gate G4는 `pass`다. 새 contract hash의 actual 자연어·control은
모두 1건 중 1위·unknown 0·응답시간 예산 이내이고, 신청기간 안전성,
Frontend actual API E2E·Browser와 경량 QA·사용성 리뷰도 통과했다. 보고서와
API 오류 UX 검증은 실행하지 않은 채 `v0.5.0` 후속으로 이관했으며 Release 1
완료 범위에 포함하지 않는다.

Release 1 구현과 근거는 `2026-08-06` `develop`에 병합됐고 PR #15의 `main`
커밋 `2b33ed7`과 `v0.1.0` tag로 발행됐다. `develop`도 같은 커밋으로
fast-forward해 4주차의 공통 시작점으로 사용한다.

## 4주차 - 공식 웹 Source·자격요건과 사용자·관리자 기반

상세 실행 순서, 병렬 작업과 Gate는
[4주차 상세 계획](../weekly_plan/week_04_v0_5_0.md)을 따른다.

### 상태

draft (`W4-G0 계약 승인 대기`)

### 목표

`v0.5.0`의 설계된 기본 기능을 모두 구현한다. 공공 API 보강과 핵심 신청
조건을 추가하되 추천·즐겨찾기·D-Day·내부 알림·`.ics`, 관리자와 품질 기능도
동일한 4주차 필수 범위로 유지하고 API·DB·UI를 끝까지 연결한다.

### Backend·Frontend

- 정책 상세의 필수·제외·우대·서류·확인 필요 구조와 근거
- 핵심 신청 조건 상세 API·UI와 자격 비단정 문구
- 조건 기반 추천, 추천 점수와 추천 이유
- 사용자 조건 저장 경계
- 즐겨찾기와 D-Day
- 웹 내부 알림
- `.ics` 캘린더 생성·등록 UI
- 검색·추천 UX와 모바일·접근성 개선

### Admin

관리자 인증 기준선 뒤 실행·데이터·로그 기능을 병렬로 연결한다.

1. Backend 04 Admin Access Control
2. Backend 05 CollectionRun Admin API
3. Frontend 03 CollectionRun Admin UI
4. Integration 09 Admin Data and Log Console

- 승인 Policy projection의 읽기 전용 CSV형 표·row 상세·pagination·filter
- 구조화 파일 로그, rotation·retention·redaction과 run/request correlation
- 관리자 로그 조회·필터·상세와 회전 archive 삭제·별도 감사 기록

### Data

- 승인된 공식 HTTPS Source 한 곳의 목록·상세 제한 수집과 DB 적재
- 기존 API의 소득·추가 자격·제외·서류 원문 필드 재매핑
- 자격요건 항목의 Source URL·수집 시각·원문 evidence
- 실제 갱신 반복 실행과 실패 데이터 분리
- 중복·수정 감지와 품질 통계
- 관리자 화면에 필요한 안전한 품질 DTO 검토

### 주 후반 통합

- 공식 HTTPS Source → Raw·정규화·DB → 핵심 신청 조건 상세 UI
- 사용자 조건 → 검색·추천 → 이유 → 즐겨찾기·알림·캘린더
- 관리자 인증 → 실행 이력 → 수동 실행 → 상태·오류 확인
- 관리자 인증 → 정책 데이터 표·row 상세 → 오류 로그 검색·archive 삭제 확인

공식 웹 Source·자격요건, 추천, 즐겨찾기·D-Day·내부 알림·`.ics`, 관리자
실행·데이터 표·영속 로그 기본 기능은 모두 W4-G4 필수다. 하나라도 미구현이면
4주차 완료로 판정하지 않고 5주차 기본 기능으로 이월하지 않는다.

### Team Leader와 후속 역할

- Team Leader는 사용자 인증·저장 경계와 관리자 권한 계약을 조정하고 중간
  E2E를 확인한다.
- 보고서 담당·사용성 리뷰어·QA는 4주차에 수행하지 않는다. 5주차 추가 기능,
  오류 수정과 UI/UX 최적화 및 담당자 자체 검증이 끝난 뒤 Integration 07
  A2에서 독립 근거를 만들고 Release 2 Gate 전에 완료한다.

## 5주차 - 추가 기능·오류 수정·UI/UX 최적화와 Release 2

### 기본 기능 기준선

4주차 W4-G4에서 설계한 기본 기능이 모두 구현된 기준선을 사용한다. 기본 기능
미완료분을 5주차 작업으로 넘기지 않는다. 추가 기능은 Release 2 안정성을
해치지 않는 범위에서 승인하고, 오류 수정·UI/UX 최적화와 검증을 우선한다.

### 안정화

- 실제 수집의 성공·실패·중단·재실행 검증
- 파싱 실패, partial·invalid와 중복 후보 처리
- DB migration, transaction, 데이터 유지와 성능 검토
- 검색·추천 정확도와 결과 없음 설명
- 사용자·관리자 API 단위·통합 테스트
- 반응형, 접근성, loading·empty·error와 Browser 회귀

### 리뷰어 테스트

팀 외 리뷰어가 검색, 상세, 추천 이유, 즐겨찾기, 알림, 캘린더와 관리자
시나리오를 수행한다. 관찰 결과를 재현 조건·심각도·기대 결과와 함께 기록하고,
승인한 문제를 수정한 뒤 재검증한다.

### QA 테스트

- 사용자·관리자 전체 기능, API·DB 통합과 기존 검색 회귀를 검증한다.
- 실제 데이터의 마감, 지역, 연령, partial·invalid와 중복 경계를 확인한다.
- 권한, 오류 응답, transaction, migration과 데이터 유지 실패를 탐색한다.
- Browser·접근성·반응형과 주요 지원 환경을 확인한다.
- 결함은 재현 절차, 심각도, 기대 결과와 증거를 남기고 수정본을 재검증한다.

### Team Leader와 보고서

- Team Leader는 리뷰어 의견과 QA 결함을 triage하고 릴리스 차단 여부를
  결정한다.
- 보고서 담당은 리뷰·QA·수정·재검증 근거를 Release 2 결과로 정리한다.

### 완료

[Release 2 완료 조건](release_roadmap.md#릴리스-완료-조건-1)을 모두 충족한
`develop`만 `v0.5.0` 후보로 삼는다.

## 6주차 - 배포 파이프라인과 Final Release

### 기능 원칙

새 사용자 기능은 원칙적으로 동결하고 배포, 재현성, 테스트와 최종 문서에
집중한다. 릴리스 차단 버그와 보안 문제만 수정한다.

### 배포

- Frontend·Backend Production Dockerfile
- PostgreSQL을 포함한 Compose, Volume과 health check
- Nginx 정적 파일과 `/api` reverse proxy
- 환경변수·비밀 분리와 초기 migration·실데이터 bootstrap
- Frontend build, Backend·Data test와 이미지 build CI
- 로그, 장애 확인, 백업·복구와 버전 tag 안내

### Clean-room 검증

- 새 PC 또는 깨끗한 환경에서 clone
- README만 보고 설정·build·migration·초기 적재·실행
- 컨테이너 재시작과 데이터 유지
- 실제 검색·추천·사용자·관리자 시나리오
- 실패 시 로그 확인과 복구

### 최종 정리

- README와 아키텍처
- Data Schema·Source·Collector 가이드
- API와 운영 문서
- LICENSE, SBOM과 CHANGELOG
- 최종보고서, 시연 스크립트·영상과 제출 체크리스트

### 역할별 최종 검증

- Team Leader는 Integration·Deploy 담당으로 전체 배포 구성, CI,
  clean-room 결과와 남은 위험을 확인한다.
- 보고서 담당은 코드·문서·테스트 결과와 최종 제출 자료의 버전을 대조한다.
- 사용성 리뷰어는 새 환경에서 핵심 사용자 흐름과 실행 안내의 이해도를
  확인한다.
- QA는 설치, build, migration, bootstrap, 컨테이너 재시작, Volume, 로그,
  권한·비밀, 실패 복구와 전체 회귀를 검증한다.

### 완료

[Final Release 완료 조건](release_roadmap.md#릴리스-완료-조건-2)을 모두
충족한 `main` 커밋을 `v1.0.0` tag 후보로 삼는다.

## 일정 변경 규칙

- 3주차에 실데이터나 golden query가 실패하면 `v0.1.0`을 미루고 해당
  Forest를 계속한다. 관리자 기능으로 완료 범위를 대체하지 않는다.
- 4주차 기능의 인증·Schema·DB 계약이 불명확하면 구현 전에 별도 Forest
  계획과 공동 검토를 추가한다.
- 5주차 리뷰어 피드백 중 릴리스 차단 문제는 수정 후 재검증하고, 낮은 위험의
  후속 개선은 근거와 함께 다음 계획으로 이동할 수 있다.
- 6주차 clean-room 실행이 실패하면 문서만 수정해 통과로 기록하지 않고
  구성과 명령을 실제로 재검증한다.

## 관련 문서

- [Release와 Milestone 계획](release_roadmap.md)
- [전체 Forest 로드맵](forest_roadmap.md)
- [검색 계약 Gate G1 인수인계](../weekly_plan/week_03_search_contract_handoff.md)
- [4주차 상세 실행 계획](../weekly_plan/week_04_v0_5_0.md)
- [개발 계획 안내](README.md)
- [문서화 정책](../../governance/documentation_policy.md)

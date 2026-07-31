# 주차별 실행 계획

## 문서 정보

- 상태: approved
- 기준일: 2026-07-31
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
| 3주차 | 실데이터 릴리스 범위 수집·DB bootstrap·품질 보고 | 서버 keyword·region·age 검색과 성능 | 자연어 조건 추출·검색 UI·pagination | 실제 데이터 E2E, golden query와 `v0.1.0` 결정 | Release 1 데이터·검색·검증 근거 정리 | golden query 결과의 이해도 사전 확인 | Release 1 핵심 검색 smoke와 결함 기록 |
| 4주차 | 반복 수집·중복·수정·품질 운영 | 추천·사용자 기능·관리자 인증·실행 API | 추천·즐겨찾기·알림·캘린더·관리자 UI | 사용자·관리자 계약 조정과 중간 통합 | 기능별 설계 결정·화면·테스트 근거 정리 | 5주차 사용자 시나리오와 평가 항목 준비 | `v0.5.0` 테스트 계획·데이터·환경 준비 |
| 5주차 | 실패·partial·invalid·품질 결함 재현과 수정 지원 | API·DB·권한·transaction 결함 수정 | UX·접근성·반응형·오류 화면 수정 | 기능 동결, 결함 triage와 `v0.5.0` 결정 | 리뷰·QA 결과와 수정 근거를 Release 2 자료에 반영 | 실제 사용자 시나리오 수행·재확인 | 전체 기능·통합·회귀·탐색 테스트와 수정본 재검증 |
| 6주차 | 초기 실데이터 절차·Source 라이선스·복구 자료 | Production image·migration·health·로그 지원 | Production build·Nginx·배포 UI 회귀 | Docker·Compose·Nginx·CI, clean-room과 `v1.0.0` 결정 | README·LICENSE·SBOM·최종보고서·시연·제출 정리 | 새 환경 실행·최종 사용성 확인 | clean-room 설치·build·재시작·Volume·보안·복구 검증 |

## 전체 흐름

```text
1주차 기반 계약
  → 2주차 DB·API·UI 통합과 안전성
  → 3주차 실데이터 검색 MVP
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

- 이 PC에는 운영 `runtime/raw`가 없어 실제 Runtime DB 적재 smoke를 성공으로
  기록하지 않았다.
- 전체 또는 릴리스 범위 수집과 자동 주기 적재는 미구현이다.
- Backend keyword·age 검색은 미구현이며 Frontend 검색은 client-only다.

이 차이는 3주차 `v0.1.0` 차단 조건으로 이동한다.

## 3주차 - 실데이터 정책 검색과 Release 1

### 우선순위

`v0.1.0` 완료 조건 외의 관리자·추천 기능을 먼저 추가하지 않는다.

### Data

- Source별 pagination, 할당량과 릴리스 수집 범위를 확정한다.
- 실제 정책 Raw를 수집하고 정규화·검증·PostgreSQL에 초기 적재한다.
- 수동 재수집·재처리의 idempotency와 실패 복구를 검증한다.
- 실제 데이터의 상태·지역·연령·카테고리·품질 분포를 기록한다.
- 실제 Raw, 인증키와 DB 파일이 Git에 포함되지 않음을 확인한다.

### Backend

- `keyword`, region, age, category, status, pagination과 기본 정렬 계약을
  확정하고 구현한다.
- 전국·상위 지역·시군구와 연령 조건 미상 정책의 검색 의미를 결정한다.
- 진행 중 정책 우선 노출과 마감·예정 표시를 구분한다.
- 실제 데이터 분포를 기준으로 query plan과 필요한 index를 검토한다.
- API·DB 단위 및 통합 테스트를 추가한다.

### Frontend

- 자연어에서 지역, 나이, 주거·월세 등 기본 조건을 결정적으로 추출한다.
- 추출 조건을 사용자에게 표시하고 수정 가능하게 한다.
- Backend 검색 query, pagination과 정렬 결과를 사용한다.
- 실제 데이터의 목록·상세, 빈 결과, 오류와 partial 상태를 검증한다.

### Team Leader - Integration

- 실제 DB → FastAPI → React 흐름을 로컬 HTTP와 Browser로 검증한다.
- 다음 golden query의 실제 기대 정책과 이유를 snapshot 기준으로 기록한다.

```text
천안 사는 27살 청년 월세 지원 받을 수 있나?
```

- 지원 Source에 기대 정책이 없으면 Source 추가 또는 릴리스 범위를 결정한다.
- 단위·통합·Browser 테스트와 `python scripts/validate_docs.py`를 실행한다.

### 보고서·리뷰어·QA

- 보고서 담당은 실제 데이터 건수·품질 분포, golden query 기대 결과와
  실행한 검증을 Release 1 근거로 정리한다.
- 사용성 리뷰어는 검색 문장, 추출 조건과 결과 이유가 이해되는지 사전
  확인한다.
- QA는 검색 정상·빈 결과·경계값·API 실패 smoke를 수행하고 재현 가능한
  결함만 기록한다.

### 완료

[Release 1 완료 조건](release_roadmap.md#릴리스-완료-조건)을 모두 충족한
`develop`만 `main` 릴리스 PR과 `v0.1.0` tag 후보로 삼는다.

## 4주차 - 사용자·관리자 핵심 기능

### 목표

`v0.5.0`의 기능 완성을 시작하되, API·DB·UI 계약을 기능별로 끝까지 연결한다.

### Backend·Frontend

- 조건 기반 추천, 추천 점수와 추천 이유
- 사용자 조건 저장 경계
- 즐겨찾기와 D-Day
- 웹 내부 알림
- `.ics` 캘린더 생성·등록 UI
- 검색·추천 UX와 모바일·접근성 개선

### Admin

다음 기존 Forest 순서를 유지한다.

1. Backend 04 Admin Access Control
2. Backend 05 CollectionRun Admin API
3. Frontend 03 CollectionRun Admin UI

### Data

- 실제 갱신 반복 실행과 실패 데이터 분리
- 중복·수정 감지와 품질 통계
- 관리자 화면에 필요한 안전한 품질 DTO 검토

### 주 후반 통합

- 사용자 조건 → 검색·추천 → 이유 → 즐겨찾기·알림·캘린더
- 관리자 인증 → 실행 이력 → 수동 실행 → 상태·오류 확인

### Team Leader·보고서·리뷰어·QA

- Team Leader는 사용자 인증·저장 경계와 관리자 권한 계약을 조정하고 중간
  E2E를 확인한다.
- 보고서 담당은 기능별 결정, 화면과 실제 테스트 근거를 누적한다.
- 사용성 리뷰어는 5주차에 수행할 독립 시나리오와 질문을 준비한다.
- QA는 요구사항별 테스트 항목, 실제·경계 데이터와 지원 환경을 준비한다.

## 5주차 - 전체 기능 통합, 리뷰어 테스트와 Release 2

### 기능 동결

승인되지 않은 새 기능 추가보다 검증과 오류 수정에 집중한다.

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
- [개발 계획 안내](README.md)
- [문서화 정책](../../governance/documentation_policy.md)

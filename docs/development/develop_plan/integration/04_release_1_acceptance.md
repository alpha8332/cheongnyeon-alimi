# Integration 04 Release 1 Acceptance Forest 개발 계획

## 계획 정보

- 번호: Integration 04
- 상태: in-progress
- 대상 Release: `v0.1.0`
- 담당 영역: Team Leader - Integration
- 작업 브랜치: `feature/data/release-dataset-bootstrap`
- 현재 Slice: IA2 completed (`Gate G4 blocked`)
- 개발 기록:
  [Release 1 Acceptance 개발 기록](../../development_notes/integration/release_1_acceptance.md)

## 목적

Data 02의 실제 정책 snapshot, Backend 06 검색 API와 Frontend 04 검색 UI를
하나의 PostgreSQL → HTTP → Browser 흐름으로 연결하고 Release 1 후보 여부를
독립 검증 근거와 함께 판정한다.

## 범위

- Gate G2 Data·Backend·Frontend 준비 증거와 공통 계약 대조
- 승인 범위 snapshot의 로컬 복구·적재와 멱등 재실행
- 실제 PostgreSQL 대상 검색 HTTP, pagination·validation·빈 결과 검증
- Frontend 실제 API 모드의 검색·상세·loading·empty·error·partial 검증
- Browser console과 Backend 요청 로그 확인
- golden query 결과, 검색 정확도 제약과 독립 QA·리뷰어·보고서 근거 대조

## 범위 밖

- 새로운 Source 추가 또는 현재 호출 예산 확대
- 검색 의미·정렬 계약의 임의 변경
- 추천, 즐겨찾기, 알림, 관리자와 배포 기능
- QA·사용성 리뷰어·보고서 담당을 Team Leader가 대신 승인하는 작업

## 선행 조건

- Data 02 DT3·DT4와 실제 snapshot 품질 근거 완료
- Backend 06 검색 endpoint와 자동 테스트 준비
- Frontend 04 Mock 소비 테스트와 실제 API Client 준비
- Runtime DB와 `_test` DB를 분리한 PostgreSQL 인증 환경

## 공통 설계 원칙

- 검색 요청은 PostgreSQL만 조회하고 외부 Source API를 호출하지 않는다.
- 다른 PC의 Git 제외 Raw·DB 상태는 자동 전달됐다고 가정하지 않고 이 PC에서
  manifest·DB row·Migration을 확인한다.
- Source 시점 차이는 이전 수치에 맞추지 않고 새 snapshot의 실제 분포로
  기록한다.
- 승인된 API·Schema·unknown·partial 의미를 바꾸는 결함은 임의 수정하지 않고
  담당과 재개 조건을 인계한다.
- 초기 실패, skip과 미실행 검증을 최종 성공으로 덮어 기록하지 않는다.

## Slice 계획

### IA0 - 통합 기준선과 실행 환경

- 상태: completed (`2026-08-06`)
- 목적: FE·BE 결과를 병합하고 로컬 Raw·DB·의존성 차이를 확인한다.
- 완료 기준: 비커밋 병합 상태, PostgreSQL 인증, 실제 API 모드와 검증 명령이
  재현 가능하게 확인됨

### IA1 - DT5 Gate G2·G3

- 상태: completed (`2026-08-06`)
- 목적: 실제 snapshot을 DB → API → UI로 연결하고 통합 결함을 수정·재검증한다.
- 완료 기준:
  - Runtime DB의 실제 snapshot과 projection을 검색함
  - Backend PostgreSQL 전체 테스트와 검색 HTTP가 통과함
  - Frontend 단위·build·lint·실제 API E2E와 Browser console이 통과함
  - pagination, 빈 결과, 422, 503, partial과 상세 이동을 검증함

### IA2 - DT6 golden query와 Release 1 판정

- 상태: completed (`2026-08-06`, `Gate G4 blocked`)
- 선행 조건: IA1, QA smoke, 사용성 리뷰어 확인과 보고서 근거
- 완료 기준:
  - golden query의 실제 정책·근거·제약과 검색 정확도를 승인함
  - 릴리스 차단 결함을 수정·재검증하거나 재개 조건과 함께 `blocked`로 기록함
  - Gate G4를 `pass`, `conditional` 또는 `blocked`로 근거와 함께 기록함

실행 결과 actual snapshot에는 천안·27세·주거·월세를 모두 확정할 정책이
없다. exact golden query는 48건을 반환하지만 첫 후보의 지역·연령은
`unknown`이고, `월세`를 단일 필수어로 제한하면 3건 모두 `partial`이며
지역·연령이 `unknown`이다. QA·사용성 리뷰어·보고서의 독립 근거도 아직
없으므로 `v0.1.0` 후보로 승인하지 않는다.

## 검증 계획

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
$env:TEST_DATABASE_URL = '<dedicated-postgresql-test-url>'
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q
npm.cmd test
npm.cmd run build
npm.cmd run lint
$env:VITE_USE_MOCK = 'false'
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm.cmd run test:e2e
.\.venv\Scripts\python.exe -B scripts\validate_docs.py
git diff --check
```

## Forest 완료 기준

- IA1 Gate G2·G3와 IA2 Gate G4가 모두 실제 실행 증거를 가짐
- Data·Backend·Frontend 코드, 계약 문서와 실행 결과가 일치함
- QA·리뷰어·보고서의 독립 근거와 남은 위험이 기록됨
- Release 1 차단 결함이 없거나 판정이 명시적으로 `blocked`임

## 위험과 미확정 사항

- `2026-08-06` snapshot은 이전 DT4보다 온통청년 3건이 줄어 외부 데이터가
  시간에 따라 변함을 재확인했다.
- golden query의 confirmed 정책은 여전히 0건이다. 첫 후보의 지원 내용에는
  `2026-03-30 ~ 2026-05-29` 신청기간이 있으나 구조화 신청 기간·상태는
  `null`이라 최신 수집만으로 신청 가능성을 설명할 수 없다.
- 현재 검색은 여러 미해석 term 중 하나만 일치해도 후보가 될 수 있어 일반적인
  `지원` term이 결과를 넓힌다. term 결합·score 의미 변경은 Gate G1 계약 보완
  결정이 필요하므로 IA1에서 임의 변경하지 않는다.
- QA·사용성 리뷰어·보고서 근거가 아직 없다. Gate G4는 `blocked`로
  판정했으며, 차단사항 해소·독립 재검증 전에는 재판정하지 않는다.

## 관련 문서

- [3주차 Data·Team Leader 실행 계획](../../weekly_plan/week_03_data_team_leader.md)
- [3주차 전체 상세 계획](../../weekly_plan/week_03_release_1.md)
- [Release Dataset Bootstrap](../data/02_release_dataset_bootstrap.md)
- [Backend Policy Search](../backend/06_policy_search.md)
- [Frontend Policy Search](../frontend/04_policy_search.md)
- [Release 1 실데이터 품질 Profile](../../../data/release_dataset_profile.md)
- [Policy API 계약](../../../api/policies.md)

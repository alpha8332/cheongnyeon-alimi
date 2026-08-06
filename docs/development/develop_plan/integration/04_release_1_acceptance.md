# Integration 04 Release 1 Acceptance Forest 개발 계획

## 계획 정보

- 번호: Integration 04
- 상태: completed (`2026-08-06`)
- 대상 Release: `v0.1.0`
- 담당 영역: Team Leader - Integration
- 작업 브랜치: `feature/data/release-dataset-bootstrap`
- 현재 Slice: IA3F completed (`Gate G4 pass`)
- 개발 기록:
  [Release 1 Acceptance 개발 기록](../../development_notes/integration/release_1_acceptance.md)

## 목적

Data 02의 실제 정책 snapshot, Backend 06 검색 API와 Frontend 04 검색 UI를
하나의 PostgreSQL → HTTP → Browser 흐름으로 연결하고 Release 1 후보 여부를
승인된 기술·경량 팀 리뷰 근거와 함께 판정한다.

## 범위

- Gate G2 Data·Backend·Frontend 준비 증거와 공통 계약 대조
- 승인 범위 snapshot의 로컬 복구·적재와 멱등 재실행
- 실제 PostgreSQL 대상 검색 HTTP, pagination·validation·빈 결과 검증
- Frontend 실제 API 모드의 검색·상세·loading·empty·error·partial 검증
- Browser console과 Backend 요청 로그 확인
- golden query 결과, 검색 정확도 제약과 승인된 경량 QA·사용성 근거 대조

## 범위 밖

- 새로운 Source 추가 또는 현재 호출 예산 확대
- 검색 의미·정렬 계약의 임의 변경
- 추천, 즐겨찾기, 알림, 관리자와 배포 기능
- 실행하지 않은 검증이나 관찰을 Team Leader가 통과로 대신 기록하는 작업

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
지역·연령이 `unknown`이다. 당시 QA·사용성 리뷰어·보고서 근거도 없었으므로
IA2에서는 `v0.1.0` 후보로 승인하지 않았다.

### IA3 - golden query 교체와 Release 1 차단 해소

- 상태: completed (`2026-08-06`, `Gate G4 pass`)
- 배경: 신청기간이 지난 기존 월세 정책을 현재 신청 가능한 정책의 인수
  기준으로 사용할 수 없어 golden query를 교체한다. IA2 결과는 당시의
  실행 이력으로 보존한다.

#### IA3A - 실행 가능한 인수 기준선

- 상태: completed
- golden query:
  `천안 사는 27살 청년 단기숙소 지원 받을 수 있나?`
- 기대 정책: 온통청년 `20260430005400212969`,
  `청년단기숙소 지원사업`
- 데이터 기준: `valid`, `open`, `always`, `housing`, 27세·천안 `match`
- 자동 기준: 기대 정책 20위 이내, unknown 0, 응답 2,000ms 이내
- control 기준: `단기숙소`와 천안·27세 명시 조건으로 1위, 1,000ms 이내
- 산출물: `data/release_1_acceptance.json`과
  `scripts/audit_release_1.py`

현재 snapshot의 offline profile은 기대 정책 1건을 확정했다. 실제 HTTP에서
control은 1건 중 1위였지만 자연어 query는 495건 중 49위였고 약 9.3초가
걸렸다. 따라서 Source 추가는 현재 차단 해소안이 아니며 검색 관련성과
응답시간이 기술 차단사항이다.

#### IA3B - Backend 검색 관련성·성능 보완

- 상태: completed (`2026-08-06`)
- `단기숙소` 같은 구체 term과 `청년`, `지원`, `사는`, `받을 수 있나` 같은
  일반·대화 term의 후보 확대 기여도를 분리한다.
- 지역·연령 구조화 조건과 구체 term을 보존하면서 기대 정책을 20위 이내로
  올리고 2초 예산을 만족한다.
- 빈 query, validation, pagination, partial·unknown과 기존 parser 계약의
  회귀가 없는지 PostgreSQL 통합 테스트로 확인한다.

구현 결과 `단기숙소`를 housing과 자연어 keyword로 함께 보존하고 대화형
filler를 제외했다. 구체 term은 term 간 AND·검색 필드 간 OR, 일반 term만
있는 탐색은 OR fallback을 사용한다. actual snapshot에서 자연어와 control
모두 1건 중 1위였고, cold 317.04ms·109.92ms와 warm 5회 최대
91.89ms·109.16ms로 예산을 충족했다. 공개 DTO와 4단계 최종 정렬은 유지했다.

#### IA3C - Data 신청기간·상태 안전성 검토

- 상태: completed (`2026-08-06`)
- 지원 내용의 임의 문장에서 날짜를 추정하지 않고 Source field mapping 근거가
  있을 때만 구조화 기간으로 승격한다.
- 현재 golden 정책과 기본 노출 후보의 기간·상태를 재감사하고, 구조화할 수
  없는 값은 unknown으로 유지하며 자격 확정 표현을 금지한다.

실제 snapshot 3,156건의 offline profile에 Source mapping·기간 상태 일치·본문
날짜 미승격 감사를 추가했다. 기본 노출 1,184건 중 온통청년 723건은 신청기간
원문이 있고 722건은 일정 또는 상태가 구조화됐다. 복지로 461건은 현재 계약에
신청기간 전용 필드가 없어 기간·상태를 모두 null로 유지했다. 일반 본문의 날짜
표기 2건은 관찰만 하고 승격하지 않았으며, Source 근거 없는 승격과 상태
불일치는 0건이다. golden 정책은 명시적 `상시` 근거와 `open` 상태가 일치해
안전성 감사를 통과했다. 후보 노출만 허용하고 자격 확정은 계속 금지한다.

#### IA3D - Frontend 실제 API 재검증

- 상태: completed (`2026-08-06`)
- 수정된 검색 응답으로 기대 정책이 첫 페이지에 노출되는지 확인한다.
- 조건·근거·출처·수집 시각과 “후보이지 자격 확정이 아님” 안내가 응답
  계약과 일치하는지 unit·Browser·E2E로 검증한다.
- actual API E2E 11건과 desktop·390px Browser에서 기대 정책
  `청년단기숙소 지원사업`의 첫 페이지 1위, 상세 출처·수집 시각·접수 상태,
  자격 비확정 안내를 확인했다.

#### IA3E - 수동 증거 수집과 정합성 검증

- 상태: completed (`2026-08-06`, 경량 팀 리뷰 정책)
- QA와 사용성 리뷰를 동일 snapshot·계약 hash로 확보한다.
- `v0.1.0` 기본 검색 MVP는 역할 독립과 보고서 대조를 필수 Gate에서 제외하고,
  API 오류 UX·보고서·확장 시나리오를 `v0.5.0`으로 이관한다.
- actual 기술 증거, 역할별 템플릿과 정합성 검증 도구를 제공한다.
- Windows reviewer는 범용 `run.bat`로 actual DB·API·UI를 실행하고 웹 UI에서
  exact query를 직접 입력해 검증한다.
- QA·사용성 두 역할이 필수 check를 실제 수행하고 증거 reference와 함께
  `pass` 또는 `blocked`를 기록해야 완료한다.

#### IA3F - Gate G4 재판정

- 상태: completed (`2026-08-06`, `Gate G4 pass`)
- 자동 인수 검사는 기술 판정만 내리고 Team Leader가 수동 증거와 비차단
  후속사항을 대조해 최종 판정한다.
- actual 기술 `pass`, QA·사용성 `pass`, evidence readiness
  `ready-for-team-leader-decision`을 확인해 `v0.1.0` 후보로 승인했다.

## 검증 계획

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -B scripts\profile_release_dataset.py --require-period-safety
.\.venv\Scripts\python.exe -B scripts\audit_release_1.py --base-url http://127.0.0.1:8000
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
- 승인된 QA·사용성 근거와 `v0.5.0` 이관 위험이 기록됨
- Release 1 차단 결함이 없거나 판정이 명시적으로 `blocked`임

## 위험과 미확정 사항

- `2026-08-06` snapshot은 이전 DT4보다 온통청년 3건이 줄어 외부 데이터가
  시간에 따라 변함을 재확인했다.
- IA2 월세 golden query의 confirmed 정책은 0건이었고 현재 인수 기준에서
  폐기했다. 첫 후보의 지원 내용에는
  `2026-03-30 ~ 2026-05-29` 신청기간이 있으나 구조화 신청 기간·상태는
  `null`이다. DT7C 재감사에서 복지로 계약에는 기간 전용 필드가 없음을 확인해
  이 본문 날짜를 승격하지 않았으며 최신 수집만으로 신청 가능성을 설명하지
  않는다.
- 교체한 golden의 관련성·성능 기술 기준과 신청기간 안전성은 IA3B~C에서
  통과했고 Frontend 실제 API 재검증도 IA3D에서 완료했다.
- 제공된 Word 리뷰에서 자격·신청 정보 보강, 긴 지역 목록 축약과 오류 토스트
  의견이 확인됐다. 실제 검색 MVP를 막지 않는 `v0.5.0` 후속으로 분류했다.
- 경량 리뷰 정책으로 보고서 대조와 API 오류 UX 검증을 `v0.5.0`으로 이관했다.
  Release 1에서 수행한 것처럼 기록하지 않는다.

## 관련 문서

- [3주차 Data·Team Leader 실행 계획](../../weekly_plan/week_03_data_team_leader.md)
- [3주차 전체 상세 계획](../../weekly_plan/week_03_release_1.md)
- [Release Dataset Bootstrap](../data/02_release_dataset_bootstrap.md)
- [Backend Policy Search](../backend/06_policy_search.md)
- [Frontend Policy Search](../frontend/04_policy_search.md)
- [Release 1 실데이터 품질 Profile](../../../data/release_dataset_profile.md)
- [Policy API 계약](../../../api/policies.md)

# Integration 04 Release 1 Acceptance 개발 기록

## 작업 정보

- 상태: completed
- 최종 판정: `Gate G4 pass`
- 작업일: `2026-08-06`
- 영역: Team Leader - Integration, DT5 Gate G2·G3, DT6 Gate G4와 DT7 IA3
- 브랜치: `feature/data/release-dataset-bootstrap`
- 계획: [Integration 04 Release 1 Acceptance](../../develop_plan/integration/04_release_1_acceptance.md)
- 병합 대상: Frontend `b37752a1bb8bfe0043e9de8908de6529309c36ee`,
  Backend `01035da76f09a186409e516d5f030f0af4fdd85f`

## 목적

다른 PC에서 완료한 DT3·DT4의 Git 제외 Runtime 상태를 이 PC에 복구하고,
병합한 Backend 검색 API와 Frontend 검색 UI를 실제 snapshot으로 연결한다.

## Forest 범위

- IA0 FE·BE 비커밋 병합과 로컬 환경 차이 확인
- IA1 snapshot 복구, PostgreSQL 적재, HTTP·Browser 통합과 결함 수정
- IA2 golden query·Release 1 판정과 차단사항·재개 조건 기록
- IA3 현재 신청 가능한 golden query 교체, 경량 팀 리뷰와 Gate G4 재판정

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| IA0 | completed | FE fast-forward, BE `--no-commit` 병합과 로컬 Runtime 부재 확인 |
| IA1 / DT5 | completed | Gate G2·G3 실제 DB → API → UI 검증 통과 |
| IA2 / DT6 | completed | exact golden query 검증, Gate G4 `blocked` |
| IA3A / DT7 | completed | 단기숙소 golden 계약·자동 감사 기준선, 기술 차단 구체화 |
| IA3B / DT7 | completed | 구체 term anchor, golden 1위·응답시간 예산 통과 |
| IA3C / DT7 | completed | 기간·상태 안전성 감사 통과 |
| IA3D / DT7 | completed | Frontend actual API·Browser·E2E 재검증 통과 |
| IA3E / DT7 | completed | 새 contract hash actual 증거와 경량 QA·사용성 리뷰 정합성 통과 |
| IA3F / DT7 | completed | 비차단 후속 분류, Gate G4 `pass`, `v0.1.0` 후보 승인 |

## 구현 내용

### 병합과 로컬 snapshot 복구

Frontend는 현재 Data HEAD의 후손이어서 fast-forward했고 Backend는
`--no-commit --no-ff`로 병합했다. 새 merge commit은 만들지 않았다.

이 PC에는 DT1 표본 Raw만 있고 Runtime DB row는 0건이었다. `runtime/raw`와
PostgreSQL이 Git 제외라는 다른 PC 작업 특성과 일치했다. 저장소 밖 키 파일의
두 레이블을 process 환경변수로만 주입해 기존 승인 예산으로 다시 수집했다.
인증값·query·payload는 출력하거나 기록하지 않았다.

| Source | snapshot ID | 요청 | 수집·수용 | 품질 |
| --- | --- | ---: | ---: | --- |
| 온통청년 | `6add34f7aad9456ab0abb19175b7621c` | 6 | 2,695 | valid 1,459·partial 1,236·invalid 0 |
| 복지로 | `ffa74ef47e6048109f11bf40d1ac5e15` | 6 | 461 | valid 0·partial 461·invalid 0 |

합계 3,156건으로 DT4의 3,159건보다 온통청년이 3건 줄었다. 같은 수치로
조작하지 않고 `2026-08-06` Source 시점 차이로 보존했다.

두 Source 모두 dry-run 후 전건 inserted했고, 동일 snapshot 재실행은
온통청년 2,695건·복지로 461건 전부 unchanged였다. 검색 요청 중 외부 API는
호출하지 않았다.

### 통합 중 수정한 결함

- Backend 신규 PostgreSQL 검색 통합 test fixture가 Alembic의
  `config.attributes["database_url"]`을 사용하지 않아 Runtime 기본 URL로
  접속하던 격리 오류를 수정했다.
- 같은 fixture가 `_test` public schema를 종료 시 정리하지 않아 후속 Migration
  테스트를 오염하던 문제를 수정했다.
- status 조건이 없는 query의 verdict를 `match`로 기대하던 테스트를 승인
  계약의 `null`로 수정했다.
- Frontend 검색어 지우기가 input만 비우고 URL `q`를 남기던 문제를 수정했다.
- E2E의 기본 `page=1` URL 강제 기대를 serializer의 기본값 생략 계약에 맞추고,
  실제 Backend가 Source stopword를 제거한 뒤 남기는 `생활` 미해석 term을
  검증하도록 수정했다.
- Playwright 결과 파일을 Git 추적 대상에서 제거하고 ignore에 추가했다.

### DT6 golden query와 Gate G4 판정

동일한 PostgreSQL snapshot 3,156건에 세 가지 요청을 실제 검색 endpoint로
실행했다. 검색 중 외부 Source API는 호출하지 않았다.

| 요청 | 결과 | 판정 |
| --- | ---: | --- |
| `천안 사는 27살 청년 월세 지원 받을 수 있나?` | 48건 | 천안·27세·주거 해석 성공, 첫 후보 지역·연령 unknown |
| `27세 천안 청년 월세 지원` | 46건 | 일반 `지원` term의 OR 일치로 비월세 후보 포함 |
| `월세` + 천안·27세·주거 명시 | 3건 | 전부 복지로 partial, 지역·연령 unknown, confirmed 0건 |

exact query의 첫 후보 `청년월세 지원사업` 상세에는 월 최대 20만원 지원과
`2026-03-30 09:00 ~ 2026-05-29 16:00` 신규 신청기간이 텍스트로 존재한다.
그러나 구조화 지역·연령·신청 기간·접수 상태는 미정이다. 현재 날짜
`2026-08-06`에 신청 가능하다고 단정할 수 없으며, 검색 상위 48건 중에는
장애인 자립지원·한부모가족시설 등 월세와 직접 관련 없는 후보도 포함됐다.

실제 API 모드 Browser에서 exact 문장을 홈 검색으로 입력해 URL 원문 보존,
연령 27세·카테고리 주거·충청남도 천안시 Chip, 48건·3페이지, partial·unknown
경고와 첫 후보 상세·원문 링크를 확인했다. 기존 DTO의 `source_name`과
`collected_at`이 상세 화면에 없던 Release 1 소비 누락은 데이터 출처와
`KST` 수집 시각 표시로 보완했다.

Gate G4 판정은 `blocked`다. confirmed 정책 부재는 DT6 기준의 필수 차단
조건이며, QA smoke·사용성 리뷰·보고서 대조의 독립 증거도 저장소에 없다.
Team Leader의 Browser·E2E 결과로 이 세 역할의 승인을 대신하지 않았다.

### DT7 golden query 교체와 자동 재인수 기반

신청기간이 종료된 기존 `청년월세 지원사업`은 현재 신청 가능한 정책을 찾는
golden 대상으로 부적합하다는 결정에 따라 IA2 증거는 역사로 보존하고 현재
인수 query를 다음과 같이 교체했다.

```text
천안 사는 27살 청년 단기숙소 지원 받을 수 있나?
```

기대 정책은 온통청년 `20260430005400212969`의
`청년단기숙소 지원사업`이다. 현재 snapshot profile에서 이 정책은
`valid/open/always/housing`, 27세·천안 `match`, unknown 0으로 확인됐다.
따라서 후보 노출은 허용하지만 이 결과만으로 사용자 자격을 확정하지 않는다.

동일 PostgreSQL·HTTP 기준 결과는 다음과 같다.

| 시나리오 | 결과 | 자동 기준 | 판정 |
| --- | ---: | ---: | --- |
| 자연어 golden, limit 100 | 495건, 기대 정책 49위, 약 9.3초 | 20위 이내·2초 이내 | blocked |
| `단기숙소` + 천안·27세 control | 1건, 기대 정책 1위, 약 0.1초 | 1위·1초 이내 | pass |

이 차이로 데이터·Source 부재가 아니라 일반·대화 term의 OR 후보 확대,
정렬과 그에 따른 응답시간을 IA3B의 차단사항으로 좁혔다.
`data/release_1_acceptance.json`은 snapshot과 기대 정책, 순위·unknown·응답시간
예산을 기계 판독 가능한 계약으로 고정한다. `scripts/audit_release_1.py`는 실제
HTTP 결과를 민감정보 없이 JSON 증거로 만든다. 최종 수동 Gate 범위는
DT7E에서 경량 QA·사용성 리뷰로 조정했지만 exact query·snapshot·기대 정책의
기술 기준은 낮추지 않았다.

### DT7B 검색 관련성·성능 보완 결과

Parser는 `단기숙소`를 `housing` category와 `source="q"` keyword로 함께
보존하고 `사는`, `받을`, `수`, `있나`를 대화형 filler로 제외한다.
Repository는 구체 term이 있으면 term 간 AND, search projection·제목·요약
필드 간 OR로 후보를 제한한다. 일반 term만 있는 검색은 기존 OR 발견 흐름을
유지하며 explicit keyword는 일반어여도 항상 후보 anchor로 사용한다.

동일 actual snapshot 3,156건의 재검증 결과는 다음과 같다.

| 실행 | 자연어 golden | 명시 조건 control | 기술 판정 |
| --- | ---: | ---: | --- |
| cold acceptance | 1건·1위·317.04ms | 1건·1위·109.92ms | pass |
| warm 5회 최대 | 1건·1위·91.89ms | 1건·1위·109.16ms | pass |

기존 495건·49위·약 9.3초와 비교해 후보 확대와 N개 정책별 평가 비용이
제거됐다. `score` 최종 정렬, nullable verdict, partial·unknown, pagination,
explicit override와 `PolicyRead` 응답 DTO는 유지했다. 기술 acceptance는
`pass`지만 자동 도구는 독립 증거를 승인하지 않으므로 Gate G4는
`technical-pass-evidence-pending`, 최종 `blocked`를 유지한다.

### DT7C 신청기간·상태 안전성 감사 결과

`scripts/profile_release_dataset.py`를 1.2.0으로 올리고 Release snapshot의
신청기간 Source mapping, 기간·상태 일치, 일반 본문 날짜 미승격과 golden 정책
근거를 한 번에 감사하도록 확장했다. `--require-period-safety`를 사용하면
Source 근거 없는 승격·상태 불일치·golden 근거 누락 중 하나라도 발견할 때
실패 종료한다.

| 감사 cohort | 전체 | 기본 노출 |
| --- | ---: | ---: |
| 정책 | 3,156 | 1,184 |
| Source 신청기간 원문 | 2,695 | 723 |
| 일정 또는 상태 구조화 | 2,694 | 722 |
| 기간·상태 모두 unknown | 461 | 461 |
| 일반 본문 날짜 표기 관찰·미승격 | 2 | 2 |
| Source 근거 없는 승격 | 0 | 0 |
| 기간·상태 불일치 | 0 | 0 |

온통청년은 `aplyYmd`와 검증된 `aplyPrdSeCd`만 기간 근거로 사용한다. 복지로
현재 목록·상세 계약에는 기간 전용 필드가 없으므로 461건 모두 기간·상태를
null로 유지했다. `청년내일저축계좌`와 `청년월세 지원사업` 일반 본문의 날짜
표기는 원문으로만 보존하고 구조화하지 않았다.

golden 정책은 Source 원문 `상시`, 일정 `always`, 상태 `open`이 일치하고 본문
승격을 사용하지 않아 안전성 감사 `passed=true`다. 후보 노출은 허용하지만
자동 감사 결과만으로 사용자 자격을 확정하지 않는다. 이 결과로 Data 기간
차단사항은 해소됐고, DT7D에서 Frontend 실제 API 재검증도 완료했다. 독립
증거가 남아 Gate G4는 계속 `blocked`다.

### DT7D Frontend actual API 재검증

actual API 모드에서 새 golden exact query를 실행해 첫 페이지의 첫 결과가
`청년단기숙소 지원사업`이고 지역·연령·주거·단기숙소 조건이 match임을
확인했다. 상세 화면은 기존 공개 DTO의 `온통청년 청년정책 API`, KST 수집 시각,
`상시`, `접수 중`, 원문 링크를 표시한다.

검색 결과와 상세에는 정책 후보 안내이며 실제 자격 충족을 확정하지 않는다는
공통 `role=note` 문구를 추가했다. Frontend unit 46건, Mock E2E 10건과 actual
E2E 11건이 통과했다. 인앱 Browser desktop과 390×844 viewport에서도 검색
첫 결과·조건 근거·상세 출처·수집 시각·상태·안내를 확인했다. 이 검증은 기술
증거이며 제공된 수동 리뷰 관찰과 별도로 보존한다.

### DT7E 경량 팀 리뷰와 증거 정합성

`audit_release_1.py`로 동일 actual snapshot의 안전한 기술 증거 JSON을
`docs/contest/release_1_technical_evidence.json`에 생성했다. contract SHA-256은
`53bc5ee18e028a050079559064eaf88a332d917099a9bad8f696d312838a411c`이고
3,156건 baseline과 두 Source snapshot identity가 계약과 일치한다. 최종
재감사에서 자연어 golden은 95.95ms, control은 78.68ms로 모두 1건 중
1위·technical `pass`다.

제공된 `v0.1.0 리뷰.docx`의 본문과 화면 3개를 확인해 QA·사용성 관찰을
`release_1_review_summary.md`에 비밀정보 없이 요약했다. Team Leader는 Release
1을 기본 검색 MVP 확인 범위로 마감하도록 수동 증거 정책을 경량 팀 리뷰로
조정했다. 역할 독립과 보고서 대조, API 오류 토스트 검증은 필수 Gate에서
제외하고 `v0.5.0` 후속으로 이관했다.

`verify_release_1_evidence.py`는 다음 항목을 기계적으로 대조한다.

- 기술 증거의 release·Gate·contract hash·snapshot·exact query·기대 정책
- QA의 기본 검색·상세, empty와 partial/unknown 관찰
- 사용성 리뷰의 조건·이유·출처/최신성·자격 비확정 이해도
- reviewer, timezone 포함 수행 시각, 관찰 notes와 저장소 증거 reference

최종 검증 결과 technical·QA·사용성은 모두 `pass`, readiness는
`ready-for-team-leader-decision`, blocker는 0건이다. 검증 도구는 증거 정합성만
판정하고 Gate 통과는 DT7F에서 별도로 결정했다.

리뷰 화면의 빈 결과 안내가 actual snapshot 환경에서도 `canonical Seed
기반`이라고 표시되는 계약 불일치를 발견했다. 이를 `고정된 실제 정책
snapshot 기반`과 수집 범위·시점 제약 안내로 수정하고 Frontend unit 회귀를
추가했다. 자격·신청 정보 보강, 긴 지역 목록 축약과 오류 토스트는 기본 검색
MVP를 막지 않는 `v0.5.0` 후속으로 분류했다.

### DT7F Gate G4 재판정

Team Leader는 새 contract hash의 actual 기술 증거, 경량 QA·사용성 리뷰,
비차단 후속사항과 비밀·Runtime 경계를 대조했다. 자연어·control acceptance는
모두 기대 정책 1위·unknown 0·응답시간 예산 이내이고 manual evidence verifier
blocker는 0건이다. 이에 Gate G4를 `pass`로 판정하고 현재 커밋 계열을
`v0.1.0` Release 1 후보로 승인했다.

이 판정은 Production 배포, 전체 Source 수집, 자동 Scheduler, 추천·즐겨찾기,
보고서 완성을 포함하지 않는다. 해당 범위는 기존 로드맵대로 `v0.5.0` 이후
Forest에서 수행한다.

Windows에서 환경변수를 직접 구성하지 않아도 전체 시스템을 사용할 수 있도록
저장소 루트에 범용 `run.bat`와 PowerShell 실행기를 추가했다. 실행기는
`.venv`·Vite·PostgreSQL·pgpass를 확인하고 Backend를 실제 PostgreSQL에,
Frontend를 actual API 모드로 연결한 뒤 홈 화면을 기본 브라우저에서 연다.
특정 acceptance나 golden query를 자동 실행하지 않으며 API key와 외부 Source
호출도 사용하지 않는다.

Backend와 Frontend 출력은 실행한 터미널에 함께 표시한다. 별도 종료 BAT,
Runtime 상태 파일과 전용 로그를 만들지 않으며 같은 터미널에서 `Ctrl+C`를
누르면 이번 실행에서 추적한 두 프로세스를 정리한다. 포트가 이미 다른
프로세스에 점유돼 있으면 임의로 종료하지 않고 실패한다.

## 주요 변경 파일

- `backend/tests/test_postgresql_policy_search_integration.py`
- `backend/app/services/policy_search_parser.py`
- `backend/app/repositories/policy_search.py`
- `backend/app/api/v1/endpoints/policy_search.py`
- `backend/tests/test_policy_search_parser.py`
- `backend/tests/test_policy_search_repository_builder.py`
- `backend/tests/test_policy_search_api_endpoint.py`
- `data/release_1_acceptance.json`
- `.gitattributes`
- `scripts/audit_release_1.py`
- `scripts/profile_release_dataset.py`
- `tests/test_release_1_acceptance_audit.py`
- `tests/test_release_dataset_profile.py`
- `docs/data/normalization_rules.md`
- `docs/data/release_dataset_profile.md`
- `docs/data/source_profiles.md`
- `frontend/src/pages/user/PolicySearchPage.tsx`
- `frontend/e2e/policy-search-audit.spec.ts`
- `frontend/.gitignore`
- `frontend/src/pages/user/ProgramDetailPage.tsx`
- `frontend/src/utils/policyDisplay.ts`
- `frontend/src/utils/policySearchErrors.ts`
- `frontend/src/styles/theme.css`
- `frontend/tests/policyDisplay.test.ts`
- `frontend/tests/policySearch.errors.test.ts`
- `frontend/tsconfig.test.json`
- `scripts/verify_release_1_evidence.py`
- `tests/test_release_1_evidence_verification.py`
- `docs/contest/release_1_evidence_guide.md`
- `docs/contest/release_1_evidence_template.json`
- `docs/contest/release_1_technical_evidence.json`
- `docs/contest/release_1_review_summary.md`
- `docs/contest/release_1_evidence.json`
- `docs/contest/release_1_gate_decision.json`
- `run.bat`
- `scripts/run_local.ps1`
- `docs/development/develop_plan/integration/04_release_1_acceptance.md`
- `docs/development/development_notes/integration/release_1_acceptance.md`

## 설계 결정

- 다른 PC의 Runtime 상태는 문서만으로 존재한다고 간주하지 않고 이 PC에서
  manifest와 DB row를 재검증한다.
- 새 snapshot 수치가 이전과 다르면 최신 인수 시점 수치를 사용하되 DT4의
  역사적 기록을 덮어쓰지 않는다.
- 검색 term 결합·score는 API 의미 변경이므로 DT5에서 임의 수정하지 않고
  DT6 결정 대상으로 남긴다.
- actual 기술 기준은 exact query·snapshot·contract hash로 유지하고 수동 Gate만
  경량 QA·사용성 리뷰로 조정한다. 보고서와 API 오류 UX는 실행한 것으로
  간주하지 않고 `v0.5.0`으로 이관한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Data unittest | 113건 통과 |
| Backend 최초 비-DB 실행 | 99건 통과·15건 skip, warning 2건 |
| Backend 실제 PostgreSQL 첫 실행 | 111건 통과·신규 fixture 3건 오류 |
| Backend fixture 1차 수정 | 112건 통과·기대값/격리 2건 실패 |
| Backend 최종 PostgreSQL 전체 | 114건 통과, warning 2건 |
| Frontend unit | 43건 통과 |
| Frontend build·lint | 통과 |
| Playwright 최초 실행 | 로컬 Chromium 부재로 10건 시작 전 실패 |
| Playwright 설치 후 실제 API 1차 | 7건 통과·3건 실패 |
| E2E 수정 후 2차 | 9건 통과·strict locator 1건 실패 |
| E2E 최종 | 10건 통과 |
| 실제 검색 HTTP | health 200, 빈 q 422, 미일치 term 0건, pagination 확인 |
| 인앱 Browser | 검색·지우기·빈 결과·pagination·partial 상세 통과, console warning/error 0건 |
| DT6 exact golden API | 48건, 첫 후보 지역·연령 unknown |
| DT6 월세 단일어+명시 조건 | 3건, partial 3·confirmed 0 |
| DT6 Frontend unit 1·2차 | test 전용 alias 미해석으로 compile 실패 |
| DT6 Frontend 최종 unit | 45건 통과 |
| DT6 Frontend build·lint | 통과 |
| DT6 실제 API Playwright | 10건 통과 |
| DT6 인앱 Browser | exact query 48건·Chip·경고·상세 출처·수집 시각 확인 |
| DT7 offline profile | 3,156건, 단기숙소 기대 정책 confirmed 1건 |
| DT7 자연어 acceptance | 495건·49위·약 9.3초, 순위·2초 예산 차단 |
| DT7 명시 조건 control | 1건·1위·약 0.1초, 기술 기준 통과 |
| DT7 Data 전체 unittest | 122건 통과 |
| DT7 Backend 전체 PostgreSQL pytest | 114건 통과, 기존 deprecation warning 2건 |
| DT7 문서 검증 | 통과 |
| DT7B parser·Repository·API 집중 pytest | 18건 통과 |
| DT7B PostgreSQL golden 통합 | 3건 통과 |
| DT7B Backend 전체 PostgreSQL pytest | 119건 통과, 기존 warning 2건 |
| DT7B Frontend API 소비 unit | 45건 통과 |
| DT7B Frontend build·lint | 통과 |
| DT7B actual acceptance | cold 317.04/109.92ms, warm 최대 91.89/109.16ms, 모두 1위 |
| DT7C strict period safety profile | 3,156건 재생, `passed=true` |
| DT7C Data 전체 unittest | 129건 통과 |
| DT7C Data Integration pytest | 4건 skip, `TEST_DATABASE_URL` 미주입, 기존 warning 1건 |
| DT7C Python compile·문서 검증·`git diff --check` | 통과 |
| DT7D Frontend unit | 46건 통과 |
| DT7D Frontend build·lint | 통과 |
| DT7D Mock Playwright 최종 | 10건 통과·actual 전용 1건 skip |
| DT7D actual API Playwright 최종 | 11건 통과 |
| DT7D actual acceptance 재감사 | technical `pass`, Gate `blocked`, natural 106.98ms·control 95.78ms |
| DT7D 인앱 Browser | desktop·390×844 검색·상세·자격 비확정 안내 통과 |
| DT7E 증거 검증 집중 unittest | 9건 통과 |
| DT7E Data 전체 unittest | 138건 통과 |
| DT7E strict period safety profile | 3,156건 재생, `passed=true` |
| DT7E actual 기술 증거 | 3,156건, natural 136.91ms·control 155.40ms, 모두 1위·technical `pass` |
| DT7E actual 기술 재검증 | natural 84.47ms·control 77.58ms, 모두 1위·technical `pass` |
| DT7F 새 contract actual 기술 증거 | natural 95.95ms·control 78.68ms, 모두 1위·unknown 0·technical `pass` |
| DT7F 경량 수동 증거 검증 | QA·사용성 `pass`, readiness `ready-for-team-leader-decision`, blocker 0건 |
| DT7F Gate G4 | `pass`, `v0.1.0` Release 1 후보 승인 |
| Windows 범용 실행기 | 실제 Backend/Frontend HTTP 준비 확인 및 종료 후 포트 정리 통과 |
| DT7F 리뷰 Word 확인 | 본문 25개·포함 화면 3개 전체 확인, LibreOffice 미설치로 페이지 render 미수행 |
| DT7F evidence 집중 unittest | 18건 통과 |
| DT7F Data 전체 unittest | 139건 통과 |
| DT7F Backend PostgreSQL·Integration | 123건 통과, 기존 deprecation warning 2건 |
| DT7F Frontend unit·build·lint | unit 46건, build·lint 통과 |
| DT7F actual API Playwright | 서버 중단 상태를 재사용한 첫 실행 4건 통과·7건 실패, 전용 actual 서버 재실행 후 11건 통과 |
| DT7F 문서·JSON·diff 검증 | `validate_docs.py`, Release JSON parse, `git diff --check` 통과 |

폐기한 IA2 golden query `27세 천안 청년 월세 지원`은 실제 API에서 46건의 후보를
반환했다. 첫 후보 `청년월세 지원사업`은 연령·지역 unknown으로 표시됐고,
Profile의 confirmed match는 0건이다. 실제 적용 가능성을 단정하지 않는다.

`npm ci`는 실행 중 Vite가 native binding을 잡아 첫 시도에 `EPERM`으로
실패했다. 이 작업에서 시작한 Vite process를 종료한 뒤 lockfile 기준 201개
package 설치가 성공했다. `npm audit`은 high 3건을 보고했으며 자동 수정은
범위 밖이라 실행하지 않았다.

DT7C Integration 4건 skip은 `TEST_DATABASE_URL`이 현재 process에 주입되지
않아 기존 PostgreSQL 통합 테스트가 실행되지 않은 결과다. 성공으로 처리하지
않는다. DT7C는 DB·API 계약을 변경하지 않았고, 실제 snapshot 안전성은 DB 없이
고정 Raw를 재생하는 strict profile로 검증했다.

DT7F Playwright 첫 실행은 기존 3000·8000 프로세스를 재사용했지만 실행 중 두
listener가 사라져 검색 결과 영역을 찾지 못한 7건이 실패했다. 성공으로
처리하지 않고 이번 검증에서 소유한 actual 서버를 새로 실행해 같은 11건을
전부 재검증했으며 종료 후 두 포트도 정리했다.

## 남은 작업

### `v0.5.0` 후속 작업

- Source에 없는 자격·신청 정보의 추가 수집 또는 보강 경계를 검토한다.
- 긴 지역 목록을 축약하고 전체 보기 동작을 제공한다.
- API 오류·재시도 흐름을 토스트와 닫기 동작으로 구현·Browser 검증한다.
- 보고서 근거 대조와 더 넓은 독립 QA·사용성 시나리오를 수행한다.
- 복지로에 신청기간 전용 Source 필드가 추가될 때만 mapping과 회귀 감사를
  다시 검토한다.
- 기존 Starlette deprecation warning 2건과 npm audit high 3건은 별도
  의존성 검토가 필요하다.

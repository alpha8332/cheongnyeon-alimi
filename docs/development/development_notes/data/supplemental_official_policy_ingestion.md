# Supplemental Official Policy Ingestion 개발 기록

## 작업 정보

- 작업일: 2026-08-17
- 영역: Data·Team Leader
- 상태: in-progress
- 브랜치: `feature/data/supplemental-official-policy-ingestion`
- 계획: [Data 06 Supplemental Official Policy Ingestion](../../develop_plan/data/06_supplemental_official_policy_ingestion.md)
- 주차 Slice: `DTL5-3` / `W5-D3`
- 현재 Gate: `SOP-G0_PASS`~`SOP-G3_PASS`, `SOP-G4_BLOCKED`
- 다음 판단: K-패스 중복 차단 뒤 신규 정책 최소 기준 계획 재승인 전 W5-G1 금지

## 목적

사용자 제공 `청년정책_데이터수집_완료.xlsx`를 바로 정책으로 적재하지 않고,
결정적 후보 inventory로 정제한다. 현재 온통청년·복지로 snapshot과 실제
PostgreSQL을 먼저 대조해 중복을 제외하고, robots·이용 조건·공개 목록·상세·
identity·요청 예산을 확인한 공식 Source만 Adapter 구현 대상으로 승인한다.

## Forest 범위

- SOP0: XLSX URL 64행의 lineage, exact 반복, 같은 URL·다른 제목과 문구 오류 격리
- SOP1: 승인 aggregator snapshot과 실제 DB의 ID·URL·제목 선행 감사
- SOP2: 공식 Source군의 운영 주체·robots·조건·allowlist·요청 예산 판정
- actual: 승인 5개 Source 제한 수집·offline replay, KOSAF 1건 PostgreSQL·API 인수
- 미수행: Browser 인수와 최소 2개 서로 다른 신규 Source DB 인수

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| SOP0 | completed | URL 64행 → 후보 identity 60개, exact 반복 4행 축약, URL 충돌 3개 격리 |
| SOP1 | completed | exact duplicate 26, review 11, potentially new 19, not assessed 4 |
| SOP2 | completed | approved 5, blocked 1, rejected 9; 승인 Source별 allowlist·예산 고정 |
| SOP3 | completed | 승인 5개 Source stable identity·상세 Adapter·offline replay·판정 Gate 구현 |
| SOP4 | blocked | 5개 제한 actual 완료, KOSAF만 신규 DB/API 인수; 최소 2개 신규 DB Source·Browser 미달 |
| SOP5 | blocked | 5개 Source는 `implemented_http`, 신규 정책 4개 Forest 기준 미달 |

## 구현 내용

### SOP0 입력 계약과 후보 정제

선택한 원본은 `청년정책_데이터수집_완료.xlsx`의
`청년정책 세부 수집방안!A1:F71`이며 SHA-256은
`c03aa55fba844639a89a4f62ec083dc74c5397b3ea7fbfab91450fbef97f2095`다.
원본은 수정하지 않았다.

표준 라이브러리만 사용하는 builder가 workbook relationship과 shared string을
읽고 다음을 고정한다.

- URL 입력 64행을 60개 `(title, canonical_url)` 후보 identity로 변환
- exact 반복 4쌍: 54·58, 55·65, 56·66, 57·69행
- 같은 URL·다른 제목 충돌 3개: 12·13, 15·16, 54·58·59행
- `data_error` 4 identity, 범용 공공데이터포털 홈 `discovery_reference` 1,
  후속 판정 후보 55
- 온통청년·복지로 직접 링크 11행과 그 외 URL 53행의 원래 행 lineage 보존
- XLSX의 수집 방법·필요서류 문구는 해시와 존재 여부만 보존하고 정책
  evidence나 사용자 표시 데이터로 복사하지 않음

inventory와 duplicate audit은 각각 JSON Schema와 교차 필드 validator로
검증한다. URL은 HTTPS·credential 없음, 모든 입력 행의 정확한 1회 포함,
Source군별 행·domain 일치와 상태별 실행 경계를 검사한다.

### SOP1 승인 snapshot·실제 PostgreSQL 중복 감사

감사는 기존 `load_aggregator_baseline()`을 재사용해 snapshot manifest와 실제
`policies` row를 한 read-only 기준선으로 묶었다. 기준선은 다음과 같다.

| Source | snapshot ID | snapshot 완료 | snapshot 수 | DB 확인 | DB 수 |
| --- | --- | --- | ---: | --- | ---: |
| 복지로 | `ffa74ef47e6048109f11bf40d1ac5e15` | `2026-08-06T09:19:03.630716+09:00` | 461 | `2026-08-17T13:26:30.358201+09:00` | 461 |
| 온통청년 | `6add34f7aad9456ab0abb19175b7621c` | `2026-08-06T09:18:54.586978+09:00` | 2,695 | `2026-08-17T13:26:30.358201+09:00` | 2,698 |

판정 순서는 승인 aggregator `(source_id, external_id)` → canonical public URL →
정규화 제목이다. ID·URL은 `exact_duplicate`, 제목만 같으면 자동 병합하지 않고
`review_required`, 어느 것도 없을 때만 `potentially_new`다. XLSX에 기간·지원
내용의 공식 evidence가 없으므로 제목 이외 fingerprint 일치를 가장하지 않는다.

| 판정 | identity 수 | 처리 |
| --- | ---: | --- |
| exact duplicate | 26 | Source 구현·신규 Policy 적재 후보에서 제외 |
| review required | 11 | 사용자 검색 비노출, SOP3 판정 fixture로 전달 |
| potentially new | 19 | 승인 Source 원문 확인 전까지 비노출 |
| not assessed | 4 | `data_error` 또는 범용 홈이므로 실행 후보 제외 |

직접 온통청년·복지로 11행은 고유 external ID 10개이며 모두 실제 DB에 존재한다.
12·13행은 같은 `WLF00005567`을 서로 다른 제목으로 사용하므로 12행의 실제 DB
제목을 유지하고 13행은 `data_error + exact_duplicate`다. 기존 aggregator row는
조회만 했고 수정·삭제·합성하지 않았다.

### SOP2 Source preflight와 승인 경계

`2026-08-17T15:05:06+09:00`까지 공식 페이지와 `robots.txt`를 제한 확인했다.
승인은 원문 재배포 허가가 아니라, 출처를 보존한 최소 정책 사실을 정해진
목록 1회·상세 최대 3회·요청 시작 간격 2초로 읽을 수 있다는 의미다.

| Source군 | 상태 | stable identity | 판정 핵심 |
| --- | --- | --- | --- |
| 고용24 정책 | approved | `systId` | 공개 목록·상세, robots 허용, 출처 표시 최소 사실 |
| LH 임대 공고 | approved | `panId` | 공개 임대 목록·상세, 로그인·파일 경로 제외 |
| 한국장학재단 장학 | approved | `pg` | 공개 장학 landing·상세와 신청 기간 재현 |
| 서민금융진흥원 상품 | approved | detail page key | 공개 전체보기·상품 상세, 인증·상담 경로 제외 |
| 모두의카드(K-패스) | approved | static `intro` | 공개 홈→사업소개·가입조건, 로그인·가입 요청 제외 |
| K-Startup 공고 | blocked | — | robots가 대상 `webCMRCZN`·`bizpbanc-*` 경로를 명시 차단 |
| 기존 aggregator 비교 | rejected | — | 신규 Source가 아니라 SOP1 fixture |
| 나머지 8 Source군 | rejected | — | 범용 홈·단일 상세·혼합 운영자라 목록·상세 계약 미확정 |

승인 allowlist의 근거는 다음 공식 페이지에서 확인했다.

- 고용24: [robots](https://www.work24.go.kr/robots.txt),
  [이용약관](https://www.work24.go.kr/cm/c/d/0130/retrieveUtzeStpt.do),
  [저작권정책](https://m.work24.go.kr/cm/c/d/0130/retrieveCpyrPoly.do),
  [정책 목록](https://www.work24.go.kr/cm/c/f/1100/selecPolicyInfo.do)
- LH: [robots](https://apply.lh.or.kr/robots.txt),
  [임대 공고 목록](https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1026),
  [청년 매입임대 상세 표본](https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?aisTpCd=26&ccrCnntSysDsCd=03&panId=2015122300020192&uppAisTpCd=13)
- 한국장학재단: [robots](https://www.kosaf.go.kr/robots.txt),
  [이용약관](https://www.kosaf.go.kr/ko/agreement.do),
  [장학 landing](https://www.kosaf.go.kr/ko/scholar.do?pg=scholarship_submain01)
- 서민금융진흥원: [robots](https://www.kinfa.or.kr/robots.txt),
  [상품 전체보기](https://www.kinfa.or.kr/financialProduct/peopleFinancial.do),
  [청년 미래이음 대출](https://www.kinfa.or.kr/financialProduct/youngFutureLinkLoan.do)
- 모두의카드: [robots](https://korea-pass.kr/robots.txt),
  [사업소개](https://korea-pass.kr/info/intro.do),
  [가입조건](https://korea-pass.kr/info/use_join.do)
- K-Startup: [robots 차단 근거](https://www.k-startup.go.kr/robots.txt)

### SOP3 Source Adapter·offline replay

`collectors/supplemental_official.py`는 승인된 다섯 Source를 기존 공통 계약에
연결한다. 실제 원문 selector는 Source 모듈 안에서만 해석하고 공통
`ExtractedPolicy`에는 정책 사실과 locator provenance만 넘긴다.

| Source | stable identity | 목록 selector | 상세 최소 selector |
| --- | --- | --- | --- |
| 고용24 | `systId` | `fn_goPolicyIntro(..., SI...)` | `#systId`, `h2.h2_sb`, `#iemVal0~2` |
| LH | `panId` | `.wrtancInfoBtn[data-id1..4]` | `.bbs_ViewA`, `#sta_acpDt` |
| 한국장학재단 | `pg` | 승인된 장학 page key 링크 | 현재 page 링크와 신청·자격·서류 heading |
| 서민금융진흥원 | detail path key | 승인 상품 상세 링크 | 문서 title과 대상·한도·서류·절차 heading |
| 모두의카드 | static `intro` | 홈의 `/info/intro.do` anchor | 소개의 청년 환급률·운영자와 가입조건 |

실제 공개 목록에 같은 parser를 대입한 제한 확인에서는 고용24 1건, LH 50건,
한국장학재단 승인 key 6건, 서민금융진흥원 승인 상품 2건의 identity를 재현했다.
본문은 저장하지 않았고 요청 간 2초 간격을 지켰다. 실제 상세 표본도 다섯 Source
모두 selector drift 없이 `ExtractedPolicy`까지 재생됐지만, 원문에서 신청 가능·
자격·서류를 모두 확인하지 못한 표본은 자동 accepted하지 않는다.

fixture는 목록·상세 정상, 목록 selector drift, 상세 누락, 상세 title drift,
마감, 필요서류 누락을 포함한다. 같은 Raw byte·hash·`collected_at`을 두 번
재생했을 때 같은 결과를 내며, 목록과 상세의 identity·parent·canonical URL이
어긋나면 전체 replay를 실패시킨다.

pagination 종료는 SOP2 요청 예산과 동일하게 Source별 승인 landing 한 페이지,
정확히 한 `list_response`로 고정했다. HTML의 임의 다음 링크를 따라가지 않으며
추가 페이지가 필요한 Source는 SOP4 actual에서 별도 종료 근거를 승인받아야 한다.

`decide_supplemental_policy()`는 청년 대상·현재 신청 가능·담당기관·신청조건·
필요서류·신청방법이 모두 공식 상세에서 확인된 경우만 accepted한다. 마감은
closed, 근거 부족은 review, evidence 계약 손상은 failed로 분리한다. accepted
후보도 기존 aggregator 기준선이 없거나 fingerprint 판정이 필요하면 교차 Source
중복 Gate에서 duplicate review가 되어 Policy row를 만들지 않는다. 신청 기간
판정 기준일은 실행 현재 시각이 아니라 Raw `collected_at` 날짜로 고정해 offline
replay 결정성을 유지한다.

### SOP4 제한 actual·PostgreSQL·API 판정

`2026-08-17`에 승인된 다섯 Source를 목록 1회·상세 최대 3회·요청 시작 간격
2초로 수집했다. Raw와 snapshot·decision manifest는 Git에서 제외된
`runtime/`에만 두었고 첨부파일·로그인·상담 경로는 요청하지 않았다.

| Source | 요청 | 목록 identity | 상세 identity | 최소 evidence | 중복·DB 결과 |
| --- | ---: | ---: | ---: | --- | --- |
| 고용24 | 2 | 1 | 1 | review 1 | 현재 신청 가능 근거 없음, DB 0 |
| LH | 4 | 50 | 3 | review 3 | 공개 HTML에 신청 가능 근거 부족, 첨부 미수집, DB 0 |
| 한국장학재단 | 4 | 6 | 1 | accepted 1 | 신규, DB insert 1 |
| 서민금융진흥원 | 3 | 2 | 2 | accepted 1·review 1 | 햇살론유스 공식 URL이 온통청년 2건과 일치해 duplicate review, DB 0 |
| 모두의카드(K-패스) | 3 | 1 | 1 | accepted 1 | 복지로 `WLF00005440` 명칭 포함 일치로 duplicate review, DB 0 |

한국장학재단은 `scholarship05_04_01`의 기본·제출서류·지원금액 탭 세 응답을
하나의 `pg` identity로 묶었다. 여러 신청 기간 중 Raw 수집일
`2026-08-17`을 포함하는 `2026-08-12 ~ 2026-09-09` 구간을 선택했으며,
문맥 속 `마감일 제외`를 마감 상태로 오판하지 않도록 날짜 구간을 먼저 판정한다.
국가근로장학금은 aggregator 기준선과 겹치지 않아 정책 ID `15095`로 삽입됐다.
`장학금`을 공통 `education` category로 보강한 뒤 동일 snapshot은
`updated=1`, 다음 재실행은 `unchanged=1`이었다.

실제 API는 `GET /api/v1/policies/search?q=국가근로장학금`에서 대상 1건을
포함해 총 17건을 반환했고, `GET /api/v1/policies/15095?include_partial=true`는
HTTP 200·`education`·`open`·`kosaf-scholarship-web`을 반환했다. 최초 검색에서
누락된 원인은 검색 파서가 장학금을 education으로 해석하는 반면 Normalizer가
other로 저장한 category 불일치였고, 공통 mapping과 회귀 테스트로 수정했다.

Browser actual은 프론트 서버가 꺼진 상태를 확인한 뒤 임시 기동했으나 Codex
in-app Browser의 로컬 URL 정책이 reload를 차단했다. 정책상 다른 브라우저나
자동화로 우회하지 않았으므로 Browser 결과는 통과로 기록하지 않는다.

SOP4 결과는 `SOP-G4_BLOCKED`다. 서로 다른 구조에서 evidence Gate를 통과한
후보는 한국장학재단·서민금융진흥원·모두의카드 3개였지만, 뒤의 두 후보는 기존
aggregator 중복이라 실제 신규 DB 인수는 한국장학재단 1개뿐이다. 고용24·LH의
근거 부족을 완화하거나 중복을 무시하지 않는다. XLSX의 나머지 잠정 신규 후보는
현재 모집 종료·청년 전용 근거 부재·robots 차단·기존 Source 중 하나여서,
계획 최소 기준 재승인 또는 별도 공식 Source discovery 승인 전에는 `SOP-G5`와
`W5-G1`을 통과시키지 않는다.

## 주요 변경 파일

- `scripts/build_supplemental_policy_inventory.py`
- `scripts/audit_supplemental_policy_duplicates.py`
- `collectors/supplemental_inventory.py`
- `data/schema/supplemental_official_policy_inventory.schema.json`
- `data/schema/supplemental_official_policy_duplicate_audit.schema.json`
- `data/reference/supplemental_official_policy_inventory.json`
- `data/reference/supplemental_official_policy_duplicate_audit.json`
- `tests/test_supplemental_policy_inventory.py`
- `collectors/supplemental_official.py`
- `collectors/cross_source_duplicate.py`
- `collectors/normalizer.py`
- `collectors/__init__.py`
- `backend/app/services/runtime_importer.py`
- `scripts/collect_release_snapshot.py`
- `tests/test_supplemental_official.py`
- `data/fixtures/html/{work24,lh,kosaf,kinfa}-*/`

## 설계 결정

- Source와 Policy 후보를 분리하고 XLSX 행을 Source 승인으로 해석하지 않는다.
- exact 반복은 identity 하나로 축약하되 모든 원래 행 번호를 보존한다.
- URL 충돌·범용 홈·검증되지 않은 서류 문구는 accepted 후보로 승격하지 않는다.
- direct ID와 canonical URL만 확정 중복으로 제외하고 제목 일치는 review에 둔다.
- 공식 제목이 aggregator 제목에 5자 이상 포함되면 자동 적재하지 않고 review에 둔다.
- 승인 Source의 실행 경계는 목록·상세 allowlist, stable identity와 요청 예산이
  모두 있을 때만 열린다.
- K-Startup의 robots 차단은 Browser나 다른 endpoint로 우회하지 않는다.
- PostgreSQL 감사 산출물에는 DB 비밀번호·연결 문자열·Raw 본문을 남기지 않는다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| inventory·audit Schema와 semantic 단위 테스트 | `9 passed, 63 subtests passed` |
| 같은 XLSX builder 재실행 | inventory SHA-256 `9750ee53…c3d1c29`, audit hash 재연결 |
| 중복 Gate·지역 inventory·aggregator loader 관련 회귀 | `30 passed, 1 warning, 118 subtests passed` |
| 실제 PostgreSQL aggregator baseline load | 복지로 461·온통청년 2,698 row 읽기 성공 |
| 직접 URL ID 감사 | 11행·고유 ID 10개 모두 exact duplicate |
| 공식 robots 제한 GET | 고용24·LH·한국장학재단·서금원 허용, K-Startup 대상 경로 차단 확인 |
| 승인 Source 목록·상세 preflight GET | 5개 Source·11개 URL 모두 HTTP 200·식별 문구 확인, 본문 미저장 |
| Adapter·Gate·중복 runtime 집중 | `30 passed, 21 subtests passed` |
| 승인 공개 목록 parser 제한 대조 | 5개 Source stable identity 재현, 본문 미저장 |
| SOP4 실제 제한 수집 | 5개 Source·16 HTTP 요청, snapshot 5개 완료 |
| 실제 PostgreSQL 신규·재실행 | KOSAF `inserted=1` → category `updated=1` → `unchanged=1` |
| 실제 중복 Gate | 햇살론유스 canonical URL이 온통청년 2건과 일치, DB 0 |
| K-패스 보완 중복 Gate | snapshot `f8ca4c40…`, 복지로 `WLF00005440` title containment review, DB 0 |
| K-패스 실제 Policy API | `q=모두의카드&include_partial=true` HTTP 200·기존 복지로 1건(`id=6212`) |
| 실제 Policy API | 검색 HTTP 200·대상 1건, 상세 HTTP 200·education·open |
| Browser actual | 로컬 URL 정책 차단, 우회 없이 미통과 기록 |
| Data 전체 pytest | `326 passed, 8 skipped, 1 warning, 172 subtests passed` |
| Backend 전체 pytest | `170 passed, 17 skipped, 1 warning` |
| 문서 링크·상태·필수 heading 검증 | `Documentation validation passed` |
| whitespace 검증 | `git diff --check` 통과(CRLF 안내만 출력) |

skip은 전용 `TEST_DATABASE_URL`이 없는 PostgreSQL actual test이며 통과로 세지
않는다. 경고는 기존 Starlette/httpx deprecation이다.

## 남은 작업

- 신규 Source 추가 승인은 완료했으나 중복으로 차단됐다. 별도 공식 Source discovery
  범위를 승인하거나 신규 정책 최소 기준을 명시적으로 재승인
- 승인 뒤 PostgreSQL → API → Browser actual을 다시 수행해 `SOP-G4` 재판정
- 전용 PostgreSQL test DB를 제공해 현재 skip된 통합 테스트 실행
- Data 05·온통청년·복지로·Release 1 golden 전체 회귀와 `SOP-G5` Forest 판정

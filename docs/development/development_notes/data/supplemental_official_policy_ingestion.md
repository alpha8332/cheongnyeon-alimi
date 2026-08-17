# Supplemental Official Policy Ingestion 개발 기록

## 작업 정보

- 작업일: 2026-08-17
- 영역: Data·Team Leader
- 상태: in-progress
- 브랜치: `feature/data/supplemental-official-policy-ingestion`
- 계획: [Data 06 Supplemental Official Policy Ingestion](../../develop_plan/data/06_supplemental_official_policy_ingestion.md)
- 주차 Slice: `DTL5-1` / `W5-D1`
- 현재 Gate: `SOP-G0_PASS`, `SOP-G1_PASS`, `SOP-G2_PASS`
- 다음 Slice: SOP3 Source Adapter·판정 fixture

## 목적

사용자 제공 `청년정책_데이터수집_완료.xlsx`를 바로 정책으로 적재하지 않고,
결정적 후보 inventory로 정제한다. 현재 온통청년·복지로 snapshot과 실제
PostgreSQL을 먼저 대조해 중복을 제외하고, robots·이용 조건·공개 목록·상세·
identity·요청 예산을 확인한 공식 Source만 Adapter 구현 대상으로 승인한다.

## Forest 범위

- SOP0: XLSX URL 64행의 lineage, exact 반복, 같은 URL·다른 제목과 문구 오류 격리
- SOP1: 승인 aggregator snapshot과 실제 DB의 ID·URL·제목 선행 감사
- SOP2: 공식 Source군의 운영 주체·robots·조건·allowlist·요청 예산 판정
- 미수행: Source Adapter, Raw 수집, 정규화, 신규 Policy 적재, API·Browser 인수

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| SOP0 | completed | URL 64행 → 후보 identity 60개, exact 반복 4행 축약, URL 충돌 3개 격리 |
| SOP1 | completed | exact duplicate 26, review 11, potentially new 19, not assessed 4 |
| SOP2 | completed | approved 4, blocked 1, rejected 9; 승인 Source별 allowlist·예산 고정 |
| SOP3 | pending | Adapter·offline fixture 미구현 |
| SOP4 | pending | 제한 actual·PostgreSQL 미수행 |
| SOP5 | pending | Source 확대·Forest 완료 판정 미수행 |

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
| 복지로 | `ffa74ef47e6048109f11bf40d1ac5e15` | `2026-08-06T09:19:03.630716+09:00` | 461 | `2026-08-17T11:29:19.985062+09:00` | 461 |
| 온통청년 | `6add34f7aad9456ab0abb19175b7621c` | `2026-08-06T09:18:54.586978+09:00` | 2,695 | `2026-08-17T11:29:19.985062+09:00` | 2,698 |

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

`2026-08-17T11:29:04+09:00`까지 공식 페이지와 `robots.txt`를 제한 확인했다.
승인은 원문 재배포 허가가 아니라, 출처를 보존한 최소 정책 사실을 정해진
목록 1회·상세 최대 3회·요청 시작 간격 2초로 읽을 수 있다는 의미다.

| Source군 | 상태 | stable identity | 판정 핵심 |
| --- | --- | --- | --- |
| 고용24 정책 | approved | `systId` | 공개 목록·상세, robots 허용, 출처 표시 최소 사실 |
| LH 임대 공고 | approved | `panId` | 공개 임대 목록·상세, 로그인·파일 경로 제외 |
| 한국장학재단 장학 | approved | `pg` | 공개 장학 landing·상세와 신청 기간 재현 |
| 서민금융진흥원 상품 | approved | detail page key | 공개 전체보기·상품 상세, 인증·상담 경로 제외 |
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
- K-Startup: [robots 차단 근거](https://www.k-startup.go.kr/robots.txt)

## 주요 변경 파일

- `scripts/build_supplemental_policy_inventory.py`
- `scripts/audit_supplemental_policy_duplicates.py`
- `collectors/supplemental_inventory.py`
- `data/schema/supplemental_official_policy_inventory.schema.json`
- `data/schema/supplemental_official_policy_duplicate_audit.schema.json`
- `data/reference/supplemental_official_policy_inventory.json`
- `data/reference/supplemental_official_policy_duplicate_audit.json`
- `tests/test_supplemental_policy_inventory.py`

## 설계 결정

- Source와 Policy 후보를 분리하고 XLSX 행을 Source 승인으로 해석하지 않는다.
- exact 반복은 identity 하나로 축약하되 모든 원래 행 번호를 보존한다.
- URL 충돌·범용 홈·검증되지 않은 서류 문구는 accepted 후보로 승격하지 않는다.
- direct ID와 canonical URL만 확정 중복으로 제외하고 제목 일치는 review에 둔다.
- 승인 Source의 실행 경계는 목록·상세 allowlist, stable identity와 요청 예산이
  모두 있을 때만 열린다.
- K-Startup의 robots 차단은 Browser나 다른 endpoint로 우회하지 않는다.
- PostgreSQL 감사 산출물에는 DB 비밀번호·연결 문자열·Raw 본문을 남기지 않는다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| inventory·audit Schema와 semantic 단위 테스트 | `9 passed, 63 subtests passed` |
| 같은 XLSX builder 재실행 | inventory SHA-256 동일(`8be3b437…8bcb23d`), 결정성 확인 |
| 중복 Gate·지역 inventory·aggregator loader 관련 회귀 | `30 passed, 1 warning, 118 subtests passed` |
| 실제 PostgreSQL aggregator baseline load | 복지로 461·온통청년 2,698 row 읽기 성공 |
| 직접 URL ID 감사 | 11행·고유 ID 10개 모두 exact duplicate |
| 공식 robots 제한 GET | 고용24·LH·한국장학재단·서금원 허용, K-Startup 대상 경로 차단 확인 |
| 승인 Source 목록·상세 preflight GET | 4개 Source·8개 URL 모두 HTTP 200·식별 문구 확인, 본문 미저장 |
| 문서 링크·상태·필수 heading 검증 | `Documentation validation passed` |
| whitespace 검증 | `git diff --check` 통과(CRLF 안내만 출력) |

전체 저장소 Data 회귀는 SOP3 Adapter 구현 뒤 실행하며 이번 Slice에서는 변경한
inventory·중복 기준선과 기존 교차 Source 경계의 관련 회귀만 수행했다.

## 남은 작업

- SOP3: 승인 4개 Source Adapter, 목록·상세·누락·drift·실패 fixture와 offline replay
- SOP3: 26 duplicate·11 review·19 잠정 신규를 원문 기준으로 재판정
- SOP4: 승인 Source별 목록 1회·상세 3~5건 이내 actual과 Raw provenance
- SOP4~SOP5: accepted·duplicate·review·closed·failed 분리, PostgreSQL → API → Browser 인수
- Data 05·온통청년·복지로·Release 1 golden 전체 회귀와 `SOP-G5` Forest 판정

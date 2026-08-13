# Data 05 Regional Youth Policy Ingestion Forest 개발 기록

## 작업 정보

- 작업일: `2026-08-11`
- 작업 영역: Data
- 상태: in-progress
- 브랜치: `feature/data/regional-youth-policy-ingestion`
- 시작 커밋: `ee23bc80e642e3b4dccd1f803abf61d2a02fc0b8`
- 관련 계획: [Data 05 Regional Youth Policy Ingestion](../../develop_plan/data/05_regional_youth_policy_ingestion.md)

## 목적

광역자치단체 청년정책 포털 후보를 검증 가능한 repository inventory로 고정하고,
승인 전 후보와 실제 운영 Source를 구분할 실행 계약을 만든다.

## Forest 범위

- 17개 지역 포털 후보 inventory와 상태 관리
- Source preflight와 승인된 목록·상세 경로
- 지역 고유성·신청 가능성·온통청년/복지로 중복 판정
- 제한 actual 수집과 PostgreSQL·API·Browser 인수

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| RYP0 | completed | 17개 후보 JSON·Schema·계약 테스트 14개와 39개 subtest 통과 |
| RYP1 | completed | 17개 상세 identity, 13개 승인·3개 차단·1개 제외 |
| RYP2 | completed | 공통 profile·discovery·runner 경계와 경북 Adapter·offline replay |
| RYP3 | completed | 지역 evidence·신청 상태 Gate와 경북 Runtime 격리 |
| RYP4 | completed | snapshot·PostgreSQL 기준선과 보수적 교차 Source 제외 Gate |
| RYP5 | completed | 경북 JSON·부산 HTML·서울 Browser actual과 DB·API·Browser 인수 |
| RYP6 | completed | 승인 13개 Source 4,606 identity 전체 판정·accepted 18건 DB 동기화·RYP-G4 pass |
| RYP7 | completed | review 1,903건 Source별 사유·필드 coverage 감사와 Source-scope 승격 계약 고정 |
| RYP8 | in-progress | 충북 313건 보강 뒤 반복 navigation timeout으로 중단, legacy null 7,091개 감소 필요 |
| RYP9 | planned | 전체 재판정·accepted DB 동기화·지역 검색 DB→API→Browser 인수 |

## 구현 내용

### RYP0 - 실행 inventory

- `광역자치단체별 청년정책사이트 정리.xlsx`의 `Sheet1!A2:C18`을 읽어
  17개 포털 후보를 repository JSON으로 변환했다.
- 입력 파일명·시트·범위와 SHA-256을 evidence로 기록하고 XLSX binary를
  Runtime 계약으로 사용하지 않는다.
- 모든 Source를 `candidate`로 시작하며 `source_id`, 승인 목록·상세 경로와
  요청 예산은 RYP1 승인 전까지 비워 둔다.
- `청년정책_데이터수집_완료.xlsx` 32행의 부산 상세 공고는 구현·승인 Source가
  아니라 RYP1 탐색을 돕는 `detail_candidate` seed로만 보존했다.

### RYP1 - 홈페이지 탐색·Source 승인

- 17개 홈에서 운영 주체, robots, 약관·라이선스 표시, 기술 접근, 정책
  목록·상세 경로와 identity를 제한 확인했다.
- HTTP 중심 1차 판정은 부산·대구·인천·광주 통합·대전·울산·강원·전북·경남
  9개 승인과 7개 차단을 만들었으나 최종 판정으로 사용하지 않았다.
- 전남 구 포털은 robots가 홈만 허용하고 현행 통합 플랫폼으로 대체되어
  `rejected`로 판정했다.
- `RegionalSourceInventoryValidator`가 승인 상태·preflight·Source ID·allowlist·
  요청 예산·행정구역 mapping의 교차 필드 조합을 검사한다.
- 명시적 개방 라이선스가 없는 승인 Source는 원문을 재배포하지 않고 최소 정책
  사실과 provenance만 Runtime에서 처리한다.

### RYP1 보완 - Browser Discovery 재검증 완료

사용자가 요구한 입력 계약은 목록 endpoint가 아니라 공식 홈 URL이다. 기존
preflight는 원시 HTTP 접근을 우선해 Browser에서 사용자처럼 메뉴·검색·선택을
거쳐 상세에 도달할 수 있는 Source를 충분히 평가하지 못했다.

서울 청년몽땅정보통을 Browser로 다시 확인해 다음 경로를 재현했다.

```text
홈 → 맞춤서비스 → 서울시 정책 90건·자치구 정책 21건
  → 청년 부동산 중개보수 및 이사비 지원사업 상세
```

상세에서 `plcyBizId=V202600006`, 주관기관, 지원내용, 신청기간, 지원규모,
연령·학력·취업상태, 참여제한, 신청절차·제출서류 label과 공식 URL을 확인했다.
따라서 서울의 `technical_access=blocked`와 Browser collection 가능성을 분리했다.
같은 기준으로 17개 사이트를 재검증해 모두 상세 identity까지 도달했다.

- `http_html` 승인 8개: 부산, 대구, 인천, 광주 통합, 대전, 울산, 전북, 경남
- `http_json` 승인 1개: 경북
- `browser` 승인 4개: 서울, 강원, 충북, 제주
- 차단 3개: 세종, 경기, 충남은 상세 도달 후 robots 경계에서 중단
- 제외 1개: 전남 구 포털은 현행 통합 플랫폼과 중복되고 robots가 홈만 허용

경북은 사용자 제공 `/policy/list.tc?mn=2379&pageNo=5069`를 다시 확인해 화면
렌더링과 `POST /policy/list.json` 200 JSON, `POST /policy/detail.modal` 200
상세 HTML을 재현했다. robots의 `/policy/list.tc/` 규칙은 실제 `.tc` 뒤에 `/`가
없는 목록과 JSON·modal 경로에 일치하지 않는다. 표본 `no=1098`의
`2026 경북 청년 행복카드 지원사업`에서 정책유형·지역·지원내용·규모·기간·기관·
문의처·첨부파일을 확인해 `http_json` Source로 승인했다.

inventory Schema를 `1.1.0`으로 올려 `browser_access`, 마지막 discovery 상태,
collection mode, interaction budget, action profile, 목록 관찰 수, 상세 표본 identity와
실패 근거를 필수화했다. Domain validator는 승인 Source의 Browser 접근·상세
evidence와 collection mode별 HTTP 접근을 검사하고, 비승인 Source가 실행 mode나
allowlist를 주장하지 못하게 한다.

### RYP2 - 공통 실행 경계와 경북 Source Adapter

- `RegionalSourceProfile` loader가 inventory `1.1.0`의 승인 상태, collection mode,
  allowlist, request·interaction 예산과 action profile을 실행 전에 검증한다.
- `BrowserDiscoveryEngine`은 합성 페이지에서 DOM 역할·텍스트·label 의미로
  정책 메뉴·목록·상세를 찾고 `dl`·`table` label의 공통 field 후보를 만든다.
  profile replay에서 action 순서, 상세 identity나 필수 field가 달라지면 정책
  0건 성공이 아니라 drift로 격리한다.
- `BrowserRunner`는 JSON stdin/stdout subprocess, timeout, non-zero exit와
  malformed success를 분류한다. 반환 action trace를 요청 profile과 다시
  대조하며 DB나 정책값 추정을 소유하지 않는다.
- 공통 `HttpClient`에 cookie jar와 form POST를 추가했다. 기존 GET의 retry·429·
  pacing·redaction 경계를 그대로 재사용한다.
- 경북 Collector는 승인 profile을 읽고 홈 GET으로 cookie·CSRF를 얻은 뒤
  `POST /policy/list.json`과 `POST /policy/detail.modal`만 호출한다. page 1,
  목록 1회, 상세 최대 3건과 요청 시작 간격 최소 2초를 넘으면 요청 전에
  거부한다.
- 목록 응답, 목록 item과 상세 modal은 서로 다른 Raw 역할로 보존한다. 목록
  item은 parent ID, 상세는 external ID로 관계를 검증하고 SHA-256·수집 시각·
  공식 URL을 남긴다. 전체 parse가 성공하기 전에는 Raw를
  쓰지 않아 drift가 partial Raw를 남기지 않는다.
- `GyeongbukYouthExtractor`가 `no`를 external ID로 고정하고 제목·지원 내용·기간·
  시행기관·공개 시설 연락처·필요 서류를 `ExtractedPolicy`와 provenance로
  전달한다. 지역 포털 관할만으로 지역 고유성을 추정하거나 온통청년·복지로
  중복을 자동 삭제하지 않는다.
- Registry·CLI·Runtime replay에 `regional-gyeongbuk-youth-platform`을 등록했다.
  최소 fixture Raw를 두 번 offline replay해 같은 NormalizedProgram을 얻었다.

제한 실사이트 preflight는 임시 Raw root에서 요청 3회로 수행했다. 목록 총
243건과 표본 `no=1098`, `2026 경북 청년 행복카드 지원사업` 상세 한 건을
확인했고 정규화까지 통과했다. 임시 Raw는 자동 삭제했으며 실제 HTML·JSON을
Git에 추가하거나 PostgreSQL에 적재하지 않았다.

### RYP3 - 지역 고유성·신청 가능성 판정

- `RegionalPolicyEvidence`가 시행기관, 지원 대상 지역, 신청 채널, 추가 혜택,
  Source 지역과 신청기간의 공개 원문을 locator·Raw provenance와 함께 보존한다.
- `RegionalPolicyDecision`은 지역 판정과 신청 상태를 분리한다. 지역 판정은
  `regional_confirmed`, `regional_review_required`, `non_regional`, 신청 상태는
  `open`, `scheduled`, `closed`, `review_required`다.
- 포털 관할만으로 지역을 만들지 않는다. Source 지역·시행기관·지원 대상이
  같은 canonical 관할을 가리켜야 `regional_confirmed`이며 전국 또는 다른 지역은
  `non_regional`, 근거 부족은 `regional_review_required`다.
- 광역 Source 안의 시·군·구는 canonical ancestor 관계로 검증하고 해당 기초
  지역 include rule을 유지한다. matched 지역 근거는 기존
  `kr-bjd-20260803` resolver와 NormalizedProgram 1.2.0 계약을 그대로 사용한다.
- 신청기간 두 날짜는 수집 시점의 KST 날짜로 open·scheduled·closed를 판정한다.
  `상시`만 명시적 open으로, 실제 소진 상태가 없는 `예산 소진 시까지`, 누락·
  잘못된 기간은 `review_required`로 두어 open으로 추정하지 않는다.
- 경북 Source mapper는 `sprvsnInstNm`, `policyScl`, `rgnSeNm`, 신청기간과 상세
  대응 field를 common evidence로 넘긴다. 두 판정이
  `regional_confirmed + open`인 정책만 canonical include evidence를 붙여
  Normalizer로 전달한다.
- Runtime replay는 모든 경북 추출 건의 비밀 없는 판정과 evidence를
  `regional_decisions`로 반환하고, 그 밖의 정책을 `regional_skipped_count`로
  집계한다. DB·API Schema는 변경하지 않았다.

RYP2 actual fixture `no=1098`은 시행기관·지원 대상·Source 지역이 모두 경상북도로
확인돼 `regional_confirmed`지만 신청기간 `2026-06-01`~`2026-06-15`가 수집일
`2026-08-11`보다 앞서 `closed`다. 따라서 기존 RYP2 offline replay의 추출 1건은
RYP3에서 사용자 정책 0건·지역 Gate 제외 1건으로 바뀌며 거짓 open 정책을 만들지
않는다. 실제 Source 재호출이나 PostgreSQL 적재는 수행하지 않았다.

### RYP4 - 온통청년·복지로 교차 Source 제외

- `AggregatorBaseline`은 온통청년·복지로별 최신 완료 snapshot ID·완료 시각·
  item 수와 읽기 전용 PostgreSQL row 수·확인 시각을 하나의 `baseline_id`로
  고정한다. 두 Source 중 snapshot이나 DB row가 빠지면 open 지역 후보를
  승인하지 않는다.
- 명시적 aggregator external ID, canonical URL, 발행기관이 포함된 공식 공고
  identity의 exact 일치만 확정 중복으로 제외한다. URL은 fragment와 `utm_*`
  추적값을 제거하되 query의 사업 identity는 유지한다.
- 제목·기관·canonical 지역·신청기간·지원내용이 모두 정규화 일치하면 의미상
  후보지만 자동 병합하지 않고 `duplicate_review_required`로 격리한다. 제목만
  같고 다른 필드가 명확히 다르면 신규 정책을 유지하며, 비교 필드가 누락되면
  검토 대상으로 둔다.
- Runtime은 accepted만 Importer에 전달한다. 제외와 review는
  `cross_source_skipped_count` 및 CollectionRun `skipped_count`에 포함하고,
  Source 내부 동일 identity만 기존 `duplicate_count`로 유지한다.
- `CrossSourceDecisionManifest`는 기준선, 후보·일치 identity, reason code,
  match field와 원문을 복원하지 않는 SHA-256 fingerprint를
  `runtime/decisions/`에 결정적으로 저장한다. 기존 aggregator Policy row는
  조회만 하며 수정·삭제·provenance 합성을 하지 않는다.

합성 계약 fixture 7건은 확정 ID·URL·공고 identity, 전체 fingerprint review,
동일 제목 근거 부족, 동일 제목 다른 사업과 신규 정책을 검증했다. 경북 actual
fixture는 현재 closed라 중복 기준선 없이도 RYP3에서 먼저 격리된다. 같은 Raw를
`2026-06-10` open으로 고정한 테스트에서는 무관한 기준선과 대조한 뒤
`accepted_regional`과 결정 manifest를 생성했다. 실 PostgreSQL actual 적재와
정책 row 생성 여부 대조는 RYP5 범위로 남겼다.

### RYP5 - 대표 Source actual 파일럿

- 대표 유형은 경북 `http_json`, 부산 `http_html`, 서울 `browser`로 고정했다.
  각 Source에서 목록 1회와 상세 3건만 관찰해 요청·상호작용 예산을 지켰다.
- 경북 목록 요청에 공식 `신청중` 필터를 적용하고, 목록의 지역구분·시행기관·
  지원대상 evidence가 일치하는 후보를 상세 예산 안에서 우선했다. 이는
  후보 선택일 뿐 RYP3 승인 Gate를 완화하지 않는다.
- 경북 포털이 대상 문구에 쓰는 `경북 주소`만 `경상북도 주소`로 확장해
  canonical resolver에 전달한다. 원문은 Raw와 `source_fields`에 그대로 남고
  다른 약칭·포털 관할은 지역 근거로 추정하지 않는다.
- 부산 Adapter는 공식 목록 HTML의 `bizSid` identity와 제목·상태·기관·기간,
  상세의 신청기간·담당기관·지원대상을 Raw·Extracted로 연결한다. `청년`만
  명시된 대상은 부산 거주로 추정하지 않고 review로 유지한다.
- 서울은 링크가 `#none`이고 클릭 뒤 `plcyBizId`가 정해지는 JavaScript 목록을
  in-app Browser로 실제 이동했다. 최대 3건, 승인 list/detail host와 identity,
  action trace를 검증한 구조화 Browser 관찰만 Runtime Raw로 저장한다.
- Runtime과 Backend 중복 기준선 로더를 세 regional Source에 공통 적용했다.
  실제 accepted가 처음 발생하며 기준선 read transaction 뒤 write transaction을
  열 때 `InvalidRequestError`가 발생하는 기존 경계를 발견했고, read transaction을
  명시적으로 종료한 후 쓰기를 시작하도록 수정했다. 최초 실패 실행은 정책을
  쓰지 않았고 CollectionRun 감사 기록만 남았다.

actual 판정 수치는 다음과 같다.

| Source | Raw | 추출 | 지역·신청 승인 | review·closed | 교차 중복 제외 | DB 결과 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 경북 JSON | 7 | 3 | 1 | 2 | 0 | 최초 `inserted=1`, 동일 Raw `unchanged=1` |
| 부산 HTML | 7 | 3 | 0 | 3 | 0 | 정책 0건, `skipped=3` |
| 서울 Browser | 7 | 3 | 0 | 3 | 0 | 정책 0건, `skipped=3` |

경북 `external_id=1094`, `2026년 꿈이음 청춘카페 지원사업`은 온통청년
2,695건·복지로 461건 최신 snapshot/DB 기준선과 대조해 신규 지역 정책으로
판정했다. 애플리케이션 DB를 Alembic `20260803_0004`에서 head
`20260810_0006`으로 올린 뒤 Policy ID `9509`로 적재했다. 상세 API와 실제 API
모드 React Browser에서 source ID, 제목, 경상북도, 접수 중,
`2026-04-01~2026-12-19`, 자격 원문과 공식 원문 링크가 DB와 일치했다. 현재
Source에는 구조화 가능한 서류·시설 문의처가 없어 Eligibility Summary는 이를
없음/미확인으로 표시하며 값을 합성하지 않는다.

같은 Raw 재실행은 동일 identity와 business 값으로 `unchanged=1`이었고,
부산 detail 제목 drift는 partial Raw 없이 실패하며 서울 캡처의 detail identity
drift도 저장 전에 거부했다. Browser 확인 시 서울 목록의 원시 HTTP도 200으로
응답하는 긍정적 변화를 관찰했지만 RYP1 승인 mode를 이번 Slice에서 소급
변경하지 않았다. RYP6에서 이용 조건과 함께 재확인한 뒤에만 HTTP mode 전환을
검토한다.

## 주요 변경 파일

- `data/reference/regional_youth_policy_sources.json`
- `data/schema/regional_youth_policy_source_inventory.schema.json`
- `collectors/regional_sources.py`
- `collectors/regional_profile.py`
- `collectors/regional_discovery.py`
- `collectors/browser_runner.py`
- `collectors/gyeongbuk_youth.py`
- `collectors/regional_pilot.py`
- `collectors/regional_policy_gate.py`
- `collectors/cross_source_duplicate.py`
- `collectors/http.py`
- `collectors/runtime.py`
- `backend/app/services/aggregator_baseline.py`
- `backend/app/services/runtime_importer.py`
- `scripts/import_runtime_data.py`
- `scripts/import_seoul_browser_capture.py`
- `collectors/__init__.py`
- `data/fixtures/regional/`
- `tests/test_regional_policy_gate.py`
- `tests/test_cross_source_duplicate.py`
- `backend/tests/test_aggregator_baseline.py`
- `tests/test_regional_discovery.py`
- `tests/test_browser_runner.py`
- `tests/test_gyeongbuk_youth.py`
- `tests/test_regional_pilot.py`
- `tests/test_regional_source_inventory.py`
- `docs/development/develop_plan/data/05_regional_youth_policy_ingestion.md`
- `docs/development/develop_plan/data/06_supplemental_official_policy_ingestion.md`

## 설계 결정

### Source 관할 라벨과 canonical 지역 분리

XLSX는 광주와 전남을 나눈 17개 포털을 제공하지만 현재
`kr-bjd-20260803`은 `전남광주통합특별시(1200000000)`를 활성 지역으로 두고
광주 `2900000000`과 전남 `4600000000`을 `2026-07-01` 퇴역으로 보존한다.

RYP0에서는 포털 후보 수를 임의로 줄이거나 후계 지역으로 자동 치환하지 않았다.
RYP1 제한 탐색에서 기존 광주 센터가 연결하는 현행 공식 사이트가
전남광주통합특별시 청년통합플랫폼임을 확인해 광주 Source를 활성 통합 코드
`1200000000`으로 승인했다. 전남 구 포털은 비승인 lineage와 퇴역 코드로
남겼다. 개별 정책의 실제 지역 rule은 RYP3 상세 원문 evidence로 결정한다.

### 후보와 승인 Source 분리

홈 URL과 상세 seed는 Source 발견의 입력일 뿐 승인 목록·상세 endpoint가 아니다.
현재 inventory `1.1.0`은 RYP1 최종 실행 경계다. `discovery.status`와
`collection_mode`를 분리하고 17개 모두의 Browser action profile을 검증해 Source
ID·allowlist·interaction/request 예산을 다시 승인했다. RYP2는 이 inventory 밖의
경로를 호출하지 않는다.

## 검증 결과

2026-08-11에 다음 검증을 실행했다.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_administrative_regions.py tests\test_regional_source_inventory.py -q
```

- 결과: `17 passed, 45 subtests passed`
- inventory JSON Schema, 17개 관할 라벨·URL 유일성, HTTPS·비밀 없는 URL,
  17개 결정 상태, 승인·비승인 실행 경계, 활성·퇴역 행정구역 code, 부산 탐색
  seed와 잘못된 교차 필드 조합 거부를 확인했다.
- 이후 RYP1 재검증에서 아래 관련 계약·행정구역 회귀를 실행했다.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_administrative_regions.py tests\test_regional_source_inventory.py -q
```

- 결과: `20 passed, 50 subtests passed`
- Browser Discovery와 공개 HTTP로 17개 상세 도달, collection mode 분기,
  Browser-only 승인, robots 차단 evidence, 비승인 실행 경계와 잘못된 교차 필드
  조합 거부를 확인했다.

RYP2 구현 뒤 공통 HTTP·profile·discovery·runner, 경북 Collector·Extractor와
Runtime replay 회귀를 실행했다.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_collectors_http.py tests\test_collectors_cli.py tests\test_regional_source_inventory.py tests\test_regional_discovery.py tests\test_browser_runner.py tests\test_gyeongbuk_youth.py tests\test_runtime_replay.py -q
.\.venv\Scripts\python.exe -m pytest tests -q -rs
```

- RYP2 관련 결과: `55 passed, 54 subtests passed`
- 전체 Python 결과: `193 passed, 6 skipped, 77 subtests passed`
- skip 6건은 `TEST_DATABASE_URL` 미설정으로 건너뛴 기존 PostgreSQL 통합
  테스트다. RYP2는 DB Schema나 적재를 바꾸지 않고 offline Runtime replay까지
  담당하며 경북 PostgreSQL actual은 RYP5 완료 기준이다.
- 제한 실사이트 preflight는 요청 3회, 목록 243건, 상세 표본 `no=1098` 1건과
  정규화 성공을 확인했다. TemporaryDirectory를 사용해 응답 Raw를 남기지 않았다.

RYP3 구현 뒤 지역·신청 상태 Gate, 경북 mapper·Runtime 격리와 기존 지역
Normalizer 회귀를 실행했다.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_regional_policy_gate.py tests\test_gyeongbuk_youth.py tests\test_runtime_replay.py tests\test_normalization.py tests\test_administrative_regions.py tests\test_collectors_cli.py -q
.\.venv\Scripts\python.exe -m pytest tests -q -rs
```

- RYP3 관련 결과: `53 passed, 16 subtests passed`
- 전체 Python 결과: `199 passed, 6 skipped, 89 subtests passed`
- skip 6건은 `TEST_DATABASE_URL` 미설정인 기존 PostgreSQL 통합 테스트다.
  RYP3는 정규화 전 Gate이며 DB·API·Migration 변경과 actual 적재는 수행하지
  않았다. 경북 actual DB 통합은 RYP5 완료 기준이다.
- 합성 fixture 12건은 지역 고유·시군구·전국·타 지역·모호 판정과
  open·scheduled·closed·상시·예산 상태를 검증했다. 경북 actual fixture는
  `regional_confirmed + closed`로 격리되고 같은 Raw replay 결과가 결정적이다.

```powershell
python scripts\validate_docs.py
git diff --check
```

- 결과: 문서 검증 통과, whitespace 오류 없음
- 자동화 테스트는 외부 웹 요청이나 PostgreSQL을 사용하지 않았다. RYP1
  preflight와 RYP2 경북 제한 preflight의 응답 원문은 Git에 저장하지 않았다.

RYP4 구현 뒤 교차 Source 판정·기준선 loader·경북 Runtime·CollectionRun 집계와
기존 정규화 회귀를 실행했다.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cross_source_duplicate.py backend/tests/test_aggregator_baseline.py tests/test_gyeongbuk_youth.py tests/test_runtime_replay.py tests/test_runtime_import_cli.py tests/test_regional_policy_gate.py tests/test_normalization.py -q
.\.venv\Scripts\python.exe -m pytest tests backend/tests -q -rs
```

- RYP4 관련 결과: `53 passed, 21 subtests passed`
- 전체 Python 결과: `317 passed, 23 skipped, 96 subtests passed`
- 전체 실행의 skip 23건은 `TEST_DATABASE_URL` 미설정 PostgreSQL 테스트다.
  이 중 새 RYP4 PostgreSQL 기준선 통합 테스트는 기존 임시 pgpass와 전용
  `cheongnyeon_alimi_test`를 명시한 별도 실행에서 `1 passed`를 확인했다.
- SQLite 단위 테스트와 별도로 실제 PostgreSQL에서 완료 snapshot descriptor와
  aggregator Policy·region rule 읽기, 기준선 row 수와 deterministic ID를
  검증했다. 기존 Policy 수정·삭제와 외부 웹 요청은 수행하지 않았다.

RYP5 구현 뒤 대표 Adapter·Browser capture·실제 DB transaction 경계와 전체
회귀를 실행했다.

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests backend\tests -q -rs
.\.venv\Scripts\python.exe -B -m pytest `
  tests\integration\test_cross_source_duplicate_baseline.py `
  tests\integration\test_runtime_to_database.py -q -rs
Set-Location frontend
npm.cmd test
npm.cmd run build
Set-Location ..
.\.venv\Scripts\python.exe -B scripts\validate_docs.py
git diff --check
```

- 전체 Python: `324 passed, 24 skipped, 96 subtests passed`. skip 24건은
  `TEST_DATABASE_URL`을 넣지 않은 전체 실행의 PostgreSQL 테스트다.
- 전용 `cheongnyeon_alimi_test`와 pgpass를 명시한 관련 PostgreSQL 통합:
  `3 passed`. 기준선 read transaction 종료 뒤 regional policy write,
  Runtime atomic·idempotent 적재를 실제 PostgreSQL에서 확인했다.
- Frontend: `50 passed`, TypeScript·Vite production build 통과.
- 문서 검증과 `git diff --check` 통과. 생성된 Frontend test/build 산출물은
  검증 뒤 제거했다.
- 실제 인수는 PostgreSQL 1건 삽입·동일 Raw 1건 unchanged, Policy 상세 API와
  React Browser 일치까지 확인했다. 실행하지 않은 광역 전체 pagination이나
  다른 지역 actual을 RYP5 성공으로 기록하지 않았다.

## 남은 작업

- RYP6 전체 pagination에서 accepted·duplicate·review·closed·failed 합계와
  목록 total·종료 조건을 대조하고 Release 1 golden 회귀로 Forest 최종 판정
- 서울 HTTP mode의 긍정적 drift는 현재 Browser 구현을 변경하지 않고 이용
  조건과 robots 범위를 다시 승인할 때만 별도 전환

### RYP6 - 공통 확대 Adapter와 첫 actual batch

`2026-08-11`에 inventory를 `1.2.0`으로 올리고 17개 지역의 구현 상태를
확정했다. 기존 경북·부산은 `implemented_http`, 서울과 나머지 승인 10개는
`implemented_browser`, 세종·경기·충남은 `blocked`, 구 전남 포털은
`rejected`다. blocked·rejected Source는 실행 allowlist에 넣지 않았다.

`RegionalBrowserCaptureStore`는 Source별 승인 목록·상세 identity, 목록 page,
total·다음 page 여부, action trace, 상세 최대 3건과 제목 일치를 검증한 뒤
JSON Raw로 저장한다. `RegionalBrowserExtractor`는 같은 Raw만 재생하며 공통
지역성·신청 가능성·온통청년/복지로 중복 Gate를 통과시킨다. 실제 capture
입력은 Git 제외 Runtime 파일이고 합성 Seed로 사용하지 않는다.

`RegionalBatchCheckpoint`는 한 page에서 발견한 identity와 판정의 집합 일치,
중복 identity, total drift, 조기 종료를 거부한다. 상태 파일은
`runtime/decisions/regional-checkpoints`에 원자적으로 교체하며 Git에 넣지 않는다.
이번 실행은 Source당 상세 1건의 제한 actual이므로 아직 전체 pagination
checkpoint로 기록하지 않았다.

`2026-08-13`에는 Browser 캡처 CLI와 체크포인트를 연결했다. 캡처 계약은 한
page의 전체 `discovered_ids`와 상세 최대 3건 batch를 분리하며, 상세를 아직
가져오지 않은 identity도 pending으로 보존한다. 입력 배열 전체를 먼저 검증한
뒤 각 page Raw와 체크포인트를 저장하고, 새 Raw 저장이나 체크포인트 갱신이
실패하면 해당 호출이 생성한 Raw만 제거한다. 기존 제한 actual 입력은
`discovered_ids` 생략을 허용하지만 전체 pagination에서는 생략하지 않는다.

| Source | 실제 표본 판정 | PostgreSQL 결과 |
| --- | --- | --- |
| 강원 | 청년 대상 근거 없음, review | 0건 |
| 충북 | 지역·open·비중복 | 신규 1건, 재실행 unchanged 1건 |
| 제주 | 중앙 canonical URL 복수 후보, duplicate review | 0건 |
| 대구 | 지역 근거 부족, review | 0건 |
| 인천 | 지역·open, material field 차이 | 신규 1건, 재실행 unchanged 1건 |
| 전남광주 | 지역·open·비중복 | 신규 1건, 재실행 unchanged 1건 |
| 대전 | 신청기간 해석 불가, review | 0건 |
| 울산 | 청년 대상 근거 없음, review | 잘못 생성된 표본 row 1건 제거 후 0건 |
| 전북 | 지역·open·비중복 | 신규 1건, 재실행 unchanged 1건 |
| 경남 | 지역·open·비중복 | 신규 1건, 재실행 unchanged 1건 |

공통 regional eligibility mapper는 RYP5의 서울·부산·경북과 RYP6 확대 10개를
합친 13개 승인 Source에서 실제 상세의 연령·지원대상·제외·필요서류·기관 문의처를
`SOURCE_FIELD` evidence와 함께 기존 EligibilitySummary 1.0.0에 연결한다.
retained 5건은 모두 `coverage=partial`, 기관 문의처 1건씩이며 인천·
경남은 필요서류도 1건씩 DB JSONB에 확인했다. 개인 휴대전화와 이메일은 기존
계약이 계속 거부한다. mapper 추가 후 5건이 `updated=1`씩 반영됐고 다음
재실행은 모두 `unchanged=1`이었다.

첫 인천 import는 로컬 `.env`의 `postgres` 역할과 RYP5 pgpass 역할이 달라
`UnicodeDecodeError`로 실패했다. 실패 CollectionRun은 보존하고, pgpass의
`alpha8332@127.0.0.1:5432` 연결로 `select 1`을 확인한 뒤 10개 Source를
재실행했다. 비밀번호는 출력·문서화하지 않았고 저장소 설정도 바꾸지 않았다.

초기 울산 표본은 지역 증거만으로 1건이 삽입되는 결함을 드러냈다. 제목·대상·
연령의 청년 근거를 필수로 하는 보수적 판정을 추가하고, 정확히 확인한
`id=9513/source=regional-ulsan-youth-platform/external_id=60156` row만 삭제했다.
Raw와 CollectionRun은 복구·감사 근거로 남아 있으며 새 Gate 재실행은 0건을
확인했다.

RYP6 현재 단계 검증:

- 최종 regional 계약 집중 회귀: `28 passed, 2 subtests passed`
- pgpass와 `cheongnyeon_alimi_test`를 명시한 PostgreSQL 통합: `3 passed`
- 전체 Python: `336 passed, 24 skipped, 96 subtests passed`
- `python scripts/validate_docs.py`, `git diff --check`: 통과

전체 Python skip 24건은 `TEST_DATABASE_URL`을 넣지 않은 기본 실행의 기존
PostgreSQL 조건부 테스트다. 관련 PostgreSQL 3건은 별도 명시 실행으로 통과했다.
첫 별도 실행은 설치된 드라이버와 맞지 않는 `postgresql+psycopg` URL을 사용해
3건 모두 설정 실패했고, 새 패키지를 설치하지 않고 기존 `.venv`의 `psycopg2`에
맞춘 URL로 다시 실행해 3건 통과를 확인했다.
이 첫 actual 단계에서는 전체 pagination과 Release 1 golden 최종 회귀를 아직
실행하지 않아 RYP6 완료로 기록하지 않았다.

### RYP6 - 전체 pagination·판정·DB 동기화 완료

`2026-08-13`에 승인 Source 목록을 끝까지 순회하고 checkpoint에서 중단·재개를
실제 검증했다. Browser 캡처 서버는 목록 discovery를 상세 처리보다 먼저
기록하고 `pending_ids`만 반환한다. 재개 시 처리 완료 identity를 다시 요청하지
않으며, 상세 오류는 캡처 성공으로 위장하지 않고 `failed`로 결정한다. checkpoint
계약 `1.2.0`은 failed identity를 상세 pending에서 제외한다.

| Source | 종료 근거 | 발견 | accepted | duplicate | review | closed | failed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 서울 | 시·자치구 목록 23 page 종료 | 110 | 0 | 0 | 97 | 13 | 0 |
| 부산 | 공식 현재 필터 total | 123 | 16 | 0 | 107 | 0 | 0 |
| 대구 | 다음 page 없음 | 197 | 0 | 0 | 197 | 0 | 0 |
| 인천 | `acptrun=ing` total | 28 | 0 | 0 | 28 | 0 | 0 |
| 전남광주 | `status=ing` total | 31 | 0 | 0 | 31 | 0 | 0 |
| 대전 | 목록 total | 12 | 0 | 0 | 12 | 0 | 0 |
| 울산 | 목록 total 596 + 반복 고정 1 identity | 597 | 0 | 0 | 596 | 1 | 0 |
| 강원 | 29 page·total | 337 | 0 | 0 | 12 | 0 | 325 |
| 충북 | 목록 total | 441 | 0 | 0 | 441 | 0 | 0 |
| 전북 | 실제 `strstate=ing` 8 page 종료 | 89 | 0 | 0 | 89 | 0 | 0 |
| 경북 | 공식 현재 필터 total | 61 | 2 | 1 | 58 | 0 | 0 |
| 경남 | 161 page·total | 1,447 | 0 | 0 | 28 | 1,419 | 0 |
| 제주 | 112 page 종료·반복 고정 ID dedupe | 1,133 | 0 | 0 | 207 | 924 | 2 |
| **합계** | 13개 checkpoint complete | **4,606** | **18** | **1** | **1,903** | **2,357** | **327** |

강원 2 page 이후 325건은 당시 상세 수집 실패로 failed에 보존했다. 후속 RYP8
조사에서 공식 상세 오류가 아니라 수집기가 상세마다 1 page로 복귀한 뒤 다른
page identity를 클릭하려 한 계약 문제로 정정했다. 경남은 5 page 이후 공식 카드의 `기간: 마감`, 제주는 일반
행의 모집·채용·행사 마감 표시를 목록 Raw 근거로 closed 처리했다. 목록에 신청
가능 필터가 있는 전북은 DOM에서 실제 제출 계약 `strstate=ing`을 확인해 기존
계획의 잘못된 `dateCheck=ing` 기록을 정정했다.

모든 Source를 같은 Raw로 다시 실행했다. 부산 16건·경북 2건은
`unchanged=18`이었고 나머지는 accepted 0건이었다. 최종 checkpoint의 accepted
집합과 DB를 동기화해 과거 제한 actual에서 남은 충북·인천·전남광주·전북·경남
표본 5건을 제거했다. 최종 지역 Policy row는 부산 16건·경북 2건뿐이다.

최종 검증:

- 전체 Python: `347 passed, 24 skipped, 96 subtests passed`
- PostgreSQL 통합: `8 passed`
- checkpoint·resume·accepted projection 집중 회귀: `26 passed`
- Frontend 단위: `50 passed`; lint·production build 통과
- Release 1 golden HTTP: 자연어·control 모두 1위, 231.66ms·133.23ms,
  technical verdict `pass`
- 실제 경북 `external_id=1094` DB → 상세 API → in-app Browser 대조 통과
- `python scripts/validate_docs.py`, `git diff --check`: 통과

Release 1 감사의 `gate_verdict=blocked`는 기존 수동 QA·사용성 증거 대기를
뜻한다. 자동 golden 회귀는 통과했으며 해당 수동 증거를 이번 Data 05 결과로
소급 처리하지 않았다. Data 05의 `RYP-G4`는 전체 수집 인프라 Gate로 pass다.

### RYP7 - 완료 판정 재검토와 review 사유 기준선

RYP6은 승인 Source 전체 identity를 누락 없이 판정하는 목표를 달성했지만,
사용자 검색 DB에는 부산 16건·경북 2건만 남았다. 지역별 실제 검색 가능성을
Data 05의 사용자 완료 조건으로 다시 확인해 Forest 상태를 `in-progress`로
정정했다. RYP6 결과와 `RYP-G4` 통과를 취소하지 않고 후속 RYP7~RYP9의 입력
기준선으로 사용한다.

동일 Raw를 현재 판정기로 다시 집계한 결과는 다음과 같다.

| Source | 지역 Gate accepted (중복 전) | 지역 근거 부족 open review | 기간 누락·미해석 review | 비고 |
| --- | ---: | ---: | ---: | --- |
| 부산 | 16 | 105 | 0 | 전국 재게시 2건 별도 제외 |
| 대구 | 0 | 183 | 12 | scheduled 2건 별도 |
| 광주 | 0 | 31 | 0 | 지역 근거 보강 우선 |
| 경북 | 3 | 53 | 5 | 3건 중 1건 교차 중복 제외 |
| 인천 | 0 | 17 | 11 | 기간 누락 9·미해석 2 |
| 전북 | 0 | 64 | 1 | 전국 재게시 24건 별도 제외 |
| 서울 | 0 | 3 | 94 | 종료 13건 별도 제외 |
| 충북 | 0 | 0 | 441 | 신청기간 field 미추출 |
| 대전 | 0 | 0 | 12 | 신청기간 field 미추출 |
| 강원 | 0 | 0 | 12 | 별도 상세 capture 실패 325건 |
| 울산 | 0 | 0 | 596 | 종료 1건 별도 |
| 경남 | 0 | 0 | 28 | 종료 1,419건은 승격 대상 아님 |
| 제주 | 0 | 0 | 207 | 종료 924·capture 실패 2건 별도 |

현재 공통 지역 판정은 Source 지역·지원 대상·시행기관 세 필드에 기대 지역명이
모두 있어야 통과한다. 공식 관할 정책 목록과 진행중 filter의 Source-level
provenance를 사용하지 못하는 과도하게 엄격한 부분이 확인됐다. 다음 구현에서는
이를 무조건 완화하지 않고, 고정된 공식 목록 scope와 policy-level 지역·청년
근거를 함께 요구하는 조합을 fixture와 actual 표본으로 승인한다. 실제 원문에
없는 지역·연령·기간은 합성하지 않는다.

#### RYP7 구현과 actual 감사

- `RegionalSourceScopeEvidence`를 Data 내부 판정 계약에 추가했다. scope 근거는
  같은 정책의 `list_response` provenance에 속해야 하며 공식 관할·운영 주체와
  정책별 대상 또는 시행기관 지역 근거 중 하나를 함께 만족해야 한다.
- 진행중 목록 scope는 신청기간이 null·미해석일 때만 open 보조 근거가 된다.
  정책별 명시 마감·종료일은 scope보다 우선한다.
- 모든 regional decider에서 청년 대상을 독립 판정한다. 제목·대상·연령·분류의
  명시적 청년·청소년·대학생 문구 또는 청년정책 scope와 정책별 숫자 연령의
  조합만 허용한다. 청년 포털 위치만으로는 승인하지 않는다.
- 공통 Browser capture는 각 상세 필드를 `value_extracted`,
  `label_present_value_empty`, `label_not_found`로 관찰해 다음 재캡처부터 selector
  누락과 원문 빈 값을 분리한다. 과거 Raw에는 이 관찰이 없어 호환 replay에서는
  `null_unverifiable`로 남긴다.
- `audit_regional_reviews.py`는 checkpoint outcome과 현재 replay identity가
  정확히 일치할 때만 Source별 사유·조합·필드 coverage 보고서를 원자적으로
  작성한다. Runtime 보고서는 Git 제외 경계에 둔다.

actual 보고서 집계:

| Source | review | 지역 근거 | 신청 상태 | 청년 미확인 | failed | legacy capture gap |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 부산 | 107 | 105 | 0 | 5 | 0 | 있음 |
| 충북 | 441 | 441 | 441 | 136 | 0 | 있음 |
| 대구 | 197 | 197 | 12 | 116 | 0 | 있음 |
| 대전 | 12 | 12 | 12 | 3 | 0 | 있음 |
| 강원 | 12 | 12 | 12 | 2 | 325 | 있음 |
| 광주 | 31 | 31 | 0 | 9 | 0 | 있음 |
| 경북 | 58 | 56 | 5 | 19 | 0 | 없음 |
| 경남 | 28 | 28 | 28 | 12 | 0 | 있음 |
| 인천 | 28 | 28 | 11 | 0 | 0 | 있음 |
| 제주 | 207 | 207 | 207 | 152 | 2 | 있음 |
| 전북 | 89 | 65 | 1 | 40 | 0 | 있음 |
| 서울 | 97 | 97 | 94 | 18 | 0 | 있음 |
| 울산 | 596 | 596 | 596 | 213 | 0 | 있음 |
| **합계** | **1,903** | **1,875** | **1,419** | **725** | **327** | **12 Source** |

신청 상태 route 합계 1,419건은 `application_period_missing 1,321 +
application_period_unresolved 96 + budget_exhaustion_state_unknown 2`다.
한 review가 지역·신청·청년 사유를 동시에 가질 수 있다. RYP7은 원인을 감사하고
안전한 승격 조합을 구현한 Slice이며 legacy null 12개 Source의 실제 label·값
재확인은 RYP8 범위다. actual 감사 후 checkpoint accepted 18·duplicate 1과 DB는
변경하지 않았다. 경북 `external_id=1009`는 과거 중복 Gate에서 duplicate로
제외됐지만 통합 청년 Gate에서는 `youth_target_unconfirmed`다. 두 판정 모두
미적재이므로 사용자 DB 영향은 없고 감사 보고서의
`checkpoint_decision_drift=1`로 보존했다. RYP9 재판정 때 checkpoint outcome을
현재 Gate 순서와 일치시킨다.

RYP7 검증:

- actual 감사 CLI: 13 Source·4,606 discovered·1,903 review·327 failed·
  legacy capture gap 12 Source·checkpoint drift 1건을 재현하고 종료 코드 0
- 지역 Gate·Source-scope·필드 관찰·감사 집중 회귀:
  `57 passed, 14 subtests passed`
- 전체 Python: `362 passed, 24 skipped, 96 subtests passed`
- PostgreSQL 통합: `8 passed`
- Browser capture JavaScript `node --check`: 통과
- `python scripts/validate_docs.py`, `git diff --check`: 통과

PostgreSQL 통합은 기존 로컬 전용 `_test` DB와 pgpass를 사용했으며 새 패키지를
설치하지 않았다. RYP7은 DB transaction을 실행하지 않는 actual 감사 Slice이고,
통합 테스트만 임시 테스트 transaction·migration 경계에서 실행했다.

### RYP8 부산 Source field observation 착수 (`2026-08-13`)

- 새 PC 인계 기준 `0cf1a1e`, `runtime/raw` 14,163개와
  `runtime/decisions` 49개를 확인하고 RYP7 actual 감사를 그대로 재현했다.
- 부산 공식 목록 HTML의 `meta[name=author]`, `<title>`,
  `select[name=endstat] option[selected]`을 각각 관할·운영 주체, 청년지원 taxonomy,
  현재 모집 scope locator로 고정했다. 값은 `extra.source_scope`에 staging하고
  RYP9 전에는 regional Gate의 accepted 근거로 소비하지 않는다.
- 상세 `dtif_atc`·`dtif_cont` pair에서 신청기간·담당기관·지원대상 관찰 상태를
  복원했다. 부산 review 107건의 legacy null은 0이 되었고, 원문 값 부재 2건과
  capture contract gap을 구분한다.
- unit fixture와 limited actual 목록 1건·상세 1건을 검증했다. checkpoint outcome은
  변하지 않았으며 감사 결과는 legacy gap Source `12 → 11`이다.
- 집중 회귀 `45 passed, 12 subtests passed`, 전체 Python `363 passed, 24 skipped,
  96 subtests passed`, Node syntax·문서 검증·`git diff --check`를 통과했다.
- 새 PC PostgreSQL에 전용 `alpha8332` 역할과 소유자가 일치하는
  `cheongnyeon_alimi_test`를 재구성하고 새 pgpass를 적용했다. 최초 인증·기존
  객체 권한 실패를 해결한 뒤 Backend·Data PostgreSQL 통합 `10 passed`를
  재확인했다.

### RYP8 대구·광주 field observation 보강 (`2026-08-13`)

- 대구 상세의 구조화 `dt/dd` 밖 `.view_txt` 본문에서 `지원대상`의 후속 문단과
  `지원내용: 값` 문단을 추출하도록 fixture를 추가했다. 상단 안내문의
  `담당기관·문의` 부분문자열은 전체 라벨 일치가 아니므로 evidence에서
  제외한다.
- 대구 목록의 포털명·`청년 꿀정보`·`현재 모집 중`을 `source_scope`에 staging하고
  완료 checkpoint의 accepted/review/duplicate 판정에는 적용하지 않았다. 현재
  마지막 페이지 8건만 제한 재캡처해 실제 라벨이 있던 1건은 대상·지원내용을
  `value_extracted`, 나머지 7건은 `label_not_found`로 구분했다.
- 광주는 목록 카드의 `policyView(policyId)` 클릭 뒤 상세가 열리는 계약을 고정했다.
  상세의 `참여요건`은 eligibility, `신청절차`는 application method로 매핑하고
  `신청방법` marker 앞의 중복 대상 설명은 신청 방식 값에서 제거했다.
- 광주 `policyId=1248` 한 건만 제한 재캡처했고, 광주 review coverage의
  `region_eligibility_text`와 `application_channel_text`는 각각 present 0건에서
  1건으로 바뀌었다. 대구·광주 모두 checkpoint outcome과 DB projection은
  변경하지 않았다.
- 완료 checkpoint에 이미 속한 identity만 다시 관찰할 수 있는 `/recapture`
  경계를 추가했다. 이 경계는 identity·page·total을 완료 checkpoint와 대조한
  뒤 새 Raw만 저장하며 checkpoint를 수정하지 않는다.
- 경북은 기존 HTTP/JSON + modal 계약에 이미 지역·대상·지원내용 locator가 있고
  RYP7 capture evidence gap도 없음을 확인했다. 공식 `신청중` 목록 1건·상세 1건을
  제한 재수집했으며 outcome·DB는 변경하지 않았다.
- 인천은 `지원규모`가 `지원내용`보다 먼저 매칭되던 공통 label 순서를 수정하고
  실제 `지원내용` heading을 우선했다. `지원대상 + 지원조건`을 결합해 부평구
  거주 조건을 보존하고 띄어 쓴 `문 의 처`도 인식한다. `poly_seq=110` 한 건을
  제한 재캡처했다.
- 전북은 `해당지역·담당기관명·연령제한·공고상세보기URL` 별칭을 추가했다.
  `id=129`에서 공식 신청 URL을 application channel로 새로 보존하고, 원문에
  대상·지원내용 라벨이 없는 상태와 빈 첨부파일을 서로 다른 관찰 상태로 남겼다.
- 서울은 표본 상세에서 `지원 내용`을 `지원규모`보다 우선하고
  `사업신청기간·추가단서 사항·참여제한 대상`을 각각 기간·지역 대상 조건·제외
  조건으로 고정했다. 과거 완료 checkpoint의 110개 identity와 현재 공식 목록
  identity가 교체돼 제한 recapture 조건을 만족하지 않으므로 새 Raw는 만들지
  않고 공식 상세 DOM과 fixture 회귀만 검증했다.

### RYP8 충북·울산·대전·강원·서울 신청기간 보강 (`2026-08-13`)

- 충북은 공지 상세의 `<br>` 구분 본문에서 번호가 붙은 `모집기간·모집대상`을
  읽도록 했다. `nttNo=440062` 한 건을 제한 재캡처해 신청기간 누락은
  `441 → 440`, 기간 open 근거는 `0 → 1`이 됐다.
- 울산은 상세 `dt/dd`의 `접수일정`을 신청기간으로 매핑했다. checkpoint의
  597 identity는 review 596건과 closed 1건이며, 계획의 595는 review 수가 아니라
  작업 전 신청기간 null 수다. `dataId=60156` 재캡처 뒤 null은 `595 → 594`이고,
  기간 open 1건과 연도 생략 형식으로 남은 unresolved 1건을 구분한다.
- 대전은 `h4` 다음의 빈 문단을 건너뛰어 `접수기간`을 찾고 `신청기한`과
  결합한다. 현재 공식 목록은 13건으로 완료 checkpoint 12건과 달라 `/recapture`
  경계가 실제 total 13 요청을 거부했다. checkpoint total을 거짓으로 맞추지 않고
  공식 상세 DOM·fixture 검증만 남겼으므로 감사의 기간 누락 12건은 유지된다.
- 강원 actual 첫 페이지는 실제 표가 `<th>/<td>`가 아니라
  `.skinTb-th/.skinTb-td` 행으로 구성돼 있었다. class-row selector로 신청기간,
  주관 기관, 거주·소득과 제외 조건을 추출하고
  `bizId=A2026021200300200900000001`만 제한 재캡처했다. actual 12건 중 신청기간
  누락은 `12 → 11`, 기간 open 근거는 `0 → 1`이며 실패 325건은 이번 Slice에서
  건드리지 않았다.
- 서울의 기간 미확인 17건 중 공식 상세 2건을 대조한 결과 모두
  `사업신청기간` 라벨은 있으나 값이 비어 있었다. identity가 교체된 현재 목록과
  완료 checkpoint가 맞지 않아 Raw를 우회 생성하지 않고 빈 값 observation
  fixture만 고정했다. `YYYYMMDD ~ YYYYMMDD` Gate 지원으로 전체 110건의
  `application_period_unresolved 76 → 25`, `application_period_ended 13 → 62`,
  `application_period_open 2 → 4`가 됐으며 기간 미확인 17건은 그대로다.
- replay 감사 합계는 `discovered 4,606`, `accepted 18`, `duplicate 1`,
  `review 1,903`, `closed 2,357`, `failed 327`, checkpoint drift 1로 유지됐다.
  importer나 DB 동기화는 실행하지 않았고 checkpoint 파일도 갱신하지 않았다.

검증 결과:

- Browser capture Node fixture·config: `11 passed`, syntax check 통과
- 지역 Gate·audit·expansion·normalization·pilot 집중 회귀:
  `68 passed, 12 subtests passed`
- 전체 Python: `366 passed, 24 skipped, 96 subtests passed`; skip 24건은
  `TEST_DATABASE_URL` 미주입 PostgreSQL 테스트
- 전용 `cheongnyeon_alimi_test` Data 통합: `8 passed` (기존 warning 1건)
- actual Browser 표본은 충북·울산·대전·강원·서울 공식 상세와 대조했고,
  대전 total drift 차단 및 서울 identity drift 미재캡처를 확인했다.

### RYP8 강원·제주 상세 실패 제한 복구 (`2026-08-13`)

실패 분류 결과:

| Source | 대상 | 판정 유형 | 대표 검증 | 다른 유형 |
| --- | ---: | --- | --- | --- |
| 강원 | 325 | 상세 클릭/POST의 목록 page 컨텍스트 유실 | 2·15·29 page 각 1건, 상세 row 27개 | identity 변경·동적 대기·필드 DOM 부재·삭제/비공개 미확인 |
| 제주 | 2 | 응답 성공, 구조화 field DOM 부재 | `wr_id=864`, `862` 제목·본문·등록일 확인 | identity 변경·동적 대기·클릭 계약·삭제/비공개 미확인 |

- 강원 checkpoint는 발견 순서상 1 page 12건만 captured이고 2~29 page의
  `12 × 27 + 1 = 325`건이 모두 failed였다. 공식 목록에서 2 page 첫 identity,
  15 page 첫 identity, 29 page 유일 identity를 클릭하자 별도 대기 없이 같은
  `.skinTb-tr` 27행 상세가 열렸다. 목록 page를 유지하지 않은 기존 수집기의
  `goto(listUrl) → 현재 page identity 클릭` 불일치가 원인이었다.
- 제주 두 상세는 HTTP 성공과 `.view_title`, `#writeContents`, `.mb_area`가
  존재했지만 공통 정책 field row가 없었다. 제목의 명시 기한과 등록일 연도만
  조합해 각각 `2025-08-13 19:00 마감`, `2025-08-14 마감`으로 보존했고 나머지
  필드는 `label_not_found`로 유지했다.
- `/recover`는 완료 checkpoint의 강원·제주 failed identity만 받는다. Raw를 먼저
  저장한 뒤 같은 checkpoint 범위를 replay하고 결과가 `review` 또는 `closed`일
  때만 `failed → captured/outcome`을 원자적으로 교체한다. accepted 결과는
  온통청년·복지로 중복 기준선 확인 전 자동 승격하지 않는다. enum·Schema·Seed·
  DB 계약은 바꾸지 않았다.
- 325건 전체를 재요청하지 않고 강원 대표 3건과 제주 2건만 actual 복구했다.
  강원은 `review 12/failed 325 → review 14/closed 1/failed 322`, 제주는
  `review 207/closed 924/failed 2 → review 207/closed 926/failed 0`이다.
  전체 감사는 `discovered 4,606`, `accepted 18`, `duplicate 1`, `review 1,905`,
  `closed 2,360`, `failed 322`, checkpoint drift 1로 재현됐다. importer와 DB
  동기화는 실행하지 않았다.

검증 결과:

- Browser capture syntax·fixture·config: `13 passed`
- 지역 expansion·Gate·review audit 집중 회귀: `44 passed, 12 subtests passed`
- 전체 Python: `369 passed, 24 skipped, 96 subtests passed`; skip 24건은
  `TEST_DATABASE_URL` 미주입 PostgreSQL 테스트
- 전용 `cheongnyeon_alimi_test` 통합: 첫 실행은 설치되지 않은 `psycopg` URL을
  지정해 8건이 실행 전 실패했다. 새 패키지 설치 없이 저장소 기준
  `postgresql+psycopg2`로 정정한 재실행은 `8 passed` (기존 warning 1건)
- `python scripts/validate_docs.py`와 `git diff --check` 통과

### RYP8 종료 이력 대조·강원 예지보전 감사 (`2026-08-13`)

강원 잔여 실패는 수집 당시의 공통 page-context 오류로 분류할 수 있지만 현재
상세가 전건 유지된다는 뜻은 아니다. 이를 구분하기 위해 checkpoint discovery
순서를 page size 12로 복원하고 2~10, 11~20, 21~29 page에서 회차별 1건씩 순환
선택하는 읽기 전용 canary를 추가했다. canary는 identity 존재, 클릭/POST 완료,
동적 ready selector, 제목 일치, field row, 삭제·비공개 문구를 차례로 확인하고
다음 여섯 유형 중 하나로만 분류한다.

- `healthy`
- `page_or_identity_changed`
- `detail_click_or_post_contract`
- `dynamic_render_wait`
- `response_success_without_field_dom`
- `deleted_or_private`

회차 0 actual은 page 2 `A2023100600300200900400003`, page 11
`A2024052900300200900000002`, page 21 `A2023100600300200900000192`를 최소 2초
간격으로 확인했다. 세 건 모두 목록 identity와 제목이 일치하고 상세 field row가
27개여서 `healthy`였다. 이 결과는 322건 전체의 현재 상태를 보증하지 않는다.
하나라도 비정상이면 해당 유형과 page 구간만 제한 batch 후보로 격리하며,
checkpoint·Raw·DB를 canary 단계에서 쓰지 않는다.

종료 이력과 완료 조건의 데이터 부분은 `audit_regional_ryp8.py`로 결정적으로
대조한다. 경남 checkpoint closed 1,419건과 제주 926건은 Raw replay의 closed
identity와 전건 같았고, 각 identity가 `list_response`·`list_item`·
`detail_response` provenance를 모두 보유했다. 제주 reason은 명시 종료 925건과
기간 종료 1건이고 경남은 명시 종료 1,419건이다. 강원 failed 322건은 checkpoint
발견 위치와 재현된 공통 오류를 근거로 `detail_click_or_post_contract`에 분류했다.
개별 현재 상세 상태 검증 수는 0으로 별도 명시해 원인 분류와 현행 상태 확인을
혼동하지 않는다.

Source별 outcome 전후와 현재 6개 field 관찰 상태는 다음과 같다. `V`는
`value_extracted`, `E`는 `label_present_value_empty`, `N`은 `label_not_found`,
`L`은 legacy `null_unverifiable`이다.

| Source | RYP7 review/closed/failed | 현재 review/closed/failed | V | E | N | L |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 부산 | 107/0/0 | 107/0/0 | 426 | 2 | 214 | 0 |
| 충북 | 441/0/0 | 441/0/0 | 114 | 3 | 1,761 | 768 |
| 대구 | 197/0/0 | 197/0/0 | 592 | 0 | 22 | 568 |
| 대전 | 12/0/0 | 12/0/0 | 0 | 0 | 0 | 72 |
| 강원 | 12/0/325 | 14/1/322 | 15 | 0 | 3 | 66 |
| 광주 | 31/0/0 | 31/0/0 | 95 | 0 | 1 | 90 |
| 경북 | 58/0/0 | 58/0/0 | 312 | 0 | 0 | 36 |
| 경남 | 28/1,419/0 | 28/1,419/0 | 0 | 0 | 0 | 168 |
| 인천 | 28/0/0 | 28/0/0 | 96 | 0 | 1 | 71 |
| 제주 | 207/924/2 | 207/926/0 | 3 | 0 | 0 | 1,239 |
| 전북 | 89/0/0 | 89/0/0 | 271 | 0 | 2 | 261 |
| 서울 | 97/13/0 | 97/13/0 | 393 | 0 | 0 | 189 |
| 울산 | 596/1/0 | 596/1/0 | 8 | 0 | 5 | 3,563 |
| 합계 | 1,903/2,357/327 | 1,905/2,360/322 | 2,325 | 5 | 2,009 | 7,091 |

11,430 slot은 네 상태로 모두 reconcile됐지만 legacy 7,091개가 남았다. 계획의
“합리적인 수준”에는 수치 기준이 없으므로 감사기가 임의 threshold를 만들지 않고
`legacy_null_within_target=null`, `data_ready=false`로 판정했다. 따라서 종료 이력
대조와 실패 분류는 완료됐으나 RYP8은 열린 상태다. 이 Slice의 시작 기준선
`accepted 18`, `duplicate 1`, `review 1,905`, `closed 2,360`, `failed 322`와 DB
projection은 유지한다. Schema·Fixture 의미·Seed·null enum·Backend·Frontend
계약은 변경하지 않았다.

감사 명령:

```powershell
$expectedOutcomes = '{\"accepted\":18,\"duplicate\":1,\"review\":1905,\"closed\":2360,\"failed\":322}'
& .\.venv\Scripts\python.exe scripts\audit_regional_ryp8.py `
  --expected-outcomes $expectedOutcomes
```

검증 결과:

- Gangwon canary Node syntax·fixture: `15 passed`
- RYP8 audit·regional replay 집중 Python: `61 passed, 12 subtests passed`
- `TEST_DATABASE_URL`을 전용 `cheongnyeon_alimi_test`로 지정한 전체 Python·
  PostgreSQL: `397 passed, 96 subtests passed` (기존 deprecation warning 1건)
- RYP8 감사: field slot `11,430/11,430` reconcile, closed history
  `2,345/2,345`, failed 분류 `322/322`, 고정 outcome 일치, legacy blocker 1개
- `python scripts/validate_docs.py`, `git diff --check`: 통과

### RYP8 충북 page 제한 재캡처 중단 (`2026-08-13`)

- 공식 목록 `441건·45 page`의 identity 441개를 최소 2초 간격으로 전건 읽기
  대조했다. 현재 목록과 checkpoint의 identity 순서 SHA-256이
  `6ace75667a11c8fc51ef494dd1c7feca7f659d3133116055883441338deadf90`로
  같고 중복은 0건이었다.
- 최신·중기·과거 상세는 모두 `.p-table__content`를 사용했다. 텍스트 원문에는
  `모집기간`, `접수기간`, `제출기한`이 있었고 이미지·첨부 중심 게시물에는
  신청기간 텍스트 라벨이 실제로 없었다. 한글 순번 `사.` 뒤의 `제출기한`을
  신청 마감으로 추출하되 `훈련기간`은 신청기간으로 오인하지 않는 fixture를
  추가했다.
- 신청기간 필드에서 추출된 단일 날짜는 마감일로 판정하도록 공통 Gate를
  보강했다. `2026.07.28.(화)`는 as-of `2026-08-13`에
  `application_period_ended`이며, Schema·enum·Seed는 변경하지 않았다. 공통
  Gate 변경이므로 전체 replay에서 다른 Source outcome 변화가 없는지 확인했다.
- page 1은 대표 3건, page 2~31은 각 10건, page 32는 navigation timeout 전후
  6건·4건으로 나눠 저장했다. page 32 첫 timeout은 실제 상세 DOM이 정상
  로드돼 남은 4건 한 번의 제한 재시도로 복구됐다.
- page 33의 두 번째 identity `149186`에서 navigation timeout이 반복됐다.
  같은 오류가 재발했으므로 지정 중단 조건에 따라 page 33~45와 다음 순서인
  울산 작업을 시작하지 않았다. page 33의 첫 묶음도 저장 전에 실패해 완료
  관찰 범위는 page 1 대표 3건과 page 2~32 전건을 합한 313 identity이며,
  page 1 잔여 7건과 page 33~45의 121건은 미재캡처 상태다.
- 충북 field slot은 `V 4/E 0/N 2/L 2,640 → V 114/E 3/N 1,761/L 768`, 전체
  legacy는 `8,963 → 7,091`이다. checkpoint outcome은 `accepted 18`,
  `duplicate 1`, `review 1,905`, `closed 2,360`, `failed 322`, drift 1로
  유지됐고 checkpoint digest도 변경되지 않았다. DB 동기화는 실행하지 않았다.

검증 결과:

- 충북 Browser fixture·runtime syntax: `16 passed`
- regional Gate·review audit·expansion·replay 집중 Python:
  `56 passed, 12 subtests passed`
- 전용 `cheongnyeon_alimi_test`를 포함한 전체 Python·PostgreSQL:
  `399 passed, 96 subtests passed` (기존 deprecation warning 1건)
- `python scripts/validate_docs.py`, `git diff --check`: 통과

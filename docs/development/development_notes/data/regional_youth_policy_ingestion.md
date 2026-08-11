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
| RYP4 | 대기 | 온통청년·복지로 중복 제외 |
| RYP5 | 대기 | 대표 Source actual |
| RYP6 | 대기 | 지역별 확대·전체 판정 |

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

## 주요 변경 파일

- `data/reference/regional_youth_policy_sources.json`
- `data/schema/regional_youth_policy_source_inventory.schema.json`
- `collectors/regional_sources.py`
- `collectors/regional_profile.py`
- `collectors/regional_discovery.py`
- `collectors/browser_runner.py`
- `collectors/gyeongbuk_youth.py`
- `collectors/regional_policy_gate.py`
- `collectors/http.py`
- `collectors/runtime.py`
- `collectors/__init__.py`
- `data/fixtures/regional/`
- `tests/test_regional_policy_gate.py`
- `tests/test_regional_discovery.py`
- `tests/test_browser_runner.py`
- `tests/test_gyeongbuk_youth.py`
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

## 남은 작업

- RYP4에서 온통청년·복지로 snapshot·PostgreSQL 기준 중복 제외
- RYP5 전에는 Browser Discovery와 이용 조건을 모두 통과한 Source만 actual 실행

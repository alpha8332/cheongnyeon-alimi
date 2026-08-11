# Data 05 Regional Youth Policy Ingestion Forest 개발 계획

## 계획 정보

- 번호: Data 05
- 담당 영역: Data
- 상태: in-progress
- 현재 진행: `RYP0` 완료, 다음 `RYP1` 홈페이지 탐색·Source 승인
- 계획일: `2026-08-11`
- 대상 Release: `v0.5.0`
- 선행 Forest: Data 01 Data Pipeline, Data 03 Recurrent Collection and Quality
  Operations, Data 04 Public HTTPS Policy Ingestion
- 참조 기반: Data 02 Release Dataset Bootstrap, Integration 03 Policy Search Data
  Foundation, Integration 08 Eligibility Evidence and Summary
- 후속 통합: 실제 정책 적재 뒤 기존 Policy API·Browser 인수, 필요할 때 별도
  교차 Source 관계 계약
- 권장 브랜치: `feature/data/regional-youth-policy-ingestion`
  한 개. 지역·Slice별 브랜치는 만들지 않음
- 구현 시작점: `ee23bc80e642e3b4dccd1f803abf61d2a02fc0b8`
- 현재 Slice: `RYP1`

## 목적

광역자치단체 청년정책 포털의 홈 또는 정책 진입점에서 해당 지역이 직접
시행하는 실제 신청 가능 청년정책을 찾아 기존 Raw → Extract → Normalize →
Validate → PostgreSQL 흐름에 연결한다.

지역 포털이 재게시한 중앙정부 전국 정책과 현재 온통청년·복지로 정책은 새
Policy row로 적재하지 않는다. Source 근거 없는 조건·기간·대상을 만들지 않고,
공식 원문과 수집 시각으로 재검증할 수 있는 정책만 사용자 검색 데이터로
승격한다.

## 현재 기준선과 독립 Forest 사유

- 현재 Collector와 Runtime replay는 `youthcenter-api`,
  `bokjiro-central-welfare-api`, `cheonan-youthcenter-web`만 지원한다.
- Data 04는 승인 공식 웹 Source 한 곳의 제한 수집을 완료 기준으로 하며 둘
  이상의 웹 Source와 범용 사이트 탐색을 범위 밖으로 둔다.
- Data 03의 `duplicate`는 같은 `(source_id, external_id)`의 Source 내부·실행 간
  중복이다. 제목이 다르거나 Source가 다른 동일 정책을 자동 병합하지 않는다.
- 정책 테이블의 현재 identity도 `(source_id, external_id)`이므로 지역 Source와
  온통청년·복지로 사이의 의미 중복은 별도 판정 Gate가 필요하다.
- 지역 포털 홈 탐색, 지역 고유성 판정과 교차 Source 제외는 독립 목표와 완료
  기준이 있으므로 Data 04 완료로 소급하거나 DTL4-5 소비 계약 대조에 섞지
  않는다.

## 선행 조건

- RYP-G0에서 17개 지역 inventory와 Forest 완료 기준을 승인한다.
- Data 04의 공통 HTTP·HTML Raw·Source Adapter·actual 적재 기준선이 구현
  브랜치에서 재사용 가능한 상태인지 확인한다.
- Data 03의 CollectionRun·동일·수정·실패 격리와 PostgreSQL Importer 기준선을
  실제 테스트로 재확인한다.
- 비교에 사용할 온통청년·복지로 snapshot ID, 수집 시각과 PostgreSQL 기준
  row를 고정한다.
- Source마다 robots·이용약관·라이선스·저장·변환·재배포 허용 범위를 승인하기
  전에는 Adapter 구현과 actual 대량 수집을 시작하지 않는다.
- API·Schema·Migration·TypeScript 변경 필요가 발견되면 Data 단독으로
  확정하지 않고 Backend·Frontend 소비 영향을 공동 검토한다.

## 초기 Source 후보 inventory

아래 URL은 `2026-08-11` 작업 입력으로 제공된 17개 탐색 시작점이다. 공식 운영 주체,
현재 접근 가능 여부, robots, 이용약관, 정책 목록·상세 endpoint와 재배포 허용
범위를 아직 승인한 값으로 취급하지 않는다.

| 광역자치단체 | 탐색 시작 URL | 초기 상태 |
| --- | --- | --- |
| 서울 | `https://youth.seoul.go.kr/mainA.do` | candidate-unverified |
| 부산 | `https://young.busan.go.kr/index.nm` | candidate-unverified |
| 대구 | `https://www.dgjump.com/` | candidate-unverified |
| 인천 | `https://youth.incheon.go.kr/` | candidate-unverified |
| 광주 | `https://gjyouthcenter.kr/main/` | candidate-unverified·canonical 지역 검토 필요 |
| 대전 | `https://www.daejeonyouthportal.kr/index.do` | candidate-unverified |
| 울산 | `https://www.ulsan.go.kr/s/ulsanyouth/main.ulsan` | candidate-unverified |
| 세종 | `https://www.4242.or.kr/` | candidate-unverified |
| 경기 | `https://youth.gg.go.kr/gg/index.do` | candidate-unverified |
| 강원 | `https://job.gwd.go.kr/youth` | candidate-unverified |
| 충북 | `https://www.chungbuk.go.kr/young/index.do` | candidate-unverified |
| 충남 | `https://youth.chungnam.go.kr/web/main/customSupp/list` | 목록 후보·미승인 |
| 전북 | `https://www.jb2030.or.kr/` | candidate-unverified |
| 전남 | `https://www.jnyouthcenter.kr/index.php` | candidate-unverified·canonical 지역 검토 필요 |
| 경북 | `https://gbyouth.go.kr/main.tc` | candidate-unverified |
| 경남 | `https://youth.gyeongnam.go.kr/youth/index.es?sid=a1` | candidate-unverified |
| 제주 | `https://jejuyouth.com/m/index.php` | candidate-unverified |

실행 기준 inventory는
`data/reference/regional_youth_policy_sources.json`이며
`data/schema/regional_youth_policy_source_inventory.schema.json`으로 검증한다.
XLSX의 17개 관할 라벨은 Source 탐색 범위로 보존하지만 현재
`kr-bjd-20260803` 기준정보는 광주·전남을 퇴역 code로 관리한다. 두 후보는
활성 통합 code로 자동 치환하지 않고 RYP1에서 현행 운영 주체와 관할 근거를
확인할 때까지 `historical_review_required`로 둔다. 후보 사이트의 데이터가
테스트·데모이거나 이용 조건상 수집할 수 없으면 다른 공식 Source를 검토하고,
우회 수집하지 않는다.

## 용어와 승인 의미

### 지역 고유 정책

다음 근거를 모두 만족하는 정책이다.

1. 해당 지방자치단체 또는 지역 공공기관이 직접 시행·접수·예산 집행 중 하나
   이상을 담당한다.
2. 지원 대상이나 신청 자격이 해당 시·도 또는 소속 시·군·구로 명시된다.
3. 공식 상세·공고·신청 페이지에서 정책명, 시행기관, 지원 내용과 지역 근거를
   확인할 수 있다.

지역 포털에 게시됐다는 사실, 제목의 지역명 또는 포털 분류만으로 지역 고유
정책을 확정하지 않는다. 중앙정책에 지역이 별도 예산·혜택·조건을 추가했다면
그 차이와 지역 공고 identity가 확인될 때만 별도 지역 정책으로 승인한다.

### 신청 가능 정책

수집 시점에 다음 중 하나를 공식 원문으로 확인할 수 있는 정책이다.

- 명시된 신청 기간 안에 있음
- `상시`, `예산 소진 시`처럼 현재 신청 경계가 명시됨
- 다음 모집 일정이나 현재 접수 상태를 공식 신청 채널에서 확인할 수 있음

마감 공고는 변경 감지와 과거 이력 근거로 Raw에 보존할 수 있지만 현재 사용자
정책으로 신규 승격하지 않는다. 기간을 확인할 수 없으면 `open`으로 추정하지
않고 검토 대상으로 격리한다.

### 교차 Source 중복

새 지역 후보가 현재 승인된 온통청년 또는 복지로 정책과 실질적으로 같은
사업인 경우다. 이 Forest에서 “중복 제외”는 기존 API 정책을 삭제하거나 지역
원문으로 자동 덮어쓰는 것이 아니라, 지역 후보의 새 Policy row 생성을 막는
것을 뜻한다.

## 범위

- 17개 광역자치단체 공식 청년정책 Source 후보 inventory와 상태 관리
- 홈·사이트맵·정책 메뉴에서 목록·상세·공개 API endpoint를 찾는 제한 탐색
- 공식 운영 주체·robots·이용약관·라이선스·재배포 조건 preflight
- 승인된 목록·상세 경로와 pagination의 Source별 allowlist
- 공개 API → 서버 HTML → 공개 JSON/XHR 순서의 수집 방식 선택
- 공통 HTTP·Raw·snapshot·실행 기록과 Source별 Adapter 재사용
- 지역 고유성, 현재 신청 가능성, 공식 신청·문의 채널 판정
- 온통청년·복지로 승인 snapshot 및 PostgreSQL 기준의 교차 Source 중복 제외
- 실제 Raw, content hash, Source URL, 수집 시각과 필드 provenance 보존
- 같은 Source 재실행의 inserted·updated·unchanged·duplicate·failed 판정
- 교차 Source 제외·검토 필요 건수와 비밀 없는 판정 근거 보고
- 승인 Source의 제한 actual 수집과 PostgreSQL → Policy API → Browser 대조

## 범위 밖

- 인터넷 전체 또는 임의 도메인을 재귀 탐색하는 범용 크롤러
- 로그인·CAPTCHA·접근 통제·robots·이용약관 우회
- 검색엔진 구축, 전체 사이트 미러링과 첨부파일 일괄 다운로드
- 지역 포털에 재게시됐다는 이유만으로 전국 정책을 지역 정책으로 복제
- 제목만 같은 정책의 자동 병합·삭제
- Source 근거가 없는 신청기간·자격·지원내용·연락처 생성
- LLM이 원문에 없는 정책 요약이나 누락값을 작성하는 처리
- 개인 전화번호·개인 이메일·성명 등 개인정보 구조화
- 교차 Source 상세 근거를 기존 API 정책에 자동 합성·덮어쓰기
- Scheduler·분산 queue·worker 플랫폼과 Production 배포 구성
- 관리자 UI의 정책별 교차 Source 관계 노출

## 공통 설계 원칙

### 홈 탐색과 운영 수집 분리

홈 URL은 정책 데이터 endpoint가 아니라 Source 발견의 시작점으로만 사용한다.
RYP1 탐색은 같은 공식 도메인의 메뉴·사이트맵·공개 요청을 최소 범위로 확인해
목록·상세 경로를 찾는다. 운영 Collector는 탐색 결과로 승인된 경로만 호출하고
홈에서 매 실행마다 링크를 무제한 재귀 순회하지 않는다.

### 수집 방식 우선순위

1. 공식 Open API 또는 공공데이터
2. 서버에서 렌더링된 정책 목록·상세 HTML
3. 사이트가 로그인 없이 공개적으로 사용하는 JSON/XHR
4. 앞선 방식이 없고 이용 조건이 허용할 때만 제한 Browser rendering 검토

Browser로 endpoint를 발견했더라도 운영 호출은 가능한 한 결정적인 HTTP
요청으로 고정한다. Browser 자동화가 필수이면 일반 Adapter에 섞지 않고 별도
승인·실패·실행 비용을 기록한다.

### 공통 엔진과 Source별 Adapter

- 공통 계층: HTTP, timeout·retry·rate limit, Raw 저장, snapshot, 실행 기록,
  정규화·검증과 PostgreSQL 전달
- Source별 계층: 목록·상세 URL, pagination, selector 또는 source field,
  external identity, 지역·기간·기관 evidence mapping
- Normalizer는 CSS selector, 사이트 메뉴명과 Source별 key를 알지 않는다.
- DOM·JSON 구조 변경은 정상 빈 값이 아니라 selector/schema drift로 격리한다.

### 거짓 데이터 방지

- 원문에 없는 값을 채우지 않고 `null`, 빈 배열 또는 review 상태로 유지한다.
- 공식 상세 URL과 원문 evidence가 없는 제목 목록은 사용자 정책으로 승격하지
  않는다.
- 테스트 문구, 비현실적 수치·날짜, 외부 데모 링크와 운영기관 불일치는
  `rejected_source_data`로 격리한다.
- 공개 시설 대표전화와 공식 문의 채널만 보존하고 개인 연락처는 수집하지 않는다.

## 지역 고유성 Gate

정규화 전 Source Adapter가 다음 evidence를 제공한다.

- `implementing_organization_text`
- `region_eligibility_text`
- `application_channel_text`와 공식 URL
- 지역 예산·추가 혜택·접수기관 근거가 있으면 해당 원문
- 각 값의 Source URL과 locator

판정은 다음 세 상태를 사용한다.

| 상태 | 의미 | 처리 |
| --- | --- | --- |
| `regional_confirmed` | 시행 주체와 지원 지역이 공식 원문으로 확인됨 | 중복 Gate로 전달 |
| `regional_review_required` | 지역 포털 게시 외에 시행·대상 근거가 부족하거나 모호함 | Policy 미적재, 검토 격리 |
| `non_regional` | 전국 정책 재게시 또는 타 지역 정책임이 확인됨 | Policy 미적재, 제외 집계 |

`coverage_scope=regional`과 canonical `include` region rule은
`regional_confirmed`의 Source evidence에서만 생성한다. 지역 근거가 없으면
포털의 소재지를 근거로 region을 추정하지 않는다.

## 온통청년·복지로 중복 제외 Gate

### 비교 기준선

- 비교 대상은 수동 Excel 제목 목록이 아니라 수집 시점의 승인 온통청년·복지로
  snapshot과 PostgreSQL row다.
- 제공된 중앙·전국 정책 목록은 회귀·오류·알려진 중복 사례를 만드는 참고
  자료로만 사용하고 DB에 직접 import하지 않는다.
- 비교 기준선의 snapshot ID, 수집 시각과 정책 건수를 실행 결과에 기록한다.

### 판정 순서

1. 지역 상세에 온통청년 `plcyNo` 또는 복지로 `servId`가 있으면 확정 중복
2. 공식 application/canonical URL과 운영 사업 identity가 같으면 확정 중복
3. 같은 공식 공고·사업 ID를 참조하면 확정 중복
4. 정규화 제목·시행기관·지역·신청기간·지원내용 fingerprint가 모두 일치하면
   중복 후보
5. 제목만 같거나 기간·기관이 불명확하면 자동 제외하지 않고 검토 필요

### 판정 결과

| 결과 | Policy 적재 | 보존 |
| --- | --- | --- |
| `accepted_regional` | 기존 Importer로 전달 | Raw·Normalized·provenance |
| `excluded_aggregator_duplicate` | 전달하지 않음 | Raw·비밀 없는 일치 근거·기준선 identity |
| `duplicate_review_required` | 전달하지 않음 | Raw·후보 identity·불확실 사유 |

초기 구현은 Policy/API Schema를 바꾸지 않는다. 확정 중복과 검토 필요 건은
`CollectionRun.skipped_count`에 포함하고 정책별 판정은 Git 비추적 Runtime
decision manifest에 보존한다. Data 03의 Source identity `duplicate_count`와
교차 Source 제외를 같은 의미로 집계하지 않는다.

지역 원문의 상세 조건으로 기존 온통청년·복지로 정책을 보강하려면 다중 Source
provenance와 canonical policy 관계를 Data·Backend·Frontend가 공동 승인해야
한다. 해당 계약 전에는 자동 합성하거나 기존 row를 덮어쓰지 않는다.

## Slice 계획

### RYP0 - Inventory 완성·v0.5.0 Gate

#### 목적

17개 광역자치단체 후보와 Forest 실행 범위를 고정한다.

#### 작업

- 제공 XLSX의 광주·전남 분리 행과 17개 HTTPS 탐색 시작점을 repository
  inventory로 변환
- 17개 후보의 운영 주체, 공식 도메인과 HTTPS 확인 경계를 Schema로 고정
- `candidate`, `approved`, `blocked`, `rejected` 상태와 근거 형식 확정
- Data 05를 `v0.5.0` 필수 범위와 DTL4-6~DTL4-8 Gate에 연결
- 실제 구현 시작 SHA와 Forest 브랜치 한 개 확정
- 사용자 제공 XLSX의 파일명·시트·범위·SHA-256을 입력 근거로 보존하되 실행
  기준은 diff와 검증이 가능한 repository JSON과 JSON Schema로 고정
- 현행 행정구역 기준과 광주·전남 17개 관할 라벨의 차이를 review 상태로 보존

#### 완료 기준

- 17개 지역 inventory에 빈 지역이 없음
- 모든 후보가 `candidate`로 시작하고 승인 목록·상세·요청 예산을 선행 주장하지 않음
- 광주·전남의 퇴역 code를 활성 통합 code로 자동 치환하지 않음
- 완료 기준과 구현 순서가 Team Leader 승인을 받음
- Forest·Release·4주차·Integration 07 로드맵이 `v0.5.0` 필수 범위로 일치함

### RYP1 - 홈페이지 탐색·Source 승인

#### 목적

홈 URL에서 실제 정책 목록·상세 endpoint를 찾고 수집 가능 Source만 승인한다.

#### 작업

- 메뉴·사이트맵·검색·공개 네트워크 요청을 제한 조사
- 목록·상세·pagination·external identity·rate limit 후보 기록
- robots·약관·라이선스·저장·변환·재배포 허용 범위 확인
- API·HTML·JSON/XHR·Browser 필요 유형 분류
- 승인 상태·Source ID·allowlist·요청 예산·지역 mapping의 교차 필드 조합을
  검사하는 domain validator 추가
- 접근 금지·로그인 전용·데모 Source를 `blocked` 또는 `rejected`로 판정

#### 완료 기준

- 각 지역에 승인 Source 또는 비승인 사유가 있음
- 승인 Source는 목록·상세 allowlist와 요청 예산을 가짐
- 공통 `JsonSchemaValidator`가 지원하지 않는 조건부 교차 필드 조합도 domain
  validator에서 거부됨
- 허용 여부가 불명확한 Source를 구현 대상으로 승인하지 않음

### RYP2 - 공통 실행 경계와 Source Adapter

#### 목적

승인 Source를 기존 파이프라인에 안전하게 연결할 재사용 경계를 만든다.

#### 작업

- Source profile과 목록·상세 Adapter interface 확정
- pagination, timeout·retry·429·rate limit 공통 동작 재사용
- 안정적인 `(source_id, external_id)` 생성과 canonical URL 검증
- 목록·상세·누락·drift·실패 축소 fixture
- 원문 byte, hash, collected_at과 locator provenance 보존

#### 완료 기준

- Source별 selector·field가 공통 Normalizer에 누출되지 않음
- 같은 Raw replay가 외부 요청 없이 같은 추출 결과를 만듦
- 실제 운영 HTML·개인정보·재배포 제한 자료가 Git에 포함되지 않음

### RYP3 - 지역 고유성·신청 가능성 판정

#### 목적

지역 포털에 섞인 전국·타 지역·마감 정책을 사용자 데이터에서 제외한다.

#### 작업

- 시행기관·대상 지역·지역 접수·추가 혜택 evidence mapping
- `regional_confirmed`, `regional_review_required`, `non_regional` 판정
- 신청기간·상시·예산 소진·마감의 Source 전용 mapping
- 지역 evidence가 없는 정책을 포털 소재지로 추정하지 않는 회귀 테스트

#### 완료 기준

- 승인 fixture에서 지역 고유·전국 재게시·모호 사례가 결정적으로 분리됨
- 신청 가능성을 확인하지 못한 정책이 `open`으로 승격되지 않음
- accepted 정책은 canonical 지역 rule과 provenance를 가짐

### RYP4 - 온통청년·복지로 교차 Source 제외

#### 목적

기존 API 정책과 같은 지역 후보의 중복 row 생성을 막는다.

#### 작업

- 승인 snapshot·PostgreSQL 비교 기준선 로더
- ID·canonical URL·공고 ID exact 판정
- 제목·기관·지역·기간·지원내용 fingerprint 후보 판정
- 확정 중복, 검토 필요와 신규 지역 정책 fixture
- Runtime decision manifest와 CollectionRun 집계 연결

#### 완료 기준

- 확정 중복은 Policy row를 만들지 않음
- 제목만 같은 다른 사업은 자동 제외하지 않음
- 불확실한 후보는 사용자 검색에 노출되지 않고 검토 근거를 보존함
- 기존 온통청년·복지로 row를 수정·삭제하지 않음

### RYP5 - 대표 Source actual 파일럿

#### 목적

서로 다른 구조의 대표 Source에서 실제 지역 정책을 끝까지 검증한다.

#### 작업

- RYP1 결과에서 HTML, 공개 API/JSON, 게시판형을 대표하는 최대 3개 Source 선정
- Source마다 목록 1페이지와 상세 3~5건부터 제한 actual 실행
- 지역 고유성·중복 제외·정규화·품질 결과 수동 원문 대조
- accepted 정책의 PostgreSQL 적재와 Policy API·Browser 확인
- 같은 snapshot 재실행과 변경·drift·HTTP 실패 검증

#### 완료 기준

- 최소 3개 승인 Source 또는 승인 가능한 모든 대표 유형의 actual 결과가 있음
- 거짓·전국·중복 정책이 사용자 검색 결과에 포함되지 않음
- accepted 표본은 원문 → Raw → DB → API → Browser lineage가 일치함
- actual 실행 수치와 실패·제외·검토 필요 건수를 개발 기록에 남김

### RYP6 - 지역별 순차 확대와 Forest 판정

#### 목적

파일럿 경계를 유지하며 승인 가능한 지역을 한 곳씩 확장한다.

#### 작업

- Source별 fixture·Adapter·actual 검증을 Conventional Commit 단위로 추가
- 각 지역의 최신·신청 가능 정책 수와 제외·실패·drift 통계 기록
- blocked Source의 재개 조건과 대체 공식 Source 기록
- 전체 회귀, 문서·계약과 Git 비추적 경계 대조

#### 완료 기준

- 17개 지역이 `implemented`, `blocked`, `rejected` 중 하나의 근거 있는 최종
  상태를 가짐
- 모든 `implemented` Source가 제한 actual 수집·재실행·DB 인수를 통과함
- `blocked`·`rejected` Source를 우회하거나 성공으로 기록하지 않음
- 기존 온통청년·복지로와 Release 1 golden 검색 회귀가 통과함

## Gate와 실행 순서

| Gate | 승인 내용 | 다음 단계 |
| --- | --- | --- |
| `RYP-G0` | 17개 inventory, 범위·완료 기준과 DTL Gate | RYP1 |
| `RYP-G1` | Source별 이용 조건·endpoint·요청 예산 | RYP2 |
| `RYP-G2` | Adapter·지역 판정·중복 제외 fixture | RYP5 |
| `RYP-G3` | 대표 Source actual DB·API·Browser 인수 | RYP6 |
| `RYP-G4` | 지역별 최종 상태·전체 회귀·문서 대조 | Forest 완료 판정 |

```text
RYP0 inventory·v0.5.0 Gate
  → RYP1 홈페이지 탐색·Source 승인
  → RYP2 Adapter 실행 경계
  → RYP3 지역 고유성·신청 가능성
  → RYP4 온통청년·복지로 중복 제외
  → RYP5 대표 actual DB·API·Browser
  → RYP6 지역별 순차 확대·전체 판정
```

RYP2의 Source별 fixture 작업은 승인 Source끼리 병렬화할 수 있다. RYP5 actual은
RYP3·RYP4 판정 Gate가 통과한 Source만 실행한다. 지역별 구현을 위해 새
브랜치를 만들지 않고 한 Forest 브랜치에서 Source별 Conventional Commit으로
검토 지점을 나눈다.

## 역할 분담

| 역할 | 책임 |
| --- | --- |
| Data | Source preflight, Adapter·Extractor, Raw·provenance, 지역 판정, 교차 Source 제외, 정규화·품질·actual 적재 |
| Backend | 초기에는 기존 Importer·Policy API 회귀 확인. 새 DB 관계나 관리자 상세 노출이 필요할 때만 공동 계약 뒤 구현 |
| Frontend | 초기에는 기존 목록·상세·검색의 실제 지역 정책 표시 회귀 확인. 새 중복 상태 UI는 별도 승인 전 구현하지 않음 |
| Team Leader | `v0.5.0` 범위·Source 이용 조건 승인, actual 원문 → DB → API → Browser 대조와 Gate 판정 |

초기 Data-only Slice는 기존 공개 API Schema를 바꾸지 않는다. Schema, Migration,
API 또는 TypeScript 변경 필요가 실제로 발견되면 해당 Slice 범위를 확장하지
않고 영향과 선택지를 공동 검토한다.

## 검증 계획

### 단위·계약 검증

- Source별 목록·상세·pagination과 stable external identity
- 선택 필드 누락, selector/schema drift와 잘못된 canonical URL
- 지역 고유·전국 재게시·타 지역·모호 지역 fixture
- open·scheduled·closed·상시·예산 소진·기간 미상 fixture
- 온통청년·복지로 ID·URL exact 중복, fingerprint 후보와 동명 다른 정책
- 거짓 수치·테스트 문구·데모 링크와 기관 불일치 격리
- Raw hash·provenance·NormalizedProgram·EligibilitySummary Schema

### PostgreSQL 통합 검증

- 최초 적재, 동일 재실행 unchanged, 수정 updated와 Source identity duplicate
- 교차 Source 제외가 새 Policy row를 만들지 않는지 확인
- 제외·검토 필요 후보가 정상 정책 transaction과 조회에서 격리되는지 확인
- accepted 지역 정책의 region relation·search projection·상세 evidence 확인
- 기존 온통청년·복지로 row 수와 identity가 변경되지 않는지 확인

### actual 인수

- 승인 Source별 제한 목록·상세 호출과 요청 예산 준수
- 공식 원문과 지역 고유성·신청 가능성·중복 판정 수동 표본 대조
- Runtime Raw → PostgreSQL → Policy API → Browser lineage
- Release 1 snapshot 3,156건과 golden 검색 회귀
- 실패·blocked Source를 fixture 성공으로 대체하지 않음

### 공통 문서 검증

```powershell
python scripts/validate_docs.py
git diff --check
```

구현 시 Source별 테스트 파일과 실제 명령은 RYP2에서 저장소 구조에 맞게
고정한다. 아직 존재하지 않는 테스트 명령을 실행 성공으로 기록하지 않는다.

## Forest 완료 기준

- 17개 광역자치단체마다 공식 Source의 최종 상태와 근거가 있음
- 승인 Source는 허용된 목록·상세 endpoint와 요청 예산을 가짐
- 최소 3개 대표 Source의 실제 지역 정책이 기존 파이프라인과 PostgreSQL에
  연결됨
- 전국 재게시·마감·거짓·온통청년·복지로 중복이 새 사용자 Policy row를 만들지
  않음
- 제목만 같은 다른 정책과 불확실 후보를 자동 삭제하지 않음
- accepted 정책의 지역·기간·기관·신청 채널과 provenance가 원문과 일치함
- 동일·수정·중복·drift·HTTP 실패가 정상 정책과 격리됨
- 기존 Release 1 검색과 온통청년·복지로 데이터가 회귀하지 않음
- 실제 Raw·운영 HTML·개인정보·비밀키·Runtime decision manifest가 Git에 없음
- 단위·PostgreSQL 통합·actual API·Browser·문서 검증 결과가 개발 기록에 있음

Forest 완료는 17개 사이트를 모두 억지로 크롤링했다는 의미가 아니다. 이용
조건·접근 경계·데이터 품질 때문에 수집할 수 없는 Source는 근거와 재개 조건을
가진 `blocked` 또는 `rejected` 상태로 남긴다.

## v0.5.0과 DTL Gate 연결

Data 05는 `v0.5.0` 필수 범위다. DTL4-4와 Integration 08의 승인 Schema·DB·API·
UI 기준선을 재사용하므로 DTL4-5 계약 소비 대조를 기다리지 않고 RYP0~RYP1
inventory·Source preflight를 병렬 수행할 수 있다.

- DTL4-5 / W4-G1: Data 05는 기존 Schema를 바꾸지 않는다는 소비 경계를 대조
- DTL4-6 / W4-G2: RYP0~RYP4 inventory·Adapter·지역 판정·중복 제외 테스트 준비
- DTL4-7 / W4-G3: RYP5 대표 Source actual DB → API → Browser 인수
- DTL4-8 / W4-G4: RYP6 지역별 최종 상태·전체 회귀·문서 대조

따라서 DTL4-8을 끝낸 뒤 Data 05를 시작하지 않는다. Data 05가 위 Gate를
통과하지 못하면 `v0.5.0` 기본 기능이 미완료이므로 W4-G4를 통과시키지 않는다.

## 위험과 미확정 사항

- 17개 Source 관할 라벨과 현행 `kr-bjd-20260803`의 15개 활성 광역 단위가
  다르다. 특히 광주·전남의 공식 원문 관할을 확인하기 전에는 통합 code나
  퇴역 code를 정책 region rule로 확정할 수 없다.
- 홈페이지에서 발견한 정책 메뉴가 공식 원문이 아니라 다른 포털 재게시일 수 있다.
- 사이트별 HTML·JSON·pagination·인코딩과 동적 렌더링 방식이 서로 다르다.
- robots가 허용해도 이용약관이 저장·변환·재배포를 제한할 수 있다.
- 온통청년·복지로와 같은 사업이어도 제목·기관명이 달라 false negative가 생길
  수 있다.
- 제목 중심 자동 제외는 지역 추가 혜택을 가진 별도 사업을 잃게 할 수 있다.
- 기존 Policy는 단일 `source_id` identity이므로 교차 Source evidence 합성은
  별도 공통 계약 없이는 표현할 수 없다.
- 신청기간과 접수 상태가 목록·상세·첨부 공고에서 충돌할 수 있다.
- PDF·HWP에만 핵심 조건이 있으면 첨부 수집·파싱 범위를 별도로 승인해야 한다.
- Source 수가 늘면 요청 예산·실행 시간·drift 유지 비용이 증가한다.

## 관련 문서

- [Data Pipeline](01_data_pipeline.md)
- [Release Dataset Bootstrap](02_release_dataset_bootstrap.md)
- [Recurrent Collection and Quality Operations](03_recurrent_collection_quality_operations.md)
- [Public HTTPS Policy Ingestion](04_public_https_policy_ingestion.md)
- [Supplemental Official Policy Ingestion](06_supplemental_official_policy_ingestion.md)
- [Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md)
- [Eligibility Evidence and Summary](../integration/08_eligibility_evidence_summary.md)
- [전체 Forest 로드맵](../forest_roadmap.md)
- [Release와 Milestone 계획](../release_roadmap.md)
- [데이터 소스](../../../data/data_sources.md)
- [Source Profile](../../../data/source_profiles.md)
- [수집 정책](../../../data/collection_policy.md)
- [데이터 정규화 규칙](../../../data/normalization_rules.md)
- [Collector 실행](../../../operations/collector.md)

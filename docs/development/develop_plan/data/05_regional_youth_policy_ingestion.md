# Data 05 Regional Youth Policy Ingestion Forest 개발 계획

## 계획 정보

- 번호: Data 05
- 담당 영역: Data
- 상태: in-progress
- 현재 진행: `RYP0`~`RYP5` 완료, `RYP6` 구현 준비
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
- 현재 Slice: `RYP5` 대표 Source actual 파일럿 완료

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

### RYP1 Browser Discovery 최종 판정 (`2026-08-11`)

- 승인 13개: 서울, 부산, 대구, 인천, 광주(현행 통합 플랫폼), 대전, 울산,
  강원, 충북, 전북, 경북, 경남, 제주
- 차단 3개: 세종, 경기, 충남
- 제외 1개: 전남 구 포털
- Browser·공개 HTTP 재검증으로 17개 모두 상세 identity 도달

원시 HTTP 중심 잠정 판정 9개 승인·7개 차단·1개 제외를 Browser 기준으로
재검증했다. 서울은 `맞춤서비스` → 서울시 정책 90건·자치구 정책 21건 →
`plcyBizId=V202600006` 상세까지 진입했고, 강원·충북·제주도 Browser 상세
식별자를 재현해 `browser` collection mode로 승인했다. 서버 HTML을 안정적으로
재현한 나머지 8개는 `http_html` mode로 승인했다.

세종·경기·충남은 Browser 상세에는 도달했지만 해당 정책 경로가 robots 허용
범위에 없어 운영 collection을 승인하지 않았다. 경북은 사용자 제공 정책 목록을
재검증해 `POST /policy/list.json`의 실제 정책 JSON과
`POST /policy/detail.modal`의 상세 HTML을 확인했다. robots의
`/policy/list.tc/` 패턴은 실제 `/policy/list.tc`와 JSON·modal 경로에 일치하지
않으므로 `http_json` mode로 승인한다. Browser DOM instrumentation 충돌은
HTTP JSON 실행 경계의 차단 사유로 사용하지 않는다. 전남 구 포털은 현행 통합
플랫폼과 중복되고 robots가 홈만 허용해 제외 상태를 유지한다.

광주 관할 라벨은 XLSX lineage로 보존하되 운영 Source는 기존 센터가 연결하는
`https://youth.jeonnam-gwangju.go.kr/www/`로 교체했다. 공식 화면이
전남광주통합특별시 청년통합플랫폼임을 확인했으므로 Source mapping은 활성
`1200000000`으로 승인했다. 실제 개별 정책의 대상 지역은 포털 관할만으로
추정하지 않고 RYP3에서 상세 원문 evidence로 판정한다. 전남 구 포털의 퇴역
`4600000000` mapping은 비승인 lineage로 유지한다.

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
- 로그인 없는 공개 화면에서 클릭·검색어 입력·select·tab·pagination·더보기와
  JavaScript event를 사용자처럼 실행하는 Browser Discovery
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

- 사용자 입력과 무관한 인터넷 전체·검색엔진 결과·외부 도메인을 무제한 재귀
  탐색하는 크롤러
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

### 지원하는 공개 웹사이트 계약

입력은 지방자치단체·지역 공공기관의 로그인 없는 공식 HTTPS 홈 URL이다. 별도
목록 URL이나 selector가 없어도 다음 상호작용으로 정책 상세에 도달할 수 있으면
수집 후보로 지원한다.

- 메뉴·전체메뉴·tab·accordion·modal 열기와 링크 클릭
- `청년`, `청년정책`, `지원사업` 등 검색어 입력과 검색 실행
- 지역·분야·모집상태 select, checkbox와 button 선택
- pagination·더보기·무한 스크롤의 제한 실행
- JavaScript `#none` 링크·POST form·XHR로 열리는 목록과 상세
- 같은 공식 운영 주체가 명시적으로 연결한 정책 하위 도메인 이동

로그인·본인인증·CAPTCHA·결제·개인정보 입력이 필요한 경로와 접근통제 우회는
지원하지 않는다. 사용자 제공 17개 사이트는 정책 열람에 로그인이 필요 없다는
사용자 확인을 출발 가정으로 두되, RYP1에서 각 사이트의 홈 → 상세 경로를 실제
Browser로 재현해야 승인한다.

### 홈 탐색과 운영 수집 분리

홈 URL은 Browser Discovery의 필수 시작점이다. 최초 등록과 구조 drift 복구 때는
Browser가 렌더링된 DOM의 메뉴·검색·선택 UI를 제한 탐색해 정책 목록·상세와
필드 구조를 찾고, 클릭 경로를 재현 가능한 Source profile로 만든다. 운영
Collector는 해당 profile을 재사용하며 매 실행마다 홈을 무제한 순회하지 않는다.

profile 재생이 실패하면 정상 빈 결과로 처리하지 않고 `discovery_drift`로
격리한 뒤 같은 홈에서 제한 재탐색한다. 새 경로는 상세 표본과 이용 조건을 다시
확인한 후에만 운영 profile로 승격한다.

### 발견 방식과 실행 방식 분리

최초 발견 방식은 Browser를 기본으로 한다. Browser가 사용자처럼 홈에서 정책
목록과 상세까지 이동하면서 DOM·form·network 요청을 함께 관찰한다. 발견 후
반복 실행 방식은 다음 순서로 선택한다.

1. 같은 공식 사이트가 제공하는 Open API 또는 공개 JSON
2. Browser에서 확인한 서버 HTML GET·POST
3. 로그인 없이 공개된 XHR
4. 클릭·JavaScript 렌더링이 필수인 Browser 실행 profile

Browser는 실패 시 최후 수단이 아니라 정식 discovery·collection mode다. 더
단순한 API·HTTP 경로가 재현되면 운영 비용과 결정성을 위해 이를 선택하지만,
원시 HTTP가 실패한다는 이유만으로 Browser에서 읽을 수 있는 Source를 차단하지
않는다. 선택 mode와 fallback 금지 조건, 실행 비용을 inventory에 기록한다.

### Browser Discovery 상태와 산출물

각 Source는 `home_loaded` → `policy_menu_found` → `list_found` →
`detail_found` → `extraction_ready` 상태를 순서대로 증명한다. 중간 실패는 마지막
성공 상태와 이유를 남기며 `HTTP blocked`를 Browser 실패와 같은 의미로 쓰지
않는다.

Source profile은 다음을 보존한다.

- 홈부터 목록·상세까지의 클릭·입력·선택 action과 대상 locator
- 목록 URL 또는 form/XHR, pagination 방식과 목록 정책 수 표본
- 상세 URL·POST identity 또는 JavaScript action과 stable external ID
- 제목·기관·지원내용·신청기간·대상·제외조건·필요서류·문의처의 label/locator
- same-origin·공식 하위 도메인 allowlist, 요청·상호작용 예산과 최소 간격
- 발견 시각, 최종 URL, DOM fingerprint와 상세 표본 대조 결과

상태 값은 다음 두 축으로 분리한다.

- discovery: `pending`, `home_loaded`, `policy_menu_found`, `list_found`,
  `detail_found`, `extraction_ready`, `discovery_review_required`, `blocked`
- collection mode: `api`, `http_html`, `http_json`, `browser`, `none`

RYP1 탐색 예산의 기본값은 Source당 동일 도메인 깊이 4, 상호작용 30회, 목록
2페이지, 상세 3건과 상호작용 시작 간격 최소 2초다. 이 값은 전체 정책 수집량이
아니라 안전하게 구조를 발견하기 위한 표본 예산이다. 후보 선택은 접근 가능한
이름·heading·메뉴 문맥의 청년·정책·지원·사업 동의어를 결정적으로 점수화하고,
동점·모호 후보는 임의 클릭하지 않고 `discovery_review_required`로 기록한다.

### Data Browser runtime 경계

현재 repository의 Playwright는 Frontend E2E 개발 의존성으로만 존재한다. RYP1
실사이트 탐색은 설치된 로컬 Playwright를 사용하되, Data 운영 코드가 Frontend
테스트 모듈을 import하는 구조는 승인하지 않는다. RYP2에서 Data 소유 Browser
runner와 Python 수집 파이프라인을 다음 JSON 경계로 분리한다.

- 입력: 홈 URL, 허용 host, interaction/request 예산, 기존 action profile
- 출력: action trace, 발견 목록·상세 identity, 렌더링 Raw metadata, locator와
  비밀 없는 실패 분류
- Browser runner는 DB에 직접 쓰거나 정책값을 추정하지 않음
- Python Runtime이 Raw 보존·정규화·검증·중복 제외·PostgreSQL 적재를 소유

Data 소유 runtime 위치와 Node dependency는 RYP2 구현 시작 전에 repository
구조와 lockfile 영향을 검토해 확정한다. 이 계획 보완만으로 새 패키지를
설치하거나 Frontend dependency 소유권을 변경하지 않는다.

### 공통 엔진과 Source별 Adapter

- 공통 계층: Browser navigator, interaction budget, HTTP, timeout·retry·rate
  limit, Raw 저장, snapshot, 실행 기록, 정규화·검증과 PostgreSQL 전달
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

17개 홈에서 사용자와 같은 Browser 상호작용으로 정책 목록·상세와 추출 가능한
필드를 찾고, discovery와 운영 collection 가능 여부를 분리해 승인한다.

#### 작업

- 17개 홈 모두에서 렌더링 후 메뉴·전체메뉴·검색·select·tab·pagination을
  interaction budget 안에서 실행
- `home_loaded`부터 `extraction_ready`까지 마지막 성공 discovery 상태 기록
- 목록·상세·pagination·external identity·form/XHR·rate limit 후보 기록
- 상세 최소 1건에서 정책명·기관·지원내용·기간·대상과 신청 경로를 원문 대조
- robots·약관·라이선스·저장·변환·재배포 허용 범위 확인
- discovery mode와 API·HTML·JSON/XHR·Browser collection mode 분리
- `discovery_status`, `collection_mode`, Source ID·allowlist·interaction/request
  예산·지역 mapping의 교차 필드 조합을 검사하는 inventory 계약 보완
- 접근 금지·로그인 전용·데모 Source를 `blocked` 또는 `rejected`로 판정

#### 완료 기준

- 각 지역에 홈 → 정책 메뉴 → 목록 → 상세의 재현 경로 또는 정확한 실패 단계가 있음
- Browser에서 상세를 읽을 수 있는 Source를 원시 HTTP 실패만으로 차단하지 않음
- 승인 Source는 discovery action profile, 목록·상세 allowlist, collection mode와
  interaction/request 예산을 가짐
- 공통 `JsonSchemaValidator`가 지원하지 않는 조건부 교차 필드 조합도 domain
  validator에서 거부됨
- 허용 여부가 불명확한 Source를 구현 대상으로 승인하지 않음

#### 완료 결과 (`2026-08-11`)

- [x] HTTP 중심 9개 승인·7개 차단·1개 제외 잠정 inventory와 validator 작성
- [x] 서울 Browser에서 홈 → 서울시 정책 90건·자치구 정책 21건 → 상세 1건과
  주요 필드까지 사용자 클릭 경로 재현
- [x] 17개 사이트 Browser Discovery 재검증
- [x] discovery 상태와 collection mode를 분리한 inventory `1.1.0`·validator 보완
- [x] 17개 모두의 action profile·상세 표본 또는 실패 단계 기록
- [x] Browser 결과를 반영한 RYP-G1 실행 경계 승인

최종 판정은 `approved` 13개·`blocked` 3개·`rejected` 1개다. 화면에서 상세를
읽을 수 있는지와 운영 수집이 robots·이용 경계를 만족하는지를 분리했으므로,
차단 Source의 discovery evidence는 보존하되 RYP2 실행 allowlist에는 포함하지
않는다.

### RYP2 - 공통 실행 경계와 Source Adapter

#### 목적

홈 URL만으로 정책 상세를 발견하고 이후 반복 실행할 Browser Discovery Engine과
Source profile 재생 경계를 기존 파이프라인에 연결한다.

#### 작업

- DOM 역할·텍스트·label 의미로 메뉴 후보를 찾는 `BrowserDiscoveryEngine`
- click·fill·select·tab·pagination·load-more의 제한 interaction interface
- 홈 → 상세 action profile 생성·재생과 drift 시 제한 재탐색
- table·definition list·heading/section label 기반 공통 정책 필드 후보 추출
- 공통 추출로 모호한 부분만 Source profile selector·mapping으로 보완
- Source profile과 목록·상세 Adapter interface 확정
- Data Browser runner JSON 입출력과 Python subprocess 오류·timeout·취소 경계
- pagination, timeout·retry·429·rate limit 공통 동작 재사용
- 안정적인 `(source_id, external_id)` 생성과 canonical URL 검증
- JS `#none`, GET·POST, 검색·select, pagination, 새 tab·modal, 누락·drift·실패
  축소 fixture
- 원문 byte, hash, collected_at과 locator provenance 보존

#### 완료 기준

- Source별 selector·field가 공통 Normalizer에 누출되지 않음
- 미등록 공개 홈 fixture에서 정책 메뉴·목록·상세 action profile을 생성함
- 생성한 profile replay가 재탐색 없이 같은 상세 identity와 필드를 추출함
- 같은 Raw replay가 외부 요청 없이 같은 추출 결과를 만듦
- profile drift가 빈 정책 0건 성공이 아니라 재탐색 또는 격리로 판정됨
- 실제 운영 HTML·개인정보·재배포 제한 자료가 Git에 포함되지 않음

#### 구현 결과 (`2026-08-11`)

- inventory `1.1.0`의 승인 Source만 여는 profile loader와 action 순서·상세
  evidence replay 검증을 구현했다.
- 합성 홈·목록·상세 fixture에서 의미 기반 메뉴 발견, 공통 `dl`·`table` field
  후보 추출과 profile drift 격리를 검증했다.
- Data Browser runner는 JSON stdin/stdout subprocess 경계, timeout·실패 분류와
  action replay 대조를 소유한다. 실제 Browser 실행 명령은 Source별 Adapter가
  등록할 때 이 경계를 소비하며 Frontend Playwright 모듈을 import하지 않는다.
- 공통 HTTP에 cookie 보존과 form POST를 추가하고 경북 승인 profile의 홈 GET →
  CSRF 포함 목록 JSON POST → 상세 modal POST를 목록 1회·상세 최대 3건·최소 2초
  간격으로 제한했다.
- 경북 목록·상세 Adapter, Raw 역할·목록 item parent·상세 external identity,
  Extractor와 Runtime offline replay를 연결했다. Source 전용 key는 공통 Normalizer에 누출하지 않고
  `extra`와 provenance에 보존한다.
- 저장소에는 합성·최소 구조 fixture만 포함했다. 제한 실사이트 preflight는
  요청 3회로 목록 총 243건과 표본 `no=1098` 한 건을 확인했으며 실제 응답 Raw는
  임시 디렉터리에서 삭제했다. PostgreSQL 적재와 지역 고유성 판정은 각각
  RYP5와 RYP3 범위로 남긴다.

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

#### 구현 결과 (`2026-08-11`)

- 정규화 전 `RegionalPolicyEvidence`와 `RegionalPolicyDecision` 계약을 추가해
  지역 판정과 신청 상태를 별도 축으로 기록한다.
- 지역 판정은 `regional_confirmed`, `regional_review_required`,
  `non_regional`, 신청 상태는 `open`, `scheduled`, `closed`,
  `review_required`를 사용한다. 두 축이 각각 `regional_confirmed`와 `open`일
  때만 Normalizer 후보로 전달한다.
- 시행기관·지원 대상·Source 지역이 같은 canonical 관할을 가리켜야 지역으로
  확정한다. 포털 소재지만 확인되거나 지역 근거가 부족하면 review로 격리하고,
  전국 재게시와 다른 지역 정책은 non-regional로 제외한다.
- 시·군·구 evidence는 광역 관할 안에 있는지 canonical parent 관계로 검증하고
  accepted 정책에는 더 구체적인 canonical include rule을 보존한다.
- 신청기간 두 날짜는 수집 기준일로 open·scheduled·closed를 계산한다. `상시`는
  open, 명시적 마감은 closed이며, 실제 소진 여부가 없는 `예산 소진 시까지`와
  기간 누락·오류는 review로 유지한다.
- 경북 mapper가 목록·상세의 시행기관, 대상 지역, 신청기간, 지원 내용과 locator·
  Raw provenance를 공통 Gate에 전달한다. RYP2의 실제 표본 `no=1098`은 지역
  근거는 확인됐지만 `2026-08-11` 기준 신청기간이 끝나 Runtime에서 closed로
  격리된다.
- 합성 계약 fixture 12건으로 지역 고유·시군구·전국·타 지역·모호 사례와
  open·scheduled·closed·상시·예산 상태를 결정적으로 검증했다.

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

#### 구현 결과 (`2026-08-11`)

- [x] 최신 완료 snapshot ID·수집 시각·건수와 PostgreSQL의 온통청년·복지로
  row 수를 묶는 읽기 전용 비교 기준선 loader 구현
- [x] 명시적 `plcyNo`·`servId`, canonical URL과 공식 공고 identity exact
  일치는 `excluded_aggregator_duplicate`로 판정
- [x] 제목·기관·canonical 지역·신청기간·지원내용 전체 fingerprint 일치는
  자동 병합하지 않고 `duplicate_review_required`로 격리
- [x] 제목만 같아도 비교 필드가 명확히 다르면 `accepted_regional`, 비교 근거가
  부족하면 review로 분리
- [x] 비밀 없는 후보 identity·match field·fingerprint와 기준선 ID를 결정
  manifest에 보존하고 `runtime/decisions/`를 Git에서 제외
- [x] 교차 Source 제외·검토는 `skipped_count`, Source 내부 중복만 기존
  `duplicate_count`로 집계

초기 구현은 DB·API Schema와 기존 aggregator row를 바꾸지 않는다. 경북 open
후보가 있을 때만 비교 기준선을 요구하며, 기준선이 없거나 불완전하면 적재하지
않고 실패 안전하게 review 또는 loader 오류로 중단한다. 합성 7개 계약 사례와
경북 open replay로 RYP-G2를 통과했다.

### RYP5 - 대표 Source actual 파일럿

#### 목적

서로 다른 구조의 대표 Source에서 실제 지역 정책을 끝까지 검증한다.

#### 작업

- RYP1 결과에서 Browser-only, 서버 HTML, 공개 API/JSON 또는 게시판형을
  대표하는 최대 3개 Source 선정
- Source마다 목록 1페이지와 상세 3~5건부터 제한 actual 실행
- 지역 고유성·중복 제외·정규화·품질 결과 수동 원문 대조
- accepted 정책의 PostgreSQL 적재와 Policy API·Browser 확인
- 같은 snapshot 재실행과 변경·drift·HTTP 실패 검증

#### 완료 기준

- 최소 3개 승인 Source 또는 승인 가능한 모든 대표 유형의 actual 결과가 있음
- 거짓·전국·중복 정책이 사용자 검색 결과에 포함되지 않음
- accepted 표본은 원문 → Raw → DB → API → Browser lineage가 일치함
- actual 실행 수치와 실패·제외·검토 필요 건수를 개발 기록에 남김

#### 구현 결과

- [x] `http_json` 경북, `http_html` 부산, `browser` 서울 3개 대표 유형을
  각각 목록 1회·상세 3건으로 제한 actual 실행
- [x] 경북 공식 `신청중` 필터와 지역 evidence 우선 상세 선택, 부산 HTML
  목록·상세 Adapter, 서울 Browser 관찰 JSON의 allowlist·identity 검증 구현
- [x] 9개 추출 중 경북 1건만 지역·신청 상태와 온통청년·복지로 중복 Gate를
  통과해 PostgreSQL에 적재하고 나머지 8건은 review·closed로 격리
- [x] 경북 표본의 Raw → 결정 manifest → PostgreSQL → Policy API → React
  상세 Browser lineage와 동일 Raw 재실행 `unchanged` 확인
- [x] selector·identity drift, Browser 캡처 drift, 결정적 offline replay와
  기존 HTTP 실패 회귀 검증

실행 수치, 일시 실패와 수정 내역은
[개발 기록](../../development_notes/data/regional_youth_policy_ingestion.md)에
남긴다. 파일럿은 3개 대표 구조만 구현하며 다른 승인 지역 확대는 RYP6 범위다.

### RYP6 - 지역별 순차 확대와 Forest 판정

#### 목적

파일럿 경계를 유지하며 승인 가능한 지역을 한 곳씩 확장한다.

#### 작업

- Source별 fixture·Adapter·actual 검증을 Conventional Commit 단위로 추가
- 각 Source 목록의 전체 pagination identity를 checkpoint로 순회하고 중단 뒤
  재개 가능한 batch 수집
- 발견한 모든 상세 identity를 accepted·duplicate·review·closed·failed 중
  하나로 집계해 조용한 누락 방지
- 각 지역의 최신·신청 가능 정책 수와 제외·실패·drift 통계 기록
- blocked Source의 재개 조건과 대체 공식 Source 기록
- 전체 회귀, 문서·계약과 Git 비추적 경계 대조

#### 완료 기준

- 17개 지역이 `implemented_http`, `implemented_browser`, `blocked`, `rejected`
  중 하나의 근거 있는 최종 상태를 가짐
- 모든 `implemented` Source가 제한 actual 수집·재실행·DB 인수를 통과함
- 승인 Source의 목록 total 또는 종료 조건과 상세 판정 합계가 일치함
- `blocked`·`rejected` Source를 우회하거나 성공으로 기록하지 않음
- 기존 온통청년·복지로와 Release 1 golden 검색 회귀가 통과함

## Gate와 실행 순서

| Gate | 승인 내용 | 다음 단계 |
| --- | --- | --- |
| `RYP-G0` | 17개 inventory, 범위·완료 기준과 DTL Gate | RYP1 |
| `RYP-G1` | 17개 Browser action profile·이용 조건·collection mode·예산 | RYP2 |
| `RYP-G2` | Adapter·지역 판정·중복 제외 fixture 통과 | RYP5 |
| `RYP-G3` | 대표 Source actual DB·API·Browser 인수 | RYP6 |
| `RYP-G4` | 지역별 최종 상태·전체 회귀·문서 대조 | Forest 완료 판정 |

```text
RYP0 inventory·v0.5.0 Gate
  → RYP1 Browser 홈페이지 탐색·Source 승인
  → RYP2 Browser Discovery Engine·profile replay·Adapter 실행 경계
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

- 홈·전체메뉴·검색·select·tab에서 정책 목록 후보를 찾는 Browser discovery
- JS `#none` click·POST form·modal·새 tab·pagination action profile replay
- DOM drift 때 제한 재탐색과 빈 결과 성공 방지
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

- 승인 Source별 홈 → 메뉴·검색 → 목록 → 상세 Browser 경로와 interaction 예산
- 선택된 collection mode의 제한 목록·상세 호출과 요청 예산 준수
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
- 승인 Source는 재현 가능한 Browser action profile, 허용된 목록·상세 endpoint,
  collection mode와 interaction/request 예산을 가짐
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

Forest 완료 전 17개 로그인 없는 공개 사이트 모두에 Browser Discovery를 실제
시도한다. 단, 로그인 불필요와 기술적 접근 가능성이 자동 수집 허용을 뜻하지는
않는다. 이용 조건·접근 경계·데이터 품질 때문에 운영 수집할 수 없는 Source는
마지막 성공 discovery 단계, 근거와 재개 조건을 가진 `blocked` 또는 `rejected`
상태로 남긴다.

## v0.5.0과 DTL Gate 연결

Data 05는 `v0.5.0` 필수 범위다. DTL4-4와 Integration 08의 승인 Schema·DB·API·
UI 기준선을 재사용하므로 DTL4-5 계약 소비 대조를 기다리지 않고 RYP0 inventory와
RYP1 Browser Discovery preflight를 병렬 수행할 수 있다.

- DTL4-5 / W4-G1: Data 05는 기존 Schema를 바꾸지 않는다는 소비 경계를 대조
- DTL4-6 / W4-G2: RYP0~RYP4 inventory·Adapter·지역 판정·중복 제외 테스트 통과
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

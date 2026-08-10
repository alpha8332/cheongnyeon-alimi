# Data 04 Public HTTPS Policy Ingestion Forest 개발 계획

## 계획 정보

- 번호: Data 04
- 담당 영역: Data
- 상태: draft
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 선행 Forest: Integration 05 Contract Baseline, Data 01 Data Pipeline
- 후속 Forest: Integration 08 Eligibility Evidence and Summary
- 권장 브랜치: `feature/data/public-web-policy-source`
- W4-G0 승인 Source: `cheonan-youthcenter-web`, 공지 `notice:674`

## 목적

공공 API만으로 부족한 정책 상세·신청 조건을 보강하기 위해, 승인된 공식
HTTPS 사이트 한 곳의 공개 목록과 상세 페이지를 제한적으로 수집하고 기존
Raw → Extract → Normalize → Validate → PostgreSQL 흐름에 연결한다. 임의의
웹사이트를 범용적으로 긁는 크롤러가 아니라 Source별 계약과 근거를 가진 첫
웹 Source 세로 기준선을 만든다.

## 범위

- 대표 공식 HTTPS 사이트 한 곳 선정과 robots·이용약관·라이선스 preflight
- 로그인 없이 공개된 목록·상세 URL의 제한 수집
- 정적 HTML 또는 이용 조건이 허용하는 공개 내부 API 우선 검토
- 목록·상세 Extractor 분리와 Source별 selector·field mapping 관리
- `RawPolicyDocument`의 `raw_format=html` envelope와 content hash 재사용
- 정책 identity, 상세 연결, 출처 URL·수집 시각·필드 provenance 보존
- 정책명·기관·신청 기간·지원 내용·신청 조건·제외 조건·필요 서류 추출
- 선택 필드 누락, HTML 구조 변경, HTTP 오류의 실패 격리
- 동일 페이지 재수집의 idempotency와 변경 감지
- 검토된 축소 HTML fixture, 실제 제한 수집과 PostgreSQL 적재 검증

## 범위 밖

- 임의 사이트를 자동 탐색하는 범용 크롤러
- 로그인·CAPTCHA·접근 통제 우회
- robots 또는 이용약관이 금지하는 수집·보존
- Playwright·Selenium의 기본 도입
- 전체 사이트 미러링, 첨부파일 대량 보존과 검색엔진 구축
- Scheduler·분산 queue·worker 플랫폼
- Source 근거가 없는 조건 추정과 LLM 생성 요약
- 둘 이상의 웹 Source 동시 지원

## 선행 조건

- W4-G0에서 천안청년센터 공지, 허용 경로, 요청 빈도와 보존 범위를 승인했다.
- 실제 페이지와 robots·이용약관은 착수 시점에 다시 확인하고 근거 시각을
  기록해야 한다.
- 대상 페이지가 정적 HTML인지 공개 내부 API인지 확인한 뒤 구현 방식을
  선택해야 한다.
- Data 01의 Raw envelope, Source Adapter, Normalizer와 Runtime Raw 비추적
  경계를 재사용해야 한다.

## 공통 설계 원칙

- HTTP client는 수집하고 Extractor는 Source 구조를 해석하며, 공통
  Normalizer는 CSS selector나 Source별 key를 알지 않는다.
- 원문과 구조화 값 사이의 provenance를 보존하고 추출하지 못한 값은
  `null`·빈 배열·확인 필요 상태로 남긴다.
- 공개된 정보라도 요청량을 최소화하고 목록 전체보다 필요한 상세만 호출한다.
- 실제 운영 HTML은 Git에 넣지 않고, 비밀·개인정보·재배포 조건을 검토한 축소
  fixture만 커밋한다.
- DOM 구조 변경을 정상적인 빈 값으로 숨기지 않고 selector drift로 분류한다.

## Slice 계획

### DW0 - Source 선정과 수집 계약

- 승인 Source `cheonan-youthcenter-web`과 표본 `notice:674`의 착수 시점 DOM·
  robots·이용 조건이 W4-G0 근거에서 바뀌지 않았는지 재확인한다.
- 목록 1회·승인 상세 1건, 동시 요청 1개·최소 2초 간격과 제외 URL을 구현
  allowlist로 고정한다.
- canonical URL과 `notice:{wr_id}` identity를 확정하고 API와 자동 병합하지 않는다.

### DW1 - 축소 fixture와 Source Adapter

- 목록·상세 정상, 선택 필드 누락과 구조 변경을 대표하는 검토된 fixture를 만든다.
- HTTP fetch와 list/detail Extractor를 분리하고 selector·mapping을 Source별
  설정에 모은다.
- 정책 상세 연결, pagination과 재시도·timeout 경계를 구현한다.

### DW2 - 정규화·근거·품질 연결

- 기존 공통 필드와 신청 조건·제외 조건·필요 서류 후보를 추출한다.
- 필드별 source URL·selector 또는 source field와 원문 evidence를 보존한다.
- 필수 필드 누락, selector drift와 HTTP 실패를 정상 정책과 격리한다.

### DW3 - PostgreSQL 적재와 actual 재검증

- 같은 페이지 재수집이 중복 row를 만들지 않고 변경 페이지는 updated로
  분류되는지 검증한다.
- 승인 범위의 실제 제한 수집을 실행하고 Raw → 정책 상세 API까지 lineage를
  대조한다.
- 실제 수집 건수·실패·누락과 실행한 검증을 Data 개발 기록에 남긴다.

## 검증 계획

- HTML fixture의 list/detail·누락 필드·selector drift 단위 테스트
- HTTP 정상·timeout·retry·비정상 상태와 요청 제한 테스트
- Raw envelope·content hash·provenance·정규화 Schema 테스트
- 전용 PostgreSQL의 최초 적재·동일 재실행·변경 재실행 통합 테스트
- 승인 Source의 제한 actual 수집과 정책 상세 API 대조
- `python scripts/validate_docs.py`
- `git diff --check`

외부 Source를 호출하지 못했으면 fixture 테스트만으로 actual 검증을 통과 처리하지
않는다.

## Forest 완료 기준

- 승인된 공식 HTTPS Source 한 곳의 목록·상세가 기존 파이프라인에 연결됨
- robots·이용약관·라이선스와 요청 범위의 검토 근거가 기록됨
- 신청 조건 보강 필드가 출처·수집 시각·원문 evidence와 함께 보존됨
- 같은 입력 재실행은 중복을 만들지 않고 구조 변경·실패는 격리됨
- fixture 단위 테스트와 PostgreSQL 통합 테스트가 통과함
- 승인 범위 actual 수집과 PostgreSQL 적재가 실행돼 결과가 기록됨
- 데이터·운영 기준 문서와 실제 구현·검증 결과가 일치함

## 위험과 미확정 사항

- Source는 승인됐지만 실제 DOM Selector와 정적 HTML 재현성은 Data 04 착수
  시점에 다시 확인해야 한다.
- 게시일·본문 신청기간·제목이 충돌하는 승인 표본은 `partial`·`unknown`으로
  보존하고 현재 신청 가능 여부를 추정하지 않는다.
- 정책 페이지 DOM·내부 API·이용 조건은 바뀔 수 있으므로 착수 시점의 실제
  확인이 필요하다.
- 같은 정책이 API와 웹에 동시에 존재할 때 자동 병합 기준은 현재 미확정이다.
  Source별 identity를 유지하고 cross-source 동일성은 별도 계약 없이 단정하지
  않는다.
- 동적 렌더링만 가능한 경우 browser automation을 즉시 추가하지 않고 정적
  endpoint, 공개 내부 API, 다른 공식 Source 또는 범위 조정안을 비교한다.

## 관련 문서

- [v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- [Eligibility Evidence and Summary](../integration/08_eligibility_evidence_summary.md)
- [Data Pipeline](01_data_pipeline.md)
- [Data Source 계약](../../../data/data_sources.md)
- [수집 정책](../../../data/collection_policy.md)
- [데이터 Schema](../../../data/data_schema.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)

# Data 06 Supplemental Official Policy Ingestion Forest 개발 계획

## 계획 정보

- 번호: Data 06
- 담당 영역: Data
- 상태: completed
- 진행: `SOP-G0_PASS`~`SOP-G5_PASS`
- 착수 조건: `W5-G0_PASS` 완료
- 계획일: `2026-08-11`
- 승인일: `2026-08-16`
- 완료 기준 재승인일: `2026-08-17`
- 실행 일정: `2026-08-14` 재승인으로 4주차에서 5주차로 이동
- 대상 Release: `v0.5.0`
- 선행 Forest: Data 02 Release Dataset Bootstrap, Data 03 Recurrent Collection
  and Quality Operations, Data 04 Public HTTPS Policy Ingestion, Data 05
  Regional Youth Policy Ingestion의 RYP2~RYP4 공통 실행·중복 판정 경계
- 후속 통합: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/data/supplemental-official-policy-ingestion` 한 개.
  Data 05 공통 엔진과 Gate가 안정되기 전에는 만들지 않으며 Source별 브랜치를
  추가하지 않음
- 현재 Slice: SOP4~SOP5 제한 actual·DB·API·Browser·전체 회귀 완료.
  Integration 07 `DTL5-4` / `W5-G1` 인계

## 목적

현재 승인 Source인 온통청년·복지로에 없거나 정보가 부족한 실제 신청 가능
청년정책을 중앙부처·공공기관의 공식 목록·상세 Source에서 찾아 기존 Raw →
Extract → Normalize → Validate → PostgreSQL 흐름에 연결한다.

URL 도메인이 다르다는 이유만으로 새 정책이라고 판단하지 않는다. 동일 정책이
온통청년·복지로에 있으면 새 Policy row를 만들지 않고, 공식 원문과 현재
snapshot을 근거로 비밀 없는 제외 판정을 남긴다.

## 현재 입력 기준선

사용자 제공 `청년정책_데이터수집_완료.xlsx`의 `청년정책 세부 수집방안`
`A1:F71`에는 URL이 있는 정책 후보 64행이 있다.

- 온통청년·복지로 직접 URL: 11행
- 그 외 도메인 URL: 53행
- 정확히 같은 정책명·URL의 반복 행: 청년버팀목 전세자금대출, 청년 채무조정,
  이주배경청년 지원, 청년예술인 적립계좌
- 서로 다른 정책명이 같은 URL을 쓰거나 제목과 서류가 맞지 않는 행이 있으므로
  XLSX 문구를 정책 데이터나 서류 evidence로 직접 import하지 않음
- Data 05 부산 inventory에는 32행의 지역 상세 공고를 탐색 seed로만 전달하고,
  나머지 중앙·공공기관 후보는 이 Forest에서 분리 관리

이 수치는 후보 inventory의 입력 품질 기준선이며 실제 Source 승인이나 현재
신청 가능 정책 수를 뜻하지 않는다.

## 대상 Source군과 우선순위

| 우선순위 | Source군 | 초기 목적 | 초기 상태 |
| ---: | --- | --- | --- |
| 1 | 고용24 | 공개 정책 목록·상세와 stable system ID 확인 | candidate-unverified |
| 1 | LH 청약플러스 | 청년 임대 공고 목록·상세와 공고 ID 확인 | candidate-unverified |
| 1 | K-Startup | 청년 대상 창업 공고와 공개 공고 ID 확인 | candidate-unverified |
| 1 | 한국장학재단 | 현재 신청 가능한 장학·근로 정책과 공식 상세 확인 | candidate-unverified |
| 2 | 서민금융진흥원 | 청년 금융상품의 공식 조건·신청 채널 확인 | candidate-unverified |
| 2 | 주택도시기금 | 청년 주거금융 상품의 공식 조건·신청 채널 확인 | candidate-unverified |
| 3 | 외교부·행안부·NIA·한국임업진흥원 | 게시판형 모집·교육 공고 확인 | candidate-unverified |
| 4 | 청년문화예술패스·농식품바우처·K-패스 | 전용 공식 사이트의 현재 신청 경계 확인 | candidate-unverified |

공공데이터포털 홈과 범용 기관 홈은 정책 endpoint가 아니므로 discovery reference로만
사용한다. 실제 목록·상세 allowlist를 찾지 못하면 Source로 승인하지 않는다.

## 선행 조건

- Data 05 RYP2의 공통 HTTP·Raw·snapshot·Source Adapter 실행 경계를 재사용할
  수 있어야 한다.
- Data 05 RYP4의 온통청년·복지로 snapshot loader와 교차 Source 중복 판정이
  테스트로 고정돼야 한다.
- 후보 XLSX의 중복·오연결·문구 불일치를 먼저 격리하고 원문 근거 없는
  필요서류를 사용하지 않는다.
- Source별 운영 주체, robots, 이용약관, 라이선스, 저장·변환·재배포 경계를
  승인하기 전에는 Adapter와 actual 대량 수집을 시작하지 않는다.
- API·Schema·Migration·TypeScript 변경 필요가 발견되면 Data 단독으로
  확정하지 않고 Backend·Frontend 소비 영향을 공동 검토한다.

## 범위

- 제공 XLSX의 정책명·기관·URL을 후보 inventory로 변환하고 오류·중복 상태 관리
- 온통청년·복지로 승인 snapshot과 PostgreSQL row 기준의 선행 중복 감사
- 공식 운영 주체·robots·약관·라이선스·공개 접근 조건 Source preflight
- 승인된 공식 목록·상세·공개 API/JSON endpoint와 요청 예산 allowlist
- Source별 stable external identity와 canonical URL
- 기존 공통 HTTP·Raw·snapshot·CollectionRun·Normalizer·Importer 재사용
- 현재 신청 가능성, 청년 대상 근거와 공식 신청·문의 채널 판정
- exact ID·URL·공고 ID와 보수적 fingerprint 기반 교차 Source 제외
- 승인 Source의 제한 actual 수집과 PostgreSQL → Policy API → Browser 대조
- Source별 implemented·blocked·rejected 상태와 재개 조건 기록

## 범위 밖

- 검색엔진이나 임의 도메인 재귀 탐색 범용 크롤러
- 로그인·CAPTCHA·접근 통제·robots·약관 우회
- XLSX의 필요서류·설명 문구를 공식 원문 확인 없이 사용자 데이터로 승격
- 제목만 같은 정책의 자동 병합·삭제
- 온통청년·복지로 기존 row의 자동 합성·덮어쓰기
- PDF·HWP·첨부파일의 일괄 다운로드와 원문 Git 재배포
- 개인 전화번호·개인 이메일·성명 구조화
- 관리자 교차 Source 검토 UI와 범용 데이터 편집 도구
- Scheduler·분산 queue·worker·Production 배포 구성

## 공통 설계 원칙

### Source와 Policy 후보 분리

XLSX의 한 행은 Source 승인이나 Policy 적재 단위가 아니다. Source inventory는
공식 운영 주체와 안정적인 목록·상세 계약을 관리하고, 실행 중 발견한 Policy
후보는 Raw identity와 중복 판정을 별도로 가진다.

### 중복 우선

Source Adapter 구현 전에 현재 온통청년·복지로 snapshot과 비교한다. 직접
`plcyNo`·`servId`, canonical URL, 공식 공고 ID가 일치하면 확정 중복으로
제외한다. 제목만 같거나 기관·기간·지원내용이 모호하면 자동 제외하지 않고
review 상태로 격리한다.

### 실제 신청 가능성과 청년 대상 근거

공식 원문에 신청 기간·상시·예산 소진·다음 모집 일정 중 하나와 청년 대상
근거가 있어야 사용자 Policy 후보가 된다. 상품·제도 소개 홈, 마감 공고와
로그인 후에만 확인 가능한 신청 정보는 현재 신청 가능 정책으로 추정하지 않는다.

### 기존 계약 재사용

초기 구현은 NormalizedProgram 1.2.0, EligibilitySummary 1.0.0, 기존 Importer와
Policy API를 바꾸지 않는다. Source별 selector·field·pagination은 Adapter에
가두고 공통 Normalizer에 누출하지 않는다.

## Slice 계획

### SOP0 - 후보 정제와 실행 inventory

#### 목적

XLSX를 검증 가능한 Source·Policy 후보 inventory로 변환한다.

#### 작업

- 64개 URL 행의 exact title·URL 중복 제거와 충돌 행 격리
- 직접 온통청년·복지로 11행을 비교 fixture로 분리
- 독립 도메인 후보를 Source군과 공식 상세 후보로 분류
- `candidate`, `approved`, `blocked`, `rejected`와 `data_error` 상태 확정
- 입력 파일명·시트·행과 변환 결과 lineage 보존

#### 완료 기준

- 같은 정책명·URL 반복이 하나의 후보 identity로 정리됨
- 제목·URL·서류 불일치 행은 승인 후보에 포함되지 않음
- 실행 inventory가 JSON Schema와 결정적 검증을 통과함

### SOP1 - 온통청년·복지로 선행 중복 감사

#### 목적

명백히 중복인 후보에 불필요한 Source 구현 비용을 쓰지 않는다.

#### 작업

- 비교 snapshot ID·수집 시각·정책 건수 고정
- 직접 ID·URL·공고 ID exact 비교
- 제목·기관·기간·지원내용 fingerprint 후보 비교
- exact duplicate·review required·potentially new 분류

#### 완료 기준

- 확정 중복은 Source 구현·Policy 적재 후보에서 제외됨
- 불확실 후보는 사용자 검색에 노출되지 않음
- 기준 온통청년·복지로 row를 수정·삭제하지 않음

### SOP2 - Source preflight와 allowlist 승인

#### 목적

수집이 허용되고 결정적인 공식 Source만 구현 대상으로 승인한다.

#### 작업

- 운영 주체·공식 도메인·robots·약관·라이선스 확인
- 목록·상세·pagination·external identity·rate limit 후보 기록
- API → 서버 HTML → 공개 JSON/XHR 순서로 수집 방식 선택
- 로그인·첨부 의존·불명확 라이선스 Source의 blocked·rejected 판정

#### 완료 기준

- 각 Source군에 승인 Source 또는 비승인 사유가 있음
- 승인 Source는 요청 예산과 목록·상세 allowlist를 가짐
- 이용 조건이 불명확한 Source를 구현 대상으로 승인하지 않음

### SOP3 - Source Adapter와 판정 fixture

상태: completed (`SOP-G3_PASS`, 2026-08-17)

#### 목적

승인 Source를 기존 파이프라인과 중복 Gate에 안전하게 연결한다.

#### 작업

- stable `(source_id, external_id)`와 canonical URL
- 목록·상세·누락·drift·실패 최소 fixture
- 청년 대상·신청 가능·기관·조건·서류 evidence mapping
- 교차 Source exact·fingerprint 판정 연결
- Raw byte·hash·collected_at·locator provenance 보존

#### 완료 기준

- 같은 Raw replay가 외부 요청 없이 같은 결과를 만듦
- Source별 field가 공통 Normalizer에 누출되지 않음
- 중복·마감·근거 부족 후보가 Policy row를 만들지 않음

### SOP4 - 우선 Source actual 파일럿

#### 목적

구조가 다른 우선 Source에서 실제 신규 정책을 끝까지 검증한다.

#### 작업

- 우선순위 Source군에서 재승인 범위인 승인 Source 5개 선정
- Source마다 목록 1페이지와 상세 3~5건 제한 호출
- 원문·중복·신청 가능·정규화·품질 수동 대조
- accepted 정책의 PostgreSQL·Policy API·Browser 확인
- 동일 snapshot 재실행과 drift·HTTP 실패 검증

#### 완료 기준

- 승인 Source 5개의 제한 actual과 offline replay 통과
- 중복 제외를 거친 신규 정책을 1개 이상 PostgreSQL·Policy API에서 인수
- duplicate·review·closed·failed가 Policy row를 만들지 않음
- accepted 정책의 Browser 검색·상세 actual 확인
- 최소 기준을 충족하지 못하면 W5-G1을 통과시키지 않고 원인 기록
- 신규·중복·검토·실패 수치와 lineage가 개발 기록에 있음

### SOP5 - 승인 Source 확대와 Forest 판정

#### 목적

동일 경계를 유지해 나머지 후보 Source군을 순차 판정한다.

#### 작업

- 우선순위 2~4 Source의 fixture·Adapter·actual 순차 추가
- 각 Source군의 implemented·blocked·rejected 상태와 재개 조건 기록
- 전체 온통청년·복지로·지역 정책·Release 1 검색 회귀
- Git 비추적 Raw·개인정보·비밀 경계 대조

#### 완료 기준

- 계획의 모든 Source군이 근거 있는 최종 상태를 가짐
- 모든 approved Source가 제한 actual·재실행을 통과하고 비accepted 결과는 DB에서 격리됨
- 승인 Source 5개가 `implemented_http`이며 신규 정책 1개 이상이 DB·API에 연결됨
- 기존 Policy identity와 검색 golden이 회귀하지 않음

## Gate와 실행 순서

| Gate | 승인 내용 | 다음 단계 |
| --- | --- | --- |
| `SOP-G0` | 정제 inventory·오류 격리·완료 기준 | SOP1 |
| `SOP-G1` | snapshot 중복 감사와 잠정 신규 후보 | SOP2 |
| `SOP-G2` | Source 이용 조건·allowlist·요청 예산 | SOP3 |
| `SOP-G3` | Adapter·판정 fixture | SOP4 |
| `SOP-G4` | 우선 Source actual DB·API·Browser | SOP5 |
| `SOP-G5` | 전체 Source 상태·회귀·문서 | Forest 완료 판정 |

```text
Data 05 RYP2~RYP4 공통 엔진·중복 Gate
  → SOP0 후보 정제
  → SOP1 온통청년·복지로 중복 감사
  → SOP2 Source preflight
  → SOP3 Adapter·판정 fixture
  → SOP4 우선 Source actual
  → SOP5 Source 확대·전체 회귀
```

Data-only 구현은 5주차 시작 커밋 `29b2dd5`의 W5-G0 통과 뒤 시작한다.
SOP0~SOP3는 Backend·Frontend 안정화와 병렬로 진행할 수 있지만,
SOP4~SOP5 actual과 전체 통합 판정은 같은 W5-G1에서 대조한다.

## 역할 분담

| 역할 | 책임 |
| --- | --- |
| Data | 후보 정제, Source preflight, Adapter·Extractor, 중복·신청 가능 판정, Raw·provenance, actual 적재 |
| Backend | 기존 Importer·Policy API 회귀 확인. 새 관계나 DB 필드가 필요할 때만 공동 계약 뒤 구현 |
| Frontend | 기존 검색·상세에서 accepted 정책 표시 회귀. 중복 검토 UI는 별도 승인 전 구현하지 않음 |
| Team Leader | v0.5.0 범위·Source 이용 조건 승인, 원문 → DB → API → Browser Gate와 우선순위 조정 |

## 검증 계획

### 단위·계약

- inventory JSON Schema, exact 중복과 오류 행 격리
- stable external identity·canonical URL·pagination
- 청년 대상·현재 신청·마감·근거 부족 fixture
- 온통청년·복지로 exact ID·URL·공고 ID·fingerprint 후보
- 선택 필드 누락·drift·HTTP 실패와 Raw replay

### PostgreSQL·통합

- 최초 insert·동일 unchanged·수정 updated·실행 내 duplicate
- 확정 중복·검토·마감 후보의 Policy 미적재
- accepted 정책의 region·search projection·eligibility evidence
- 기존 온통청년·복지로·지역 Source identity와 row 불변

### actual 인수

- 승인 Source별 제한 요청 예산 준수
- 공식 원문과 청년 대상·신청 가능·중복 판정 표본 대조
- Runtime Raw → PostgreSQL → Policy API → Browser lineage
- Release 1 snapshot 3,156건과 golden 검색 회귀

### 문서

```powershell
python scripts/validate_docs.py
git diff --check
```

## Forest 완료 기준

- 모든 계획 Source군이 implemented·blocked·rejected 중 하나의 근거를 가짐
- 승인 Source 5개의 제한 actual·offline replay가 완료됨
- 실제 신규 청년정책 1개 이상이 중복 제외를 거쳐 DB·API에 연결되고 actual
  Browser 검색·상세가 확인됨
- 온통청년·복지로 중복·마감·근거 부족·XLSX 오류가 새 Policy row를 만들지 않음
- accepted 정책의 기관·기간·조건·신청 채널과 provenance가 원문과 일치함
- 동일·수정·중복·drift·HTTP 실패가 정상 정책과 격리됨
- 기존 지역 정책·온통청년·복지로·Release 1 검색 회귀가 통과함
- 실제 Raw·운영 HTML·첨부·개인정보·비밀키가 Git에 없음
- 단위·PostgreSQL·actual API·Browser·문서 검증 결과가 개발 기록에 있음

## v0.5.0과 5주차 Gate 연결

- W5-G0: 4주차 병합 기준선·Data 05 snapshot·기존 중복 Gate 고정
- W5-D1: SOP0~SOP2 inventory·중복·Source preflight
- W5-D2: SOP3 Adapter·판정 fixture와 공통 회귀
- W5-D3 / W5-G1: SOP4~SOP5 actual DB → API → Browser, 전체 Source 상태와
  Forest 완료 판정

Data 06이 완료 기준을 충족하지 못하면 `v0.5.0` 보완 Source 기능이 미완료이므로
W5-G1을 통과시키지 않는다. `2026-08-17` 재승인은 신규 정책 수를 근거 있는 1개
이상으로 조정하되, 승인 Source 5개 actual과 중복·review 무적재, Browser actual
인수 품질 Gate는 유지한다.

구체적인 일차별 실행과 Team Leader Gate는
[5주차 Data·Team Leader 실행 계획](../../weekly_plan/week_05_data_team_leader.md)을
따른다. 이 계획의 `approved`는 Source 승인이나 구현 완료를 뜻하지 않는다.

## 위험과 미확정 사항

- 독립 도메인 53행 중 다수가 온통청년·복지로에 다른 이름으로 존재할 수 있다.
- XLSX에는 같은 URL의 다른 제목, 제목과 필요서류 불일치가 있어 원문 대조 전
  신뢰할 수 없다.
- 상품 소개 홈과 현재 모집 공고를 구분하지 않으면 마감·비신청 데이터를 노출한다.
- 일부 Source는 로그인·첨부파일 또는 JavaScript 요청에 핵심 조건이 있을 수 있다.
- Source군 확대는 요청 예산·실행 시간·drift 유지 비용을 크게 늘린다.
- 재승인된 actual 목표가 이용 조건·기술 접근 때문에 불가능하면 Release 범위를
  조용히 축소하지 않고 W5-G1 blocked 또는 추가 계획 재승인을 선택한다.

## 관련 문서

- [Regional Youth Policy Ingestion](05_regional_youth_policy_ingestion.md)
- [Release Dataset Bootstrap](02_release_dataset_bootstrap.md)
- [Recurrent Collection and Quality Operations](03_recurrent_collection_quality_operations.md)
- [Public HTTPS Policy Ingestion](04_public_https_policy_ingestion.md)
- [Release 2 Feature Acceptance](../integration/07_release_2_feature_acceptance.md)
- [전체 Forest 로드맵](../forest_roadmap.md)
- [Release와 Milestone 계획](../release_roadmap.md)
- [데이터 소스](../../../data/data_sources.md)
- [Source Profile](../../../data/source_profiles.md)
- [수집 정책](../../../data/collection_policy.md)

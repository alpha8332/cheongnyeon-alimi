# 3주차 Data·Team Leader 실행 계획

## 계획 정보

- 상태: approved
- 대상 주차: 3주차
- 대상 Release: `v0.1.0`
- 수행 역할: Data 담당, Team Leader - Integration
- 연계 담당: Backend, Frontend, 보고서, 사용성 리뷰어, QA
- 상위 계획: [3주차 전체 상세 계획](week_03_release_1.md)

이 문서는 Data 담당과 Team Leader를 같은 사람이 수행하는 현재 역할 배정을
기준으로 한다. Data 구현 결과를 직접 만들면서 동시에 Backend·Frontend
의존성을 조정하고 Release Gate를 판단하되, 자신의 Data 결과만으로 통합이나
릴리스 통과를 승인하지 않는다.

## 담당 목표

1. 실제 Source의 릴리스 수집 범위와 품질 기준을 확정한다.
2. 실제 정책 snapshot을 PostgreSQL에 재현 가능하게 적재한다.
3. 실제 데이터 근거로 Data·Backend·Frontend 검색 계약을 조정한다.
4. 각 담당자의 결과를 실제 DB → API → UI로 연결한다.
5. golden query와 독립 검증 증거를 확인해 `v0.1.0` 후보 여부를 결정한다.

## 전체 실행 순서

```text
DT0 시작 기준·담당·Forest 확인
  ↓
DT1 Source preflight·대표 표본·릴리스 범위
  ↓
DT2 검색 계약 공동 승인
  ├──────────────┬──────────────┐
  ↓              ↓              ↓
DT3 Data 구현    BE 검색 구현    FE 검색 구현
  ↓              ↓              ↓
DT4 실제 DB·품질 인계
  └──────────────┴──────────────┘
                 ↓
DT5 실제 데이터 통합·결함 조정
                 ↓
DT6 golden query·Release 1 판정
```

DT1을 수행하는 동안 Backend의 자연어 해석 코드 조사·테스트 골격과
Frontend의 해석 조건·검색 이유 UI prototype은 병렬로 진행할 수 있다.
DT2 검색 계약이 승인된
뒤에는 세 영역이 본 구현을 병렬로 진행한다.

## Slice DT0 - 시작 기준과 실행 경계 확정

### 목적

2주차 작업과 3주차 구현을 섞지 않고, 실제 작업을 시작할 수 있는 기준과
담당 Forest를 확정한다.

### 선행 조건

- 현재 브랜치와 작업 트리 확인
- Backend 03·Frontend 02를 포함한 2주차 결과의 `develop` 병합 확인
- Data 01·Integration 02 계획과 개발 기록 확인
- Release·Forest·3주차 전체 계획 확인

### 수행 작업

#### Data 역할

- 두 Source의 현재 Collector·Extractor·Normalizer와 Runtime importer 경계를
  다시 확인한다.
- 실제 Raw root가 `runtime/raw`이고 Git 제외 대상인지 확인한다.
- API 키 존재 여부만 확인하고 값, 요청 query와 payload를 출력하지 않는다.
- PostgreSQL Migration 적용 대상과 실제 snapshot 적재 DB를 구분한다.

#### Team Leader 역할

- Data 02, Backend 06, Frontend 04, Integration 03 상세 Forest 계획 작성
  필요 여부와 담당자를 확인한다.
- Backend·Frontend 담당자에게 3주차 시작 기준과 Critical Path를 공유한다.
- 보고서 담당, 사용성 리뷰어와 QA가 사용할 증빙·결함 기록 위치를 정한다.
- 각 Forest 브랜치는 최신 `develop`에서 시작하고 Slice마다 브랜치를 만들지
  않는다는 기준을 확인한다.

### 병렬 가능한 다른 담당 작업

- Backend: 현재 Policy Repository·Service·API 분석과 테스트 골격
- Frontend: Backend 해석 조건·검색 이유 표시와 query state 조사
- QA: 검색 정상·빈 결과·경계값·실패 smoke 초안
- 보고서: Release 1 증빙 목차와 수집 양식

### 완료 기준

- 2주차 `develop` 기준 SHA와 3주차 담당·Forest 경계가 확인됨
- 비밀 주입, Runtime 경로와 PostgreSQL 실행 환경이 확인됨
- 실제 결과를 기록할 개발 기록과 검증 위치가 정해짐

### 후속 해제

DT0 완료 후 DT1 Source preflight와 각 담당자의 준비 작업을 시작할 수 있다.

## Slice DT1 - Source preflight와 대표 실데이터 확인

### 목적

전체 수집 구현 전에 두 Source의 실제 pagination·호출 제약과 검색에 필요한
필드 분포를 확인한다.

### 선행 조건

- DT0 완료
- API 키 안전 주입과 호출량 보호 기준 확인
- 기존 실제 호출 기록과 Source Profile 확인

### 수행 작업

#### Source 실행 전

- 현재 Source endpoint, 필수 parameter, page·limit 의미를 확인한다.
- 온통청년 계정별 호출 한도와 오류 payload의 확인 가능 범위를 정한다.
- 복지로 detail 호출 제한을 유지하고 불필요한 상세 호출을 하지 않는다.
- 한 번의 preflight에서 허용할 목록·상세 요청 수를 기록한다.

#### 대표 표본 수집

- 온통청년과 복지로 각각 최소 범위의 최신 목록을 수집한다.
- Raw 저장 경로, parent·detail 관계와 비밀 제거를 확인한다.
- 외부 응답을 수정하지 않고 Raw 원문과 수집 metadata를 보존한다.
- 수집 실패 시 재시도 가능 오류와 즉시 중단 오류를 분류한다.

#### 분포 분석

최소한 다음을 Source별로 집계한다.

- 목록·상세·Raw 문서와 추출 정책 수
- `valid`, `partial`, `invalid`
- 지역 원문·코드, 시·도, 시·군·구와 전국 표현
- `age_min`, `age_max`, 연령 원문과 연령 조건 미상
- 카테고리 원문과 정규화 categories
- 신청 시작·종료·상시·예산 소진과 신청 상태
- 제목·요약·지원 내용·자격 조건의 월세·주거 검색 가능 표현
- external ID, 중복 후보와 source URL

#### 릴리스 범위 초안

- 한 페이지만 임의로 Release 데이터로 정하지 않는다.
- Source별 전체 page 수 또는 종료 판정 방식을 확인한다.
- 할당량 안에서 재현 가능한 릴리스 수집 범위를 제안한다.
- 전체 순회가 불가능하면 범위, 제외 데이터와 사용자 영향까지 기록한다.

### 기다리지 않아도 되는 다른 작업

DT1 전체가 끝나기 전에 Backend와 Frontend는 다음을 진행할 수 있다.

- Backend `W3-B0`: query DTO, Repository 변경 지점과 테스트 골격
- Frontend `W3-F0`: Backend 해석 조건·검색 이유 표시 prototype

다만 지역 계층, 연령 조건 미상, 기본 status와 partial 의미는 확정 구현하지
않는다.

### 산출물

- Source별 preflight 결과
- 대표 실데이터의 필드·품질 분포
- 릴리스 수집 범위와 호출 예산 초안
- 지역·연령·상태·검색 계약에서 결정해야 할 질문 목록

실제 Raw, 인증키와 DB 파일은 산출물 문서나 Git에 포함하지 않는다.

### 완료 기준

- 두 Source에서 검색 계약 결정에 충분한 실제 표본이 확보됨
- 기존 실제 수집이 모두 partial이었던 원인이 현재 표본에서도 확인됨
- 지역·연령·상태·검색 필드의 실제 표현과 누락 비율을 설명할 수 있음
- 릴리스 수집 범위 초안을 Data·Backend·Frontend가 검토할 수 있음

### 후속 해제

- DT2 검색 계약 공동 검토
- Backend의 지역·연령 검색 의미와 index 설계
- golden query에 맞는 실제 정책 후보 조사

## Slice DT2 - 검색 계약 공동 결정과 Gate G1 주관

### 목적

Data 표본, Backend 자연어 해석 초안과 Frontend 표시 prototype을 하나의 검색 계약으로
정리하고 세 영역의 본 구현을 해제한다.

### 선행 조건

- DT1의 대표 표본·분포와 릴리스 범위 초안
- Backend `W3-B0`의 API·Repository 초안
- Frontend `W3-F0`의 해석 조건 표시·query state 초안

Backend나 Frontend 초안이 준비되지 않았다면 Data 계약을 단독 승인하지
않는다. 기다리는 동안 DT3의 pagination·수집 실행 구조 중 검색 계약과
독립적인 부분을 준비할 수 있다.

### 수행 작업

#### Data 담당 결정안

- 온통청년 지역 코드의 표준 이름과 버전 고정 근거
- 복지로 지역 정보 부재 시 처리
- 연령 원문 누락·상한·하한 처리
- 신청 상태와 수집 시점 기준
- `valid`·`partial`·`invalid` 사용자 노출 영향
- 검색 대상 텍스트 필드에 원문과 정규화 값 중 무엇을 사용할지

#### Team Leader 공동 검토

Data·Backend·Frontend와 다음을 확정한다.

- `keyword`, `region`, `age`, `category`, `status` parameter
- `천안시` 검색에서 충청남도·전국 정책을 포함하는 규칙
- 27세와 `age_min`·`age_max` 비교 규칙
- 연령 조건 미상 정책의 포함과 UI 표시
- 기본 신청 가능 상태, 마감·예정 정책 표시와 정렬
- partial 기본 비노출과 opt-in 유지 여부
- pagination·기본 정렬과 결과 없음 응답
- Backend 자연어 해석 결과를 사용자가 확인·수정하는 방식
- 검색 이유와 미확인 조건의 응답·표시 방식

#### 계약 문서

결정이 현재 계약을 변경하면 같은 Slice에서 다음을 갱신하도록 담당을
배정한다.

- Data: 정규화 규칙·Source Profile
- Backend: Policy API와 DB·index 계약
- Frontend: TypeScript query·화면 소비 기준
- Integration: golden query와 전체 인수 기준

### 병렬 가능 작업

- Data: 승인 전에도 pagination 종료 탐지와 안전한 호출 제어 구현 가능
- Backend: 계약 독립적인 테스트 fixture와 query builder 골격 가능
- Frontend: 해석 조건·검색 이유 UI component 가능

### Gate G1 승인 조건

- 실제 Data 표본이 각 검색 결정의 근거로 연결됨
- Backend API와 Frontend query 이름·의미가 일치함
- Schema, `null`, 빈 배열과 enum 변경 여부가 확인됨
- 미확정 항목이 본 구현 또는 Release 1을 막는지 분류됨
- Data·Backend·Frontend 담당자가 소비 관점에서 확인함

### 후속 해제

G1 승인 후 다음 본 구현을 병렬로 시작한다.

- DT3 릴리스 데이터 수집·bootstrap
- Backend `W3-B1`~`W3-B3` 서버 검색
- Frontend `W3-F1`~`W3-F2A` 자연어 전달·해석 결과·Mock 검색 UI

## Slice DT3 - 릴리스 데이터 수집과 PostgreSQL bootstrap

### 목적

승인된 릴리스 범위의 실제 정책 snapshot을 반복 실행 가능한 절차로 수집하고
PostgreSQL에 적재한다.

### 선행 조건

- DT1 릴리스 범위와 호출 예산 승인
- pagination 종료, 중단·재시도와 API 이용 조건 확인
- Migration 적용 PostgreSQL과 Runtime Raw root 준비

G1 전체 검색 계약이 아직 승인되지 않아도 Source pagination·Raw 저장
구현은 진행할 수 있다. 다만 지역·연령 정규화 규칙 변경은 G1 없이 확정하지
않는다.

### 수행 작업

#### 수집

- Source별 page 순회와 안전한 종료 조건을 구현·검증한다.
- timeout, 요청 간격, 재시도와 429·할당량 오류 처리를 유지한다.
- 중간 실패 시 이미 저장된 Raw의 일관성과 재실행 방식을 확인한다.
- 호출 수, page, Raw와 실패 수를 비밀 없이 요약한다.

#### 재처리와 적재

- 최신 회차 경계와 list item·detail 결합을 확인한다.
- Normalizer·Validator로 valid·partial·invalid를 분리한다.
- valid·partial accepted batch를 transaction으로 upsert한다.
- invalid는 DB write 전에 분리하고 오류 경로를 기록한다.
- 같은 snapshot을 재실행해 inserted·updated·unchanged와 중복 row 부재를
  확인한다.

#### bootstrap 절차

- Migration → 수집 → Runtime 재처리 → DB 확인 순서를 문서화한다.
- dry-run과 실제 import를 구분한다.
- 새 DB에서 실제 snapshot을 만들 때 필요한 환경변수와 명령을 정리한다.
- 검색 요청이 이 절차를 호출하거나 외부 API에 접근하지 않음을 확인한다.

### 병렬 진행되는 다른 담당 작업

- Backend: 승인된 검색 Repository·Service·API 구현
- Frontend: 자연어 전달, Backend 해석 조건·검색 이유 UI와 Mock 소비 테스트
- QA: 대표 검색·경계 데이터와 smoke 준비
- 보고서: 수집 범위·건수·품질 근거 누적

### 완료 기준

- 승인된 릴리스 범위를 한 페이지 누락 없이 순회할 수 있음
- 실제 Raw → Normalized → PostgreSQL 적재 성공
- 재실행 결과와 transaction·중복 방지 검증
- Source별 품질·실패·적재 집계 제공
- 비밀키, Runtime Raw와 DB 파일 Git 비추적 확인

### 후속 해제

- DT4 실제 데이터 품질·검색 후보 인계
- Backend `W3-B3`의 실제 분포 기반 query plan·index 검토
- 실제 DB 기반 golden query 기대 정책 확정

## Slice DT4 - 실제 데이터 품질 판정과 담당자 인계

### 목적

DB에 적재된 snapshot이 사용자 검색에 사용할 수 있는지 판정하고 Backend와
Frontend가 실제 데이터로 통합할 수 있게 안전한 근거를 제공한다.

### 선행 조건

- DT3 실제 snapshot 적재
- DT2 검색 계약 승인

### 수행 작업

#### Data 품질 판정

- Source별 DB row, valid·partial·invalid와 누락 비율을 Raw 집계와 대조한다.
- 지역 코드·전국·충청남도·천안시 정규화를 표본 검증한다.
- 연령·신청 기간·상태와 월세·주거 검색 텍스트를 검증한다.
- 중복·수정·external ID와 provenance를 확인한다.
- 일반 사용자 기본 노출 가능한 실제 정책 수를 집계한다.

#### golden query 후보

- 천안 또는 적용 가능한 충청남도·전국 정책을 확인한다.
- 27세 조건과 주거·월세 의미가 실제 원문·정규화 값에 있는지 확인한다.
- 신청 가능 상태인 실제 후보의 `source_id`, `external_id`, 제목과 근거를
  기록한다.
- 맞는 정책이 없으면 결과를 만들지 않고 Source 추가 또는 릴리스 범위 결정
  항목으로 올린다.

#### Team Leader 인계

Backend 담당에게 다음을 제공한다.

- 실제 row 수와 검색 필드 분포
- 지역·연령·상태 경계 사례
- query plan·index 검토에 필요한 예상 cardinality
- golden query 후보와 실패 사례

Frontend 담당에게 다음을 제공한다.

- 사용자에게 표시할 실제 nullable·partial 사례
- 지역·연령·신청 상태 fallback 사례
- 결과 없음과 데이터 범위 설명에 필요한 사실

Raw payload와 비밀정보는 인계하지 않는다.

### 완료 기준

- 실제 snapshot이 검색 통합에 사용 가능한지 설명할 수 있음
- Backend·Frontend가 사용할 안전한 실제 사례와 경계값이 준비됨
- golden query 후보 존재 또는 Source 범위 결정 필요가 명확함

### 후속 해제와 대기

- Backend `W3-B2`가 검색 endpoint를 완료하면 DT5 HTTP 통합을 시작할 수 있다.
- Frontend `W3-F2A`가 Mock 회귀를 완료해도 Backend endpoint 전에는 실제 API
  Browser 통합을 시작하지 않는다.
- 기다리는 동안 Data 오류 수정, 품질 재검증과 보고서 근거 정리를 진행한다.

## Slice DT5 - Integration Gate G2·G3 주관

### 목적

Data·Backend·Frontend의 영역별 결과를 실제 snapshot으로 연결하고 결함을
올바른 담당자에게 분류한다.

### 선행 조건

- Data DT3·DT4 완료
- Backend `W3-B2` 검색 API와 자동 테스트 완료
- Frontend `W3-F2A` Mock 소비 테스트와 실제 API Client 준비

세 조건 중 하나라도 없으면 전체 E2E를 완료로 기록하지 않는다.

### 수행 작업

#### Gate G2 확인

- Data: 실제 적재·재실행·품질 근거
- Backend: 승인 계약 자동 테스트와 실제 PostgreSQL 검색
- Frontend: Mock 계약, loading·empty·error와 실제 연결 준비
- 공통: API·Schema·DB·Frontend 타입과 문서 일치

#### 실제 통합

1. 최신 Migration 적용
2. 승인 snapshot 적재
3. Backend 실제 DB 검색 HTTP 검증
4. Frontend 실제 API 모드 연결
5. 홈 → 검색 → 결과 → 상세 Browser 검증
6. pagination, 빈 결과, partial과 오류 상태 검증
7. Browser console과 서버 로그 확인

#### 결함 분류

- 정규화·품질·Source 문제: Data
- query·상태 코드·성능·DB 문제: Backend
- 조건 전달·표시·상태·접근성 문제: Frontend
- 계약·순서·배포 환경 문제: Team Leader - Integration

다른 담당자의 영역을 임의 수정하지 않고 결함 근거와 완료 조건을 전달한다.
실제 영역 간 차단이 생기면 `docs/index.md` 인계 보드에 등록한다.

### Gate G3 완료 기준

- 검색 HTTP 요청 중 외부 API 호출 없음
- 실제 정책 snapshot을 PostgreSQL에서 조회
- Backend pagination·filter·오류 계약 통과
- Frontend 실제 목록·상세·상태와 Browser console 정상
- 릴리스 차단 통합 결함이 수정·재검증됨

### 후속 해제

G3 통과 후 DT6 golden query·Release 1 최종 판정을 시작한다.

## Slice DT6 - golden query와 `v0.1.0` 판정

### 목적

사용자 기대 시나리오와 모든 독립 증거를 확인해 `v0.1.0` 후보 여부를
결정한다.

### 선행 조건

- Gate G3 통과
- Data·Backend·Frontend 전체 검증 결과
- QA smoke 결과와 수정본 재검증
- 사용성 리뷰어 사전 확인
- 보고서 담당의 Release 1 근거

### golden query

```text
천안 사는 27살 청년 월세 지원 받을 수 있나?
```

### Data 담당 확인

- 기대 정책이 실제 Source와 snapshot에 존재함
- 천안·상위 지역·전국 적용 근거가 실제 데이터와 일치함
- 27세와 정책 연령 조건이 일치함
- 주거·월세 의미가 실제 검색 대상 필드에 존재함
- 신청 가능 상태와 수집 시각이 설명 가능함

### Team Leader 확인

- 자연어가 Backend에서 승인 계약대로 해석되고 Frontend에 표시됨
- 기대 정책이 결과에 포함되고 상세·출처를 확인할 수 있음
- 맞는 정책이 없을 때 결과를 생성하지 않고 이유를 설명함
- 지역·연령·상태 변형과 빈 결과·오류 smoke가 통과함
- Data·Backend·Frontend 문서와 실제 코드·실행 결과가 일치함
- 보안키, Runtime Raw, DB와 임시 산출물이 Git에 포함되지 않음

### 역할 겸임 안전장치

Data 담당과 Team Leader가 같은 사람이므로 다음 증거 없이 자신의 Data 결과만
보고 Gate G4를 통과시키지 않는다.

- Backend 담당의 검색 테스트와 실제 DB 조회 결과
- Frontend 담당의 실제 API·Browser 결과
- QA의 독립 smoke와 차단 결함 재검증
- 사용성 리뷰어의 조건·결과 이해도 확인
- 보고서 담당의 실행 증거 대조

### 판정

- `pass`: 모든 Release 1 필수 조건과 검증 증거 충족
- `conditional`: 낮은 위험 제약만 남고 릴리스 문서에 범위가 명확함
- `blocked`: golden query, 실데이터, 계약, 보안 또는 필수 테스트 실패

`conditional`은 필수 조건 실패를 허용하는 상태가 아니다. 실제 정책 부재,
실데이터 적재 실패, 검색 계약 불일치와 필수 Browser 실패는 `blocked`다.

### 완료 기준

- Gate G4 판정과 근거가 Integration 개발 기록에 남음
- `pass` 또는 허용 가능한 `conditional`인 `develop`만 릴리스 PR 후보
- 미해결 위험, 범위 제약과 후속 작업이 Release 문서에 기록됨

## 다른 담당자 의존성 요약

| 내가 수행할 작업 | 기다려야 하는 다른 담당 결과 | 기다리는 동안 가능한 내 작업 |
| --- | --- | --- |
| DT2 검색 계약 승인 | Backend `W3-B0` API 초안, Frontend `W3-F0` query·UI 초안 | DT3 pagination·호출 제어 준비 |
| Backend 실제 분포·index 인계 | Backend 담당이 소비할 query 설계 질문 | Data 분포·cardinality와 경계 사례 정리 |
| DT5 실제 검색 HTTP | Backend `W3-B2` endpoint·테스트 | Data 품질 수정·재적재·문서화 |
| DT5 Frontend Browser | Frontend `W3-F2` 실제 API 연결 | Backend HTTP 결과와 golden 후보 검증 |
| DT6 Release 판정 | BE·FE 전체 테스트, QA, 리뷰어, 보고서 근거 | Data 최종 품질·보안·Git 경계 점검 |

## 내가 먼저 제공해야 하는 산출물

Backend·Frontend가 기다리지 않게 다음 순서로 공유한다.

1. 대표 데이터의 지역·연령·상태·품질 분포
2. 릴리스 수집 범위와 예상 데이터 규모
3. 검색 계약 결정 질문과 Data 권고안
4. 실제 snapshot DB 준비 여부
5. 경계 사례와 golden query 후보
6. 통합 중 Data 결함 수정 결과

## 테스트와 검증

### Data 자동 테스트

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

### Runtime dry-run·적재

Source별 실제 명령과 호출 횟수는 Data 02 Forest 계획에서 확정한다. 저장된
Raw 재처리는 먼저 `--dry-run`으로 검증하고 실제 적재 결과를 별도로 기록한다.

```powershell
.\.venv\Scripts\python.exe -B scripts\import_runtime_data.py `
  --source <source-id> `
  --raw-root runtime/raw `
  --limit <approved-limit> `
  --dry-run
```

### Backend·Integration 확인

```powershell
.\.venv\Scripts\python.exe -B -m pytest backend/tests tests/integration -q
```

### Frontend 확인

```powershell
Set-Location frontend
npm test
npm run lint
npm run build
```

### 문서·Git

```powershell
python scripts/validate_docs.py
git diff --check
git status --short
```

실제 HTTP·Browser, 외부 API 호출과 PostgreSQL 결과는 실행한 시점의
개발 기록에 명령·환경·결과만 기록하고 비밀값과 Raw payload는 남기지 않는다.

## 내 완료 체크리스트

### Data

- [ ] Source preflight·호출 예산·릴리스 범위 승인
- [ ] 대표 실데이터 분포와 검색 계약 질문 공유
- [ ] Gate G1 Data 계약 공동 승인
- [ ] 실제 릴리스 snapshot 수집·정규화·PostgreSQL 적재
- [ ] 재실행 idempotency·transaction·중복 방지 검증
- [ ] 지역·연령·상태·품질과 golden query 후보 검증
- [ ] Backend·Frontend에 안전한 실제 사례 인계
- [ ] 비밀·Raw·DB Git 비추적 확인

### Team Leader

- [ ] 2주차 병합 기준과 3주차 Forest·담당 확인
- [ ] Gate G0 시작 승인
- [ ] Gate G1 검색 계약 승인
- [ ] Gate G2 세 영역 준비 증거 확인
- [ ] Gate G3 실제 DB → API → UI 통합 확인
- [ ] QA·리뷰어·보고서 근거 확인
- [ ] golden query와 변형·실패 시나리오 확인
- [ ] Gate G4 `v0.1.0` 판정과 남은 위험 기록

## 관련 문서

- [3주차 전체 상세 계획](week_03_release_1.md)
- [주차별 상세 실행 계획 안내](README.md)
- [Release와 Milestone 계획](../develop_plan/release_roadmap.md)
- [전체 Forest 로드맵](../develop_plan/forest_roadmap.md)
- [Data Pipeline 개발 기록](../development_notes/data/data_pipeline.md)
- [Policy Data Database Integration 개발 기록](../development_notes/integration/policy_data_database_integration.md)
- [Source Profile](../../data/source_profiles.md)
- [정규화 규칙](../../data/normalization_rules.md)
- [Policy API 계약](../../api/policies.md)
- [Collector 실행](../../operations/collector.md)
- [역할과 책임](../../governance/role_assignment.md)

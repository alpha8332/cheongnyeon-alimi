# 3주차 - 실데이터 정책 검색과 Release 1

## 계획 정보

- 상태: in-progress (`Gate G4 pass`, `develop` 병합 대기)
- 대상 Release: `v0.1.0`
- 실행 주차: 3주차
- 주 담당: Data, Backend, Frontend
- 통합·릴리스 담당: Team Leader
- 지원 역할: 보고서 담당, 사용성 리뷰어, QA
- 권위 범위: 3주차 실행 순서, 병렬 작업과 통합 Gate

이 문서는 Data 02, Integration 03 Policy Search Data Foundation,
Backend 06, Frontend 04와 Integration 04 Release 1 Acceptance의 상세 Forest
계획을 대신하지 않는다. 각 Forest 구현 전에는 담당 계획을 생성·승인하고
`develop_plan/README.md`와 `docs/index.md`에 색인을 추가한다.

Data와 Team Leader를 함께 수행하는 담당자의 Slice·선행 관계와 대기 중
가능한 작업은
[3주차 Data·Team Leader 실행 계획](week_03_data_team_leader.md)을 따른다.

## 목표

실제로 진행 중인 정책 데이터를 PostgreSQL에 적재하고, 사용자가 일반적인
한국어 문장이나 명시적 조건으로 검색했을 때 관련 정책 목록과 상세를 확인할
수 있는 `v0.1.0` 후보를 만든다.

사용자 검색 요청은 PostgreSQL만 조회한다. 온통청년·복지로 API 호출은 별도
수집·적재 과정에서만 수행하며 검색 요청마다 외부 API를 호출하지 않는다.

## 시작 조건

다음 조건을 확인한 뒤 3주차 구현을 시작한다.

- Backend 03과 Frontend 02를 포함한 2주차 결과가 `develop`에 병합됨
- Data 01과 Integration 02의 완료 계약·개발 기록 확인
- `NormalizedProgram` 1.0.0, Policy DB 매핑과 공개 Policy API 현재 계약 확인
- 온통청년·복지로 API 키를 로그·문서·명령 인자에 노출하지 않는 주입 방법 확인
- PostgreSQL Migration 적용 환경과 실제 데이터용 Runtime 경로 준비
- Data 02, Integration 03, Backend 06, Frontend 04, Integration 04의
  담당자와 상세 계획 확정

3주차 공통 검색 기준선은 Data 02·Integration 03과 DT2 Data 권고,
Gate G1 인수인계가 포함된 커밋이다. Backend 06과 Frontend 04는
[검색 계약 Gate G1 인수인계](week_03_search_contract_handoff.md)의 명령으로
정확한 SHA를 확인한 뒤 Forest 단위 브랜치를 시작하고 stacked 의존 관계를
기록한다.

## 현재 기준선

3주차 시작 전 확인된 사실은 다음과 같다.

- 두 Source의 제한 수집, Raw 저장, 정규화와 검증이 구현돼 있다.
- 저장된 Runtime Raw를 PostgreSQL로 재처리하는 CLI가 구현돼 있다.
- canonical Seed → PostgreSQL → Policy API → React UI 통합은 검증됐다.
- Data 02 DT3~DT4에서 Git 제외 Runtime Raw의 완료 snapshot을 재현 가능하게
  수집·재생해 실제 정책 3,159건을 Runtime DB에 적재하고 품질·검색 경계를
  Backend·Frontend에 인계했다.
- Integration 03 PSF0~PSF8에서 검색 데이터 ADR, Normalized 1.1.0 실행 계약,
  `kr-bjd-20260803` 행정구역 기준정보, PostgreSQL 저장 기반과 두 Source
  mapping·원자적 관계·projection 적재, 지역·조건 3값 판정 primitive를
  완료하고 소비 호환·성능·실데이터 재생까지 검증했다. Mock UI partial 배지
  표시 문제는 Frontend 최종 디자인·Integration 04 인계사항이다. 전체 Gate와
  Data 02 인계를 마쳤으며 기반 브랜치 병합 후 DT2 Data 준비를 재개한다.
- Integration 03 병합 뒤 DT2 actual profile과 Data 권고안·Schema 영향 판정을
  준비했고 Backend 06·Frontend 04 초안을 병합했다. DT2A 계약 보완과 DT2B
  공동 결정과 DT2C 소비 검증, DT2D 상태 동기화를 완료해 Gate G1을
  `2026-08-04`에 승인했다.
- 전체 또는 릴리스 범위 pagination과 자동 주기 적재는 구현하지 않았다.
- 공개 Policy API에는 자유 `keyword`와 `age` query가 없다.
- Frontend 검색은 최대 100건을 받은 뒤 문장 전체 포함 여부를 검사한다.
- 현재 `regions` JSONB exact match는 상위 지역·전국·미확인·제외와
  행정구역 개편을 표현하지 못하고 일부 Source 검색 key는 Raw에만 남는다.

따라서 합성 Seed 통합이나 기존 client-only 검색을 Release 1 완료 증거로
사용하지 않는다.

## 범위

### Data

- Source 검색 key를 Source 중립 summary·keywords·대상·지역 계약으로 변환
- 행정구역 기준정보와 지역 code mapping
- Source별 pagination·호출 한도·이용 조건과 릴리스 수집 범위 확정
- 실제 정책 Raw 수집, 정규화·검증과 PostgreSQL 초기 적재
- 재수집·재처리의 idempotency, 중단·실패와 upsert 검증
- 실제 데이터의 지역·연령·카테고리·신청 상태와 품질 분포 보고
- golden query 관련 실제 정책 존재 여부와 출처 확인

### Backend

- 행정구역·정책 관계, search projection, Migration과 3값 판정 primitive
- 한국어 자연어 원문을 결정적인 규칙으로 지역·연령·카테고리·핵심어로 해석
- `keyword`, `region`, `age`, `category`, `status`, pagination과 정렬 계약
- PostgreSQL 기반 서버 검색 Repository·Service·API
- 구조화된 해석 조건·관련도·검색 이유·미확인 조건 응답
- 전국·상위 지역·시군구, 연령 조건 미상과 partial 노출 의미
- 실제 데이터 기준 query plan·index 검토
- 단위·PostgreSQL·API 통합 테스트

### Frontend

- 한국어 자연어 원문을 `q`로 Backend에 전달
- Backend 해석 조건 표시와 사용자 수정
- Backend 검색 이유·미확인 조건·pagination·정렬 연결
- loading, empty, error, partial과 상세 화면 유지
- Mock 계약 테스트와 실제 API Browser 검증

### Integration·지원 역할

- 실제 DB → FastAPI → React E2E
- golden query 기대 결과와 Release 1 판정
- 검증·화면·데이터 품질 근거 정리
- 사용성 사전 확인과 검색 smoke

## 범위 밖

- 개인화 추천 점수와 추천 이유
- 즐겨찾기, 알림과 캘린더
- 관리자 인증·실행 이력·수동 실행 UI
- 자동 Scheduler와 별도 worker 플랫폼
- LLM·벡터 검색
- Production Docker·Nginx·CI/CD

범위 밖 기능이 없어도 `v0.1.0`의 실데이터 검색 완료 조건은 낮추지 않는다.

## 실행 원칙

- 실제 Source 필드를 확인하기 전에 지역·연령 검색 의미를 임의로 고정하지
  않는다.
- 전체 적재가 끝날 때까지 Backend·Frontend 준비 작업을 멈추지 않는다.
- 대표 실데이터 표본과 분포가 확인되면 공동 검색 계약을 확정하고 병렬
  구현한다.
- Backend와 Frontend는 승인된 API 계약을 사용하고 서로 다른 임시 parameter를
  만들지 않는다.
- 실제 정책이 없으면 검색 결과를 만들거나 적용 가능성을 단정하지 않는다.
- Schema, Fixture, Seed, `null`, 빈 배열 또는 enum 변경이 필요하면 현재
  주차 범위를 자동 확장하지 않고 Data·Backend·Frontend 영향을 공동 검토한다.

## 선행 관계와 Critical Path

### Critical Path

```text
W3-D0 실제 데이터 표본·분포 확인
  → W3-PF 검색 데이터 기반·Migration Gate
  → W3-G1 검색 의미·API 계약 승인
  → W3-B2 Backend 검색 API 완료
  → W3-F2 Frontend 실제 API 연결
  → W3-I1 실제 데이터 E2E
  → W3-I2 golden query·Browser 검증
  → W3-G4 v0.1.0 판정
```

이 경로가 지연되면 Data 전체 적재나 UI가 완료돼도 Release 1을 완료할
수 없다.

### 처음부터 병렬 가능한 작업

| Data | Backend | Frontend | Team Leader·지원 |
| --- | --- | --- | --- |
| Source pagination·할당량 조사 | 현재 Repository·API·자연어 해석 변경 지점 조사 | 현재 API Client·query state 소비 구조 조사 | 인수 기준·golden query·QA 항목 준비 |
| 대표 실제 표본·Source key lineage | API·Repository 계약 문서 초안 | TypeScript 타입·표시 의미 문서 초안 | ADR·Schema 소비 Gate 준비 |
| 필드·품질 분포·지역 기준정보 조사 | Backend 06 Forest·Slice 계획 | Frontend 04 Forest·Slice 계획 | 역할·브랜치·통합 환경 확인 |

### 선행 결과를 기다려야 하는 작업

| 후속 작업 | 필요한 선행 결과 |
| --- | --- |
| 지역 계층·전국 포함 규칙 확정 | Integration 03 region reference·coverage 계약 |
| 연령 조건 미상 정책 포함 규칙 | 실제 `age_min`·`age_max`·원문 누락 분포 |
| Backend 검색 의미와 index 확정 | Integration 03 판정 primitive·projection, 대표 표본과 예상 전체 건수 |
| Frontend 실제 API 연결 | Backend query·응답 계약 승인과 endpoint 준비 |
| golden query 기대 정책 고정 | 실제 DB의 진행 중 정책과 출처 확인 |
| Release 1 Browser·E2E | Data 적재, Backend 검색, Frontend 연결 완료 |

## 단계별 실행과 Gate

### Phase 0 - 시작 준비와 대표 표본

#### 병렬 작업

- `W3-T0` Team Leader: 2주차 `develop` 병합 SHA, 담당자, Forest 계획과
  Release 1 체크리스트 확인
- `W3-D0` Data: 두 Source preflight, pagination·할당량 확인, 최소 대표 표본
  수집과 필드·품질 분포 작성
- `W3-B0` Backend: 현재 Policy Repository·Service·API 분석과 query·응답
  계약·Forest 계획 문서 초안
- `W3-F0` Frontend: 현재 API Client·query state 분석과 TypeScript
  타입·표시 의미·Forest 계획 문서 초안
- `W3-R0` 보고서: 데이터 건수, 품질, 검색 결과, 테스트와 화면 증빙 양식 준비
- `W3-U0` 사용성 리뷰어: golden query와 변형 사용자 문장 준비
- `W3-Q0` QA: 정상·빈 결과·경계값·API 오류 smoke 목록 준비

#### Gate G0 - 시작 확인

- 2주차 병합 기준과 3주차 작업 브랜치 범위가 명확함
- 비밀 주입, PostgreSQL과 Runtime 경로가 준비됨
- 각 작업의 담당과 완료 증거 위치가 정해짐

### Phase 0.5 - 검색 데이터 기반

[Integration 03 계획](../develop_plan/integration/03_policy_search_data_foundation.md)의
PSF0~PSF8을 수행한다.

- Source key → 공통 검색 필드 lineage와 `summary`·keywords·대상 mapping
- `nationwide|regional|unknown`과 include·exclude 지역 불변식
- versioned 행정구역 code·parent·alias 기준정보
- Policy·지역 관계와 Korean search projection Migration
- Importer transaction·idempotency와 3값 판정 primitive
- 기존 목록·상세 DTO, Fixture·Seed와 Frontend 소비 호환

#### Gate GF - 검색 데이터 기반 승인

- Schema·`null`·빈 배열·enum과 공개 API 영향이 세 영역에서 확인됨
- 빈 DB·기존 데이터 DB Migration과 downgrade가 통과함
- 천안·충남·전국·미확인·타 지역·exclude 판정 테스트가 통과함
- 실제 DT1 Raw 재생에서 검색 key 유실과 추정값 생성이 없음
- Backend 06과 Data 02가 같은 DB·projection 계약을 소비할 수 있음

Gate GF 전에는 최종 지역 query와 실제 snapshot 적재를 완료로 처리하지
않는다.

### Phase 1 - 검색 계약 공동 확정

Data 표본을 바탕으로 Data·Backend·Frontend와 Team Leader가 다음을 결정한다.

- 검색 대상 필드와 `keyword` 결합 방식
- 지역 표준 값, 시·도/시·군·구와 전국 정책 포함 관계
- 지역 미상의 3값 판정과 사용자 미확인 조건
- `age`와 `age_min`·`age_max` 비교
- 연령 조건 미상 정책의 포함·표시 규칙
- 기본 `status`, partial 노출과 마감·예정 표시
- 기본 정렬과 pagination
- Backend 자연어 해석 결과와 구조화 조건 수정 요청 방식
- 검색 이유와 미확인 조건의 응답 구조
- 결과 없음 사유와 조건 수정 방식

#### Gate G1 - 검색 계약 승인

- 상태: approved (`2026-08-04`)
- Data 실제 표본과 분포가 근거로 연결됨
- Backend API query·응답·오류 계약이 문서화됨
- Frontend TypeScript query 타입과 UI 의미가 같은 계약을 사용함
- Schema나 enum 변경 여부와 세 영역 영향이 확인됨
- 미확정 항목은 구현을 막는지 또는 후속으로 가능한지 분류됨

G1 전에는 현재 구조 분석과 계획·계약 문서 초안만 작성한다.
Backend·Frontend 구현과 테스트 코드 작성은 G1 승인 뒤 별도 Slice에서 시작한다.

### Phase 2 - 세 영역 병렬 구현

#### Data

- `W3-D1`: Integration 03 계약을 사용한 릴리스 범위 pagination·중단·재시도 구현
- `W3-D2`: 실제 Raw 수집·정규화·검증과 PostgreSQL bootstrap
- `W3-D3`: 재실행 idempotency, 중복·수정과 품질 보고 검증

#### Backend

- `W3-B1`: 자연어 해석과 검색 request·service·repository 계약 구현
- `W3-B2`: `q` 해석, keyword·region·age·category·status·관련도·정렬·pagination,
  검색 이유·미확인 조건 API 구현
- `W3-B3`: 단위·PostgreSQL·API 테스트와 실제 분포 기반 성능·index 검토

#### Frontend

- `W3-F1`: 자연어 원문 전달, Backend 해석 조건 표시·수정과 query state 구현
- `W3-F2A`: 승인된 Mock 계약으로 pagination·상태·회귀 테스트
- `W3-F2`: Backend endpoint 준비 후 실제 API Client 연결

#### 지원

- `W3-R1`: 결정·구현·검증 근거를 역할별로 수집
- `W3-U1`: 검색 조건과 결과 이유의 이해 가능성 사전 확인
- `W3-Q1`: 구현 중 독립 smoke와 결함 재현

#### Gate G2 - 영역별 준비

- 상태: completed (`2026-08-06`)

- Data: 실제 릴리스 범위 적재와 재실행 결과를 제시할 수 있음
- Backend: 승인된 검색 계약의 자동 테스트와 실제 PostgreSQL 조회가 통과함
- Frontend: Mock 소비 테스트가 통과하고 실제 API 연결 준비가 됨
- 비밀키, Runtime Raw와 DB 파일이 Git 추적 대상에 없음

### Phase 3 - 실제 데이터 연결

- `W3-I0`: Migration 적용 DB에 실제 snapshot 적재
- `W3-I1`: 실제 DB를 대상으로 Backend 검색 HTTP 검증
- `W3-I2`: Frontend 실제 API 모드에서 검색·상세 Browser 검증
- `W3-D4`: 통합 중 발견한 정규화·품질 문제 수정
- `W3-B4`: 실제 query·응답·성능 문제 수정
- `W3-F3`: 조건 전달·표시·빈 결과·오류 UI 문제 수정

#### Gate G3 - Release 1 후보

- 상태: completed (`2026-08-06`)
- 근거: [Release 1 Acceptance 개발 기록](../development_notes/integration/release_1_acceptance.md)

- 검색 요청 중 외부 Source API 호출이 발생하지 않음
- 실제 진행 중 정책 snapshot이 PostgreSQL에 존재함
- 실제 DB → FastAPI → React 목록·상세가 동작함
- loading, empty, 404, 422, 500과 partial 상태가 검증됨
- 실제 데이터 양에서 pagination과 응답 시간이 검토됨

### Phase 4 - golden query와 릴리스 판정

필수 golden query:

```text
천안 사는 27살 청년 단기숙소 지원 받을 수 있나?
```

검증 항목:

- `천안`이 승인된 지역 규칙으로 해석됨
- `27살`이 연령 조건으로 전달됨
- `단기숙소`가 주거 검색의 구체 term으로 반영됨
- 진행 중이고 실제 적용 지역·연령에 맞는 정책이 우선됨
- 결과 카드와 상세에서 자격·신청 기간·출처를 확인할 수 있음
- 결과가 없으면 적용 정책을 생성하지 않고 조건과 데이터 범위 제약을 설명함

기대 정책은 온통청년 `20260430005400212969`의 `청년단기숙소 지원사업`이다.
자연어 결과 20위 이내·unknown 0·2초 이내와 명시 조건 control 1위·1초
이내를 모두 만족하지 않으면 릴리스 차단 결함이다.

#### Gate G4 - `v0.1.0` 판정

Team Leader가 다음 증거를 확인한다.

- Data, Backend, Frontend 담당 테스트 결과
- 실제 데이터 E2E와 Browser 검증
- QA smoke와 릴리스 차단 결함 재검증
- 사용성 리뷰어의 조건·결과 이해도 확인
- `v0.1.0` 경량 정책에 따른 QA·사용성 수동 근거와 후속 분류
- 문서 검증, 비밀·Runtime 산출물과 Git 상태

`2026-08-06` 판정은 `pass`다. 새 contract hash의 actual 자연어·control은
모두 1건 중 1위·unknown 0이고 95.95ms·78.68ms로 기술 acceptance를 통과했다.
신청기간 안전성, Frontend actual API E2E·Browser와 경량 QA·사용성 리뷰도
통과했다. evidence verifier는 `ready-for-team-leader-decision`, blocker 0건을
반환했다.

보고서 대조와 API 오류 토스트 Browser 검증은 실제 수행하지 않았으며
`v0.5.0` 후속으로 이관했다. 기본 정책 검색 MVP의 Gate 통과 근거로 안내하지
않는다.

모든 증거가 충족된 `develop`만 `main` 릴리스 PR과 `v0.1.0` tag 후보가 된다.

## 역할별 산출물

| 역할 | 필수 산출물 |
| --- | --- |
| Data | 릴리스 수집 범위, 실제 snapshot, 품질 분포, bootstrap·재실행 절차와 검증 |
| Backend | 승인된 검색 API 계약, 구현, Migration·index 필요 시 변경과 자동 테스트 |
| Frontend | 자연어 전달·Backend 해석 조건 수정 UI, 검색 이유·미확인 조건·pagination과 UI 회귀 테스트 |
| Team Leader | Gate 판정, 통합·Browser 결과와 Release 1 결정 |
| 보고서 | 실제 건수·품질·검색·화면·테스트 근거와 계획 변경 내역 |
| 사용성 리뷰어 | golden query와 변형 문장 사용성 관찰·재확인 |
| QA | 검색 정상·빈 결과·경계·실패 smoke, 결함과 수정본 재검증 |

## 테스트와 검증

Forest 구현 중 세부 테스트 명령이 달라지면 해당 계획과 개발 기록에 실제
명령을 갱신한다. 현재 저장소 기준 전체 검증 후보는 다음과 같다.

### Data

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

외부 API 호출이 없는 자동 테스트와 명시적 실제 수집을 분리한다. 실제 호출
횟수, 성공·실패와 적재 결과는 Data 개발 기록에 남긴다.

### Backend와 Integration

```powershell
.\.venv\Scripts\python.exe -B -m pytest backend/tests tests/integration -q
```

실제 PostgreSQL 통합 테스트는
[Backend Windows 로컬 환경](../backend_local_setup.md)의 테스트 DB 경계를
따른다.

### Frontend

```powershell
Set-Location frontend
npm test
npm run lint
npm run build
```

### 실제 HTTP·Browser

- 실제 snapshot 기반 검색 HTTP
- 홈 → 자연어 검색 → 결과 → 상세
- 조건 수정과 pagination
- 결과 없음, API 오류와 partial 표시
- Browser console 오류와 빈 화면

### 문서와 Git

```powershell
python scripts/validate_docs.py
git diff --check
git status --short
```

실행하지 못한 검증은 성공으로 기록하지 않고 원인과 Release 영향에 남긴다.

## 위험과 결정 필요 사항

- 온통청년 공식 호출 한도와 오류 payload가 아직 확인되지 않았다.
- 온통청년 지역 코드를 표준 이름으로 바꿀 권위 있는 versioned code table이
  필요하다.
- 기존 실제 수집 20건은 모두 partial이었으므로 사용자 기본 노출 가능한 실제
  정책 수가 부족할 수 있다.
- API 할당량에 따라 릴리스 수집 범위를 조정해야 할 수 있다.
- 실제 데이터 분포에 따라 PostgreSQL index 또는 검색 방식 변경이 필요할 수
  있다.
- golden query에 맞는 정책이 지원 Source에 없으면 Source 범위 결정이
  Release 1을 막는다.
- Backend 자연어 해석은 결정적 규칙을 기준으로 하며 LLM 정확도로 해결하지
  않는다.

## 인계사항 발생 조건

DT1에서 확인한 `R1-SEARCH-DATA-SEMANTICS`는 Integration 03과 DT2·Gate G1에서
종료했다. 후속 `R1-SEARCH-IMPLEMENTATION`을 진행하며 다음 중 추가 차단이
실제로 발생하면 요청 범위를 넘어 임의 수정하지 않고 `docs/index.md` 인계
보드에 기록한다.

- 실제 Source 필드와 Schema·DB·API 계약 충돌
- `null`, 빈 배열, enum 또는 지역·연령 규칙 변경 필요
- Data 변경이 Backend·Frontend 소비를 막음
- Backend API 계약 변경이 Frontend 구현을 막음
- 실제 정책 부재로 Source 추가 결정 필요
- 별도 Scheduler·worker·배포 구조가 선행돼야 하는 문제
- 다른 담당 Forest의 변경 없이는 해결할 수 없는 릴리스 차단 결함

## 완료 체크리스트

- [ ] 2주차 결과가 `develop`에 병합되고 3주차 Forest 계획이 승인됨
- [x] 대표 실제 표본과 데이터 분포 확인
- [x] Gate GF 검색 데이터 기반·Migration·소비 호환 승인
- [x] Gate G1 검색 계약 공동 승인
- [x] 릴리스 범위 실제 정책 snapshot PostgreSQL 적재
- [x] 재수집·재처리 idempotency와 품질 보고 검증
- [x] Backend 서버 검색과 실제 PostgreSQL 테스트
- [x] Frontend 자연어 전달·Backend 해석 결과·실제 API·pagination 연결
- [x] 실제 DB → FastAPI → React E2E
- [x] 폐기한 월세 golden query와 변형·빈 결과·실패 시나리오 기록
- [x] 신청 가능한 단기숙소 golden 기대 정책·자동 acceptance 기준 고정
- [x] 단기숙소 자연어 golden 순위·응답시간 기준 통과
- [x] Browser·console 확인
- [x] 관련 단위·통합·Frontend 테스트 통과
- [x] 문서 검증과 `git diff --check` 통과
- [x] 비밀키·Runtime Raw·DB 파일 Git 비추적 확인
- [x] 경량 QA·사용성 리뷰 근거 확인, 보고서·API 오류 UX는 `v0.5.0` 이관
- [x] Team Leader의 Gate G4 Release 1 `pass` 판정

## 관련 문서

- [주차별 상세 실행 계획 안내](README.md)
- [Data·Team Leader 실행 계획](week_03_data_team_leader.md)
- [검색 계약 Gate G1 인수인계](week_03_search_contract_handoff.md)
- [주차별 실행 계획 요약](../develop_plan/weekly_delivery_plan.md)
- [Release와 Milestone 계획](../develop_plan/release_roadmap.md)
- [전체 Forest 로드맵](../develop_plan/forest_roadmap.md)
- [Policy Data Database Integration](../develop_plan/integration/02_policy_data_database_integration.md)
- [Policy Search Data Foundation](../develop_plan/integration/03_policy_search_data_foundation.md)
- [Policy API 계약](../../api/policies.md)
- [Policy DB 매핑](../../architecture/policy_database_mapping.md)
- [Fixture와 Seed 계약](../../data/fixture_seed_contract.md)
- [Collector 실행](../../operations/collector.md)
- [역할과 책임](../../governance/role_assignment.md)


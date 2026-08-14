# 4주차 Data·Team Leader 실행 계획

## 계획 정보

- 상태: in progress (`DTL4-1`·`W4-G0` 완료, 후속 Forest 착수 가능)
- 대상 주차: 4주차
- 대상 Release: `v0.5.0`
- 수행 역할: Data 담당, Team Leader - Integration
- 연계 담당: Backend, Frontend
- 후속 역할: 보고서 담당, 사용성 리뷰어, QA는 5주차 추가 기능·오류 수정·
  UI/UX 최적화와 담당자 자체 검증 종료 뒤 수행
- 현재 Slice: Data 05 `RYP0`~`RYP8`·`RYP-G4` 완료,
  `RYP9` 감사 재판정·accepted 103건 부분 적재와 명시적 지역 검색 match-only 완료,
  충북 open 0건 확정·review 1,151건 Source별 보강 진행 (legacy null 0·RYP8 감사 통과,
  `DTL4-4B`·`ES4` actual 세로 인수 포함),
  이후 RYP9·Data 06 구현과 `DTL4-5` 소비 대조 예정
- 상위 계획: [4주차 전체 상세 계획](week_04_v0_5_0.md)
- 공통 Release 기준점: `2b33ed7` (`v0.1.0`)

이 문서는 Data 담당과 Team Leader를 같은 사람이 수행하는 현재 역할 배정을
기준으로 한다. Data 03·04·05와 Integration 08의 Data 결과를 직접 만들면서
Integration 05·07·09의 계약과 실제 연결을 조정한다. 자신의 Data 구현과
테스트만으로 Backend·Frontend 완료, 공동 Gate 또는 Release 2 통과를 승인하지
않는다.

## 담당 목표

1. W4-G0에서 웹 Source·자격요건·추천·사용자 기능·관리자 PIN·데이터·로그와
   품질 계약을 Data·Backend·Frontend 공동 기준으로 동결한다.
2. 반복 수집에서 unchanged·updated·duplicate·failed와 partial·invalid를
   재현 가능하게 구분한다.
3. 승인된 공식 HTTPS Source 한 곳의 세로 기준선, 광역자치단체 지역 고유
   정책과 온통청년·복지로 누락 중앙·공공기관 Source를 기존 파이프라인과
   PostgreSQL에 실제 연결한다.
4. API·웹 원문의 신청 조건을 근거 있는 구조로 만들고 Backend 상세 API와
   Frontend `핵심 신청 조건` UI에 인계한다.
5. 관리자 데이터 화면의 읽기 projection과 파일 로그·correlation·삭제 감사
   계약이 Data·보안 의미를 훼손하지 않는지 검토한다.
6. 관리자, 웹 Source·자격요건, 추천·사용자 세 actual E2E를 주관하고 Release 1
   회귀를 확인한다.
7. 설계한 기본 기능이 모두 구현·검증된 경우에만 W4-G4 midpoint를 통과시킨다.

## 담당 Forest와 브랜치 경계

| Forest | 내 역할 | 권장 브랜치 | 이번 주 완료 기준 |
| --- | --- | --- | --- |
| Integration 05 Contract Baseline | Team Leader 주관, Data 근거 제공 | `docs/docs/v0-5-contract-baseline` | `W4-G0_APPROVED` |
| Data 03 Recurrent Quality Operations | Data 구현 | `feature/data/recurrent-quality-operations` | 반복·수정·중복·실패·품질 통계 검증 |
| Data 04 Public HTTPS Ingestion | Data 구현 | `feature/data/public-web-policy-source` | 공식 Source 1곳 actual 수집·DB 적재 |
| Data 05 Regional Youth Policy Ingestion | Data 구현 | `feature/data/regional-youth-policy-ingestion` | 지역 고유 정책 수집·온통청년/복지로 중복 제외·actual 적재 |
| Data 06 Supplemental Official Policy Ingestion | Data 계획·후속 구현 | Data 05 공통 Gate 뒤 Forest 브랜치 한 개 | 중앙·공공기관 후보 정제·중복 감사·actual 적재 |
| Integration 08 Eligibility Summary | Data 구현·공동 소비 검토 | `feature/schema/eligibility-evidence-contract` 단일 Integration 브랜치 | evidence 구조 → 상세 API → UI E2E |
| Integration 09 Admin Data and Log Console | Data 의미 검토, Team Leader 보안·E2E | Backend·Frontend observability 브랜치 | 읽기 전용 DB 표와 로그 조회·삭제 감사 E2E |
| Integration 07 Release 2 Acceptance | Team Leader midpoint 주관 | cross-area domain 합의 전 생성 금지 | W4-G1~G4 근거와 5주차 시작 조건 |

Slice마다 새 브랜치를 만들지 않는다. Data 03, Data 04, Data 05와 Data 06은 독립 목표와
완료 기준이 있으므로 Forest별 브랜치를 사용한다. Data 05에서도 지역별
브랜치를 만들지 않고 Source별 Conventional Commit으로 검토 지점을 나눈다.
Integration 08은 승인된
한 브랜치에서 Data·Backend·Frontend 변경을 Conventional Commit 경계로
구분하고 Slice별 추가 브랜치를 만들지 않는다.

## 전체 실행 순서

```text
DTL4-0 시작 기준·환경·담당·브랜치 확인
  ↓
DTL4-1 Data inventory·소비 초안 → W4-G0 계약 승인
  ├────────────────┬────────────────┬────────────────┐
  ↓                ↓                ↓                ↓
DTL4-2A 품질 기반 DTL4-3A 웹 기반  DTL4-4A 조건 기반  BE·FE 승인 Mock·기반
  └────────────────┴────────────────┴────────────────┘
                            ↓
DTL4-5 계약 소비 대조·관리자 데이터·로그 검토 → W4-G1
  ├────────────────┬────────────────┬────────────────┐
  ↓                ↓                ↓                ↓
DTL4-2B 품질 actual DTL4-3B 웹 actual DTL4-4B 조건 actual BE·FE actual 구현
  └────────────────┴────────────────┴────────────────┘
                            ↓
DTL4-6 영역별 actual·단위·통합 준비 판정 → W4-G2
                            ↓
DTL4-7 세 actual E2E·Release 1 회귀·결함 조정 → W4-G3
                            ↓
DTL4-8 전체 회귀·문서 대조·midpoint 판정 → W4-G4
```

DTL4-2A·3A·4A는 W4-G0 뒤 병렬 진행하고 W4-G1에서 소비 계약을 확인한다.
W4-G1 뒤 DTL4-2B·3B·4B actual 구현과 Backend·Frontend actual 연결을 병렬로
수행한다. 같은 Schema, Migration, Policy model이나 Source Adapter를 동시에
수정해야 하면 Team Leader가 소유 브랜치와 병합 순서를 먼저 지정한다.

DTL4-4B와 ES4가 완료된 현재 Data 05 RYP0~RYP5를 완료했다. 17개 홈의 Browser·
공개 HTTP 재검증 결과 13개 승인·3개 차단·1개 제외를 확정했고, 공통 profile·
discovery·Browser runner 경계와 경북 JSON·modal Adapter의 offline replay를
검증했다. RYP3에서 지역 evidence·신청 상태 Gate와 경북 closed 격리를 추가했다.
RYP4 교차 Source Gate와 RYP5 대표 actual DB·API·Browser 인수를 완료했다.
RYP0~RYP4는 DTL4-6 W4-G2, 완료한 RYP5 actual은 DTL4-7 W4-G3, RYP6
지역별 최종 상태와 회귀는 DTL4-8 W4-G4의 필수 입력이다. Data 06 SOP0~SOP3,
SOP4 actual과 SOP5 최종 상태도 각각 같은 W4-G2~G4의 필수 입력으로 둔다.

`2026-08-13`에 RYP6는 13개 승인 Source 4,606건 전체 판정, accepted 18건
PostgreSQL 동기화, 동일 Raw unchanged, Release 1 golden 기술 회귀를 완료해
수집 인프라 Gate `RYP-G4`를 통과했다. 그러나 DB 검색 데이터가 부산·경북에만
존재하므로 Forest는 다시 `in-progress`로 두고, RYP7~RYP9에서 review 사유 감사·
Source별 필드 추출·지역 검색 actual을 마친 뒤 완료 판정한다. Data 06·DTL4-5·
주차 전체 `W4-G4`도 완료로 소급하지 않는다.

같은 날 RYP7은 review 1,903건을 지역 근거 1,875건·신청 상태 1,419건·청년
미확인 725건으로 중복 사유 감사하고 Source-scope·필드 관찰 계약을 고정해
완료했다. legacy null이 남은 12개 Source의 실제 라벨·값 보강은 RYP8, 전체
accepted 재판정과 지역 검색 actual은 RYP9에서 수행한다.

같은 날 RYP8 부산 목록·상세 locator와 field observation을 추가해 legacy capture
gap Source를 12개에서 11개로 줄였다. checkpoint와 accepted DB는 유지하며 나머지
11개 Source 보강 전에는 RYP8을 완료로 판정하지 않는다.

## 권장 5일 배치

| 일차 | Data 담당 | Team Leader 담당 | 당일 Gate |
| --- | --- | --- | --- |
| 1일차 | 현재 Source·field coverage·품질 inventory, 웹 Source 후보 preflight | 역할·브랜치·OpenAPI·TypeScript 초안 대조, PIN·로그·저장·날짜 계약 동결 | W4-G0 |
| 2일차 | Data 03 fixture, Data 04 Adapter, 자격 mapping, Data 05 inventory·Source 승인 | Backend·Frontend Mock 소비 대조, 병합 충돌·계약 변경 관리 | W4-G1 |
| 3일차 | Data 05 Adapter·지역·중복 제외, Data 06 후보 정제·중복 감사 | 관리자 데이터·로그와 자격요건·추천 actual API 소비 확인 | W4-G2 |
| 4일차 | Data 05 대표 지역·Data 06 우선 Source DB·API·Browser | 관리자·웹 Source·사용자 세 E2E, 최초 실패·수정·재검증 기록 | W4-G3 |
| 5일차 | Data 03~06 전체 회귀·Source별 최종 상태·문서 | 전 담당 회귀·문서·비밀 경계 대조와 W4-G4 판정 | W4-G4 |

기본 기능이 밀리면 5주차 범위로 바꾸지 않는다. 완료하지 못한 기능과 원인을
기록하고 W4-G4를 `BLOCKED`로 판정한다.

## Slice DTL4-0 - 시작 기준과 실행 경계 확정

### 목적

Release 1 publication과 실제 로컬 환경을 확인하고 4주차 Forest·브랜치·기록
위치를 정한다.

### 선행 조건

- `main`, `develop`, `origin/main`, `origin/develop`과 `v0.1.0` 확인
- 현재 브랜치와 작업 트리의 기존 사용자 변경 확인
- `docs/index.md`, governance 문서와 4주차 전체·Forest 계획 확인
- PostgreSQL `5432`, 저장소 Python 환경, Node와 `run.bat` 확인

### Data 수행 작업

- Data 02 실제 snapshot과 Runtime Raw·PostgreSQL 기준선이 재사용 가능한지
  확인한다.
- API key 파일과 pgpass는 존재 여부·권한만 확인하고 값을 출력하지 않는다.
- Data 03·04의 단위·PostgreSQL·actual Source 검증 명령과 전용 test DB를
  구분한다.
- `runtime/raw`, 향후 Runtime HTML·logs와 DB 파일이 Git 제외인지 확인한다.
- Python 명령이 실패하면 `.venv`, `uv`와 저장소 설정을 먼저 확인하고 새
  Python이나 package를 임의 설치하지 않는다.

### Team Leader 수행 작업

- 각 Forest의 주 담당, 소비 검토자, 시작·merge target과 완료 기준을 확인한다.
- Backend에 관리자 PIN·CollectionRun·데이터·로그·자격요건·추천 API 초안을,
  Frontend에 PIN·관리자·핵심 조건·추천·로컬 기능 type·Mock 초안을 요청한다.
- Data 03·04·05와 Integration 08의 겹치는 Schema·Migration·Adapter 변경 소유자를
  정한다.
- 구현을 시작하는 Forest에는 대응 `development_notes/` 문서를 만들도록
  담당을 배정하되 계획만 있는 Forest의 결과를 미리 작성하지 않는다.

### 완료 기준

- 실제 시작 SHA, 작업 트리와 Forest별 branch·merge target이 기록됨
- PostgreSQL·Python·Node·Browser·비밀 주입의 실행 가능 여부가 확인됨
- 계약 초안·구현·소비·actual E2E의 담당자가 확정됨
- 사용자 변경, Runtime 자료와 비밀을 덮어쓰거나 Git에 포함하지 않음

### 후속 해제

DTL4-0 완료 후 DTL4-1 inventory와 W4-G0 공동 검토를 시작한다.

## Slice DTL4-1 - Data inventory와 W4-G0 계약 Gate

### 목적

현재 코드·Schema·실데이터 근거와 Backend·Frontend 소비 초안을 하나의 구현
가능한 계약으로 동결한다.

### Data inventory

#### 반복 수집·품질

- importer·upsert·CollectionRun의 현재 inserted·updated·unchanged·failed 의미
- 비교 필드에서 `collected_at` 같은 실행 metadata를 제외하는 기준
- duplicate·partial·invalid와 fetch·extract·normalize·validate·persist 실패
- 관리자에게 노출 가능한 집계와 노출하면 안 되는 Raw·예외·credential

#### 공식 웹 Source

- 후보 사이트의 공식성, 공개 목록·상세, 안정적인 identity와 보강 필드
- robots·이용약관·라이선스, 허용 경로·요청 빈도·보존 범위
- 정적 HTML·허용된 공개 내부 API 우선순위와 동적 렌더링 필요 여부
- API와 웹의 동일 정책 후보, 충돌·최신성·source-scoped identity 경계

대상은 `cheonan-youthcenter-web`, 승인 표본은 `notice:674`다. Data 04 착수
시점에 DOM·이용 조건·robots를 다시 확인하고 승인 요청 예산을 넘기지 않는다.

#### 자격요건 evidence

- 기존 snapshot의 소득·추가 자격·참여 제외·필요 서류 field coverage
- `eligibility_text` 호환과 requirements·exclusions·preferences·documents·
  unknown 구조 후보
- category, 원문 수치·단위, source ID·URL·수집 시각·field 또는 selector
- API·웹 원문 충돌과 complete·partial·unknown 대표 사례

### Team Leader 공동 결정

| 계약 | Data 근거 | Backend 초안 | Frontend 초안 | 승인 핵심 |
| --- | --- | --- | --- | --- |
| 일반 사용자 저장 | 개인정보 최소화 | 서버 계정 없음 | versioned localStorage | migration·전체 삭제 |
| 추천 | 검색 primitive·조건 coverage | 점수·이유·미확정 DTO | 이유 우선 UI | 자격 확률 아님 |
| 핵심 신청 조건 | API·웹 evidence | 상세 DTO | 필수·제외·서류·확인 UI | 최종 자격 비단정 |
| 날짜 | 신청기간 source 근거 | KST·null 의미 | D-Day·알림·`.ics` | 상시·미상 계산 금지 |
| 관리자 인증 | 비밀·로그 경계 | 4자리 PIN·token·rate limit | PIN 한 칸·만료·로그아웃 | `0000`은 local dev만 |
| 관리자 데이터 | Policy·품질 field 의미 | 읽기 projection·allowlist | CSV형 표·row 상세 | arbitrary SQL 금지 |
| 파일 로그 | 수집 단계·run ID | JSONL·rotation·redaction | filter·detail·정리 | archive 삭제·감사 |
| 수동 실행 | Source·run·중복 의미 | `202`·run ID·stale | 확인·polling | Source별 활성 1개 |

### W4-G0 승인 조건

- 대표 공식 HTTPS Source 한 곳과 수집 허용 경계가 정해짐
- 자격요건 Schema·provenance·partial·unknown과 기존 호환이 정해짐
- Backend OpenAPI와 Frontend TypeScript·Mock이 같은 `null`·빈 배열·enum을
  사용함
- 4자리 PIN, local 최초 `0000`, 배포 hash·secret·rate limit이 정해짐
- 관리자 Policy projection과 로그 rotation·retention·삭제 감사가 정해짐
- 추천·즐겨찾기·D-Day·알림·`.ics`의 4주차 필수 완료가 재확인됨
- 미확정 항목에 담당·차단 여부·재개 조건이 기록됨
- 세 담당자가 자신의 소비 관점에서 확인함

### 산출물

- Integration 05 결정표와 `W4-G0_APPROVED` 또는 차단 기록
- Data coverage·Source preflight·대표 fixture 후보
- Backend OpenAPI·Frontend TypeScript 소비 검토 결과
- Schema·Migration·API·운영·환경설정 문서 갱신 담당표

### 후속 해제

W4-G0 승인 후 DTL4-2·3·4와 Backend·Frontend 본 구현을 병렬 시작한다.

## Slice DTL4-2 - Data 03 반복 수집과 품질 운영

### 목적

같은 데이터, 수정 데이터, 중복과 단계별 실패를 반복 실행해 품질 통계와 DB
결과를 결정적으로 만든다.

### 수행 작업

#### DTL4-2A - Fixture와 판정 기준

- 동일 snapshot, 단일 field 수정, 실행 내·실행 간 duplicate와 실패 fixture
- inserted·updated·unchanged·rejected·failed 기대 집계
- `collected_at`, run ID와 저장 시각을 business 비교에서 제외
- 같은 `(source_id, external_id)`의 중복 row 방지
- cross-source 동일 정책은 자동 병합하지 않고 후보로만 분류

#### DTL4-2A - 실패 격리 기반

- fetch·extract·normalize·validate·persist 단계별 안전한 오류 분류
- 실패 자료가 정상 정책 transaction과 통계를 오염시키지 않는지 검증
- partial·invalid·실행 실패와 stale를 서로 다른 상태로 유지
- Raw payload·stack trace·credential 없이 관리자 DTO가 소비할 집계 제공

#### DTL4-2B - 실제 PostgreSQL 구현·검증

- 동일 snapshot 재실행에서 거짓 updated와 중복 row가 없는지 확인
- 수정 fixture가 정확히 updated로 분류되는지 확인
- 실패·rollback 뒤 정상 재실행과 기존 데이터 유지 확인
- Backend 05·Integration 09 통계·로그 correlation 소비를 대조

### 병렬 작업

- Backend: CollectionRun 목록·상세·수동 실행과 품질 DTO
- Frontend: 승인 Mock 기반 실행 이력·상태·오류 화면
- Data: DTL4-3 Source Adapter와 DTL4-4 자격요건 mapping

### 완료 기준

- 동일·수정·중복·실패가 기대 집계와 DB 결과를 만듦
- 정상 정책과 실패 자료가 transaction·조회에서 격리됨
- 관리자 집계에 Raw·credential·내부 stack이 노출되지 않음
- Data 단위 테스트와 전용 PostgreSQL 통합 테스트 통과
- Data 03 개발 기록과 품질·CollectionRun 기준 문서가 실제 결과와 일치

## Slice DTL4-3 - Data 04 공식 HTTPS Source 수집

### 목적

공공 API를 보강할 공식 HTTPS Source 한 곳을 기존 Raw → Extract → Normalize →
Validate → PostgreSQL 경로에 실제 연결한다.

### 수행 작업

#### DTL4-3A - Source 승인과 호출 안전

- W4-G0 승인 Source의 현재 robots·약관·라이선스를 다시 확인한다.
- 목록·상세 canonical URL, Source ID와 external identity를 확정한다.
- 공개 목록과 필요한 상세만 제한 호출하고 delay·timeout·retry·429를 적용한다.
- 정적 HTML 또는 허용된 공개 요청을 우선하며 로그인·CAPTCHA를 우회하지 않는다.

#### DTL4-3A - Fixture·Adapter·Extractor 기반

- 정상 목록·상세, 선택 field 누락과 selector drift를 대표하는 축소 HTML fixture
- 실제 운영 HTML·개인정보·재배포 제한 자료의 Git 비포함
- fetch와 list/detail Extractor 분리, selector·mapping의 Source module 집중
- `RawPolicyDocument(raw_format=html)`과 content hash·source URL·수집 시각 보존
- DOM 구조 변경을 정상 빈 값으로 숨기지 않고 drift 실패로 분류

#### DTL4-3B - 정규화·적재·actual 재실행

- 정책명·기관·기간·지원 내용·신청 조건·제외·서류와 provenance 추출
- 필드 누락은 합의된 `null`·빈 배열·unknown으로 유지
- Source 근거 없는 값 보정과 API·웹 충돌 자동 덮어쓰기 금지
- 실제 제한 수집 → 정규화 → 전용 PostgreSQL 적재
- 동일 페이지 재실행의 unchanged, 변경 page의 updated와 실패 격리 확인

### 산출물

- Source profile·수집 정책·mapping과 검토된 HTML fixture
- Collector·Extractor·Normalizer·Validator와 테스트
- actual Raw manifest·CollectionRun·DB 결과의 비밀 없는 요약
- Data 04 개발 기록과 Backend·Frontend 소비 인계

### 완료 기준

- 공식 Source 한 곳의 실제 목록·상세가 PostgreSQL까지 적재됨
- robots·약관·라이선스와 호출 범위 근거가 기록됨
- idempotency·변경·누락·drift·HTTP 실패 테스트 통과
- Runtime HTML·비밀·DB 파일이 Git에 포함되지 않음
- actual 수집을 실행하지 않았다면 Forest와 W4-G2를 통과시키지 않음

## Slice DTL4-4 - Integration 08 자격요건 근거 Data 구현

### 목적

기존 API와 새 웹 Source의 긴 신청 조건을 근거가 보존되는 구조로 제공하고
Backend·Frontend가 같은 의미를 소비하게 한다.

### 수행 작업

#### DTL4-4A - Coverage와 대표 사례

- 소득·자산·거주·연령·취업·학력·주거·가구·기타 조건 coverage
- 필수·제외·우대·필요 서류·자동 비교 불가능 원문 분류
- complete·partial·unknown과 API·웹 충돌 사례
- 실제 정상·경계·긴 문장·누락 사례를 비밀 없는 fixture로 고정

#### DTL4-4A - Schema·mapping·provenance 기반

- W4-G0 승인 구조를 Data Schema·JSON Schema와 Extracted/Normalized model에 반영
- 기존 `eligibility_text`를 호환 원문으로 유지할지 version migration 적용
- 각 항목에 category·원문·source ID·URL·수집 시각·field/selector evidence 보존
- 수치·단위를 추정·반올림하지 않고 계산 불가능 조건은 unknown으로 유지
- API와 웹 충돌 시 임의 최신 우선 덮어쓰기를 하지 않음

완료 결과(`2026-08-10`): Eligibility Summary `1.0.0` 독립 JSON Schema·Python
모델과 정상·경계·긴 문장·누락·충돌 fixture를 고정했다. 온통청년·복지로·
천안 웹 Source mapping은 명확한 원문만 requirements·documents·exclusions로
승격하고 의미가 혼재한 field는 unknowns로 보존한다. 당시 Backend exact field
parity와 충돌하지 않도록 독립 nested 계약으로 먼저 승인했고, ES2에서
`NormalizedProgram`·DB·상세 API에 함께 편입했다.

#### DTL4-4 역할·commit 분리

- Integration 08 전체는 `feature/schema/eligibility-evidence-contract`에서
  진행하고 Slice마다 브랜치를 추가하지 않는다.
- Data·Team Leader 변경은 `feat(data)`, Backend 변경은 `feat(backend)`,
  Frontend 변경은 `feat(frontend)`, 통합 검증·문서는 `test(integration)`·
  `docs(integration)` Conventional Commit 경계로 구분한다.
- Backend·Frontend 담당자가 별도 브랜치에서 작업한 경우 Team Leader가 승인
  계약을 기준으로 commit을 현재 Integration 브랜치에 반영한다.
- ES2 Backend API 뒤 ES3 Frontend가 실제 응답 소비를 확인하고, Team Leader는
  같은 브랜치의 최종 결과에서 DB → API → Browser E2E를 수행한다.
- 개인 휴대전화·개인 이메일·성명은 시설 연락처 계약과 UI에 포함하지 않는다.

#### DTL4-4B - actual 소비 인계

- Backend DTO fixture와 Frontend TypeScript·Mock이 Data JSON과 일치하는지 확인
- 사용자 로컬 조건 비교는 `조건상 일치`, `조건상 불일치`, `추가 확인 필요`만
  제공하도록 근거를 분리
- 추천 이유가 구조화 조건을 자격 확률로 바꾸지 않는지 Integration 06 검토
- 정책 상세에서 각 요약이 공식 원문으로 추적 가능한지 actual E2E 준비

진행 결과(`2026-08-10`): 등록 Source dispatcher와 소비자 인계 fixture를
추가했다. canonical Seed에 포함되는 API 정책 4건과 승인 웹 Source 합성 표본
`notice:674` 1건의 identity·요약·evidence를 같은 JSON으로 고정했다. ES2에서
`NormalizedProgram 1.2.0` 37필드, Migration `20260810_0006`, JSONB 저장과
상세 API를 구현하고 PostgreSQL actual을 통과했다. 목록 payload는 유지한다.
ES3는 Frontend 상세 TypeScript·Mock과 신청·제외·우대 조건, 필요 서류, 문의처,
공개 evidence UI를 구현했다. 승인 웹 표본 Browser 주입으로 키보드·모바일까지
검증했다. ES4는 승인 천안 fixture를 실제 PostgreSQL에 적재해 상세 API와
Browser의 조건·서류·문의처·evidence를 대조하고, Release 1 snapshot 3,156건의
HTTP 기술 감사와 실제 Browser golden 회귀까지 통과했다.

### 완료 기준

- 필수·제외·우대·서류·unknown과 evidence가 Schema 검증을 통과함
- 기존 정책 상세·검색 소비 호환 또는 승인 migration이 검증됨
- API Source 사례와 웹 Source 사례가 실제 DB에 존재함
- Backend·Frontend fixture·type 소비 검토 완료
- 실제 DB → 상세 API → 핵심 신청 조건 UI에서 evidence가 일치함

## Slice DTL4-5 - 소비 계약 대조와 W4-G1 주관

### 목적

영역별 기반 구현이 W4-G0을 서로 다르게 해석하지 않았는지 조기에 확인한다.

### Team Leader 수행 작업

- Data JSON Schema·fixture, Backend OpenAPI·Migration과 Frontend TypeScript·Mock의
  field·required·nullable·enum·오류 parity를 대조한다.
- 관리자 PIN이 아이디 없는 4자리 한 칸이고 `0000`이 local development에서만
  동작하는지 초안을 확인한다.
- 관리자 데이터 화면이 승인 Policy projection 읽기 전용이고 arbitrary SQL·
  수정·삭제 경로가 없는지 검토한다.
- 파일 로그가 request·CollectionRun·Source·단계 correlation을 가지며 PIN·token·
  Raw·SQL parameter를 기록하지 않는지 검토한다.
- archive 삭제·현재 로그 rotate 정리·path containment·별도 감사 의미를
  Backend·Frontend가 동일하게 소비하는지 확인한다.
- 추천·즐겨찾기·D-Day·알림·`.ics`가 일정상 후순위라는 이유로 범위에서
  빠지지 않았는지 확인한다.
- Data 05가 기존 NormalizedProgram 1.2.0·Importer·상세/검색 API를 재사용하고,
  교차 Source 중복 후보를 새 Policy row로 적재하지 않는 경계를 대조한다.

### W4-G1 승인 조건

- 각 담당의 승인 계약 소비 테스트가 존재함
- HTML·자격요건·관리자 데이터·로그 fixture가 공개 DTO와 일치함
- PIN·token·비밀·Raw·SQL parameter 비노출 테스트가 존재함
- 계약 변경이 발생하면 구현보다 기준 문서와 소비 검토가 먼저 갱신됨
- 병합 충돌과 actual 연결 순서가 담당·브랜치·commit 기준으로 정리됨

### 차단 처리

소비 불일치는 한 영역의 구현에 억지로 맞추지 않는다. 계약 권위, 영향받는
Data·Backend·Frontend, 선택지와 재개 조건을 기록하고 필요한 경우
`docs/index.md` 인계 보드에 실제 차단사항을 등록한다.

## Slice DTL4-6 - 영역별 검증과 W4-G2 준비 판정

### 목적

actual 통합 전에 각 영역의 단위·통합 결과와 Data 실제 수집·DB 결과가 준비됐는지
판정한다.

### Data 검증

- Data 전체 단위 테스트
- Data 03 동일·수정·중복·단계 실패 PostgreSQL 통합
- Data 04 HTML fixture·HTTP 경계·actual 제한 수집·DB 적재
- Data 05 RYP0~RYP5 inventory·Source 승인·Adapter·지역 고유성·온통청년/복지로
  중복 제외와 대표 actual 단위·통합 준비
- Data 06 SOP0~SOP3 후보 정제·snapshot 중복 감사·Source 승인·Adapter 단위·통합 준비
- Integration 08 Schema·mapping·provenance·호환 테스트
- Runtime Raw·HTML·로그와 비밀·DB 파일 Git 비추적 확인

### 다른 담당 결과 확인

- Backend: PIN·권한, CollectionRun, 관리자 data/log, 자격요건·추천 PostgreSQL
  테스트 결과
- Frontend: PIN·관리자 data/log, 핵심 조건·추천·로컬 기능 unit·lint·build와
  Mock Browser 결과
- 미실행·실패 테스트, 환경 제약과 actual E2E blocker가 숨겨지지 않았는지 확인

다른 담당 테스트를 Team Leader가 대신 통과로 기록하지 않는다. 결과 명령,
종료 코드와 근거 위치를 받아 대조한다.

### W4-G2 승인 조건

- Data 단위·PostgreSQL·actual 웹 수집이 통과함
- Backend·Frontend의 담당자 자체 검증이 통과함
- actual DB·API·Browser 실행에 필요한 Migration·환경변수·fixture가 준비됨
- blocker가 없거나 담당·수정·재검증 조건이 명확함

## Slice DTL4-7 - 세 actual E2E와 W4-G3

### 목적

Mock이나 문서가 아니라 실제 PostgreSQL·Runtime 파일·FastAPI·React에서 세
Critical Path를 검증한다.

### E2E A - 관리자

```text
로컬 최초 PIN 0000 로그인
  → 정책 데이터 표·filter·row 상세
  → CollectionRun 이력·수동 실행
  → run 상태·품질 통계
  → request/run/source·단계 로그 검색
  → 현재 로그 rotate 정리 또는 archive 삭제
  → 별도 감사 기록 확인
```

- PIN 오류·`429`·token 만료·`401`·`403` 확인
- arbitrary SQL·정책 수정·임의 file path·활성 handle·감사 기록 삭제 차단
- PIN·token·hash·secret·Raw·SQL parameter 비노출

### E2E B - 웹 Source·자격요건

```text
공식 HTTPS Source 제한 수집
  → HTML Raw·Extract·Normalize·Validate
  → 지역 고유성·온통청년/복지로 중복 제외
  → PostgreSQL upsert·CollectionRun
  → 정책 상세 API
  → 핵심 신청 조건·제외·서류·unknown·공식 원문 UI
```

- API·웹 evidence, source URL·수집 시각과 UI 항목 일치
- Data 05 대표 지역 Source의 실제 정책만 적재되고 전국 재게시·확정 중복은
  사용자 검색·상세에 나타나지 않음
- Data 06 우선 Source의 실제 정책만 적재되고 온통청년·복지로·Data 05 확정 중복은
  사용자 검색·상세에 나타나지 않음
- missing·partial·selector drift와 실패 격리
- 실제 자격을 확정하지 않고 추가 확인 필요 표시

### E2E C - 추천·사용자 기능

```text
사용자 조건 저장
  → 추천·점수 구간·추천 이유·미확정 조건
  → 즐겨찾기
  → D-Day·웹 내부 알림
  → 정책별 .ics 생성·등록
```

- 날짜 미상·상시에 임의 D-Day·알림이 생기지 않음
- localStorage 정상·손상·version migration·전체 삭제
- 추천 점수가 자격 확률이나 요청 간 절대값으로 표시되지 않음

### Release 1 회귀

- 기존 golden natural/control query와 정책 identity·reason·unknown
- 목록·상세·검색 loading·empty·error·partial
- 기존 실제 snapshot과 Policy API 호환

### 결함 조정

- 최초 실패, 재현 조건, 담당 Forest, 수정 commit과 재검증 결과를 보존한다.
- Data 결함만 직접 수정하고 Backend·Frontend 변경은 해당 담당자에게 인계한다.
- 범위 밖 구조 변경이 필요하면 임의 구현하지 않고 선택지와 Release 영향을
  기록한다.

### W4-G3 승인 조건

- 세 E2E와 Release 1 회귀가 실제 환경에서 실행됨
- 차단 결함이 수정·재검증됐거나 Gate가 `BLOCKED`로 기록됨
- 비밀·Raw·Runtime log·DB 파일이 Git에 포함되지 않음
- Data·API·UI의 identity·상태·evidence·시간 의미가 일치함

## Slice DTL4-8 - 전체 회귀·문서·W4-G4 midpoint

### 목적

모든 기본 기능 구현과 담당자 자체 검증을 확인하고 5주차 추가 기능·오류 수정·
UI/UX 최적화 및 독립 리뷰를 시작할 수 있는지 판정한다.

### Data 마감

- Data 03·04·05와 Integration 08 전체 회귀·actual 수치 정리
- Source·Schema·normalization·collection·quality·operations 문서 동기화
- 실제 구현 Forest별 Data 개발 기록과 검증 결과 작성
- Runtime Raw·HTML·로그, API key, pgpass와 DB file 비추적 최종 확인

### Team Leader 마감

- Backend·Frontend 전체 회귀, OpenAPI·TypeScript·Schema·Migration 대조
- 관리자 PIN 설정 방법, 파일 로그와 Runtime 경계가 README·`.env.example`·
  운영 문서에 실제 구현대로 기록됐는지 확인
- 완료된 의미 있는 기능만 `CHANGELOG.md` `[Unreleased]`에 요약
- 실행하지 않은 독립 QA·사용성 리뷰·보고서 대조를 완료로 기록하지 않음
- 5주차에는 기본 기능 이월이 아니라 승인 추가 기능, 결함 수정, UI/UX 최적화와
  독립 검증만 시작하도록 인계

### W4-G4 판정

- `W4-G4_MIDPOINT_PASS`: 모든 기본 기능·세 E2E·담당자 회귀·문서 완료
- `W4-G4_CONDITIONAL`: 모든 기본 기능은 구현됐고 낮은 위험 결함 또는 비차단
  검증 제약의 담당·완료 조건이 명확함
- `W4-G4_BLOCKED`: 기본 기능 하나라도 미구현, 필수 E2E·계약·보안 경계 실패

다음 중 하나라도 빠지면 `PASS`나 `CONDITIONAL`을 사용할 수 없다.

- 공식 웹 Source actual 수집·DB 적재
- 핵심 신청 조건 Data·API·UI evidence
- 추천·점수 의미·이유
- 즐겨찾기·D-Day·웹 내부 알림·`.ics`
- 4자리 관리자 PIN·CollectionRun
- 관리자 정책 데이터 표
- 구조화 파일 로그·조회·rotate·archive 삭제·감사
- 실제 관리자·웹 Source·사용자 E2E

## 다른 담당자에게 요청할 산출물

### Backend

- PIN session·권한·rate limit과 README 설정 방법
- CollectionRun 목록·상세·수동 실행·stale
- 읽기 전용 Policy 관리자 API
- 구조화 file logging·조회·삭제·감사 API
- 자격요건 상세와 결정적 추천 API
- 단위·PostgreSQL·보안·성능 회귀 결과

### Frontend

- 4자리 PIN 로그인·만료·로그아웃·보호 route
- 관리자 정책 데이터·CollectionRun·로그 UI
- 핵심 신청 조건과 공식 원문 연결
- 추천·이유·미확정, 즐겨찾기·D-Day·알림·`.ics`
- unit·lint·build·Mock·actual Browser 결과

### 5주차 후속 역할

- 보고서: 결정·화면·테스트·미실행 검증 근거 대조
- 사용성 리뷰어: 독립 사용자·관리자 시나리오와 기대 결과 수행
- QA: 요구사항 추적, 실제·경계·실패 데이터와 전체 회귀

이 역할들은 4주차 담당자 자체 검증을 대신하지 않으며 4주차 완료 조건에도
포함하지 않는다.

## 테스트와 검증 명령

실제 Forest에서 확정한 명령을 우선하고 실행하지 않은 명령은 통과로 기록하지
않는다.

### Data

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
$env:TEST_DATABASE_URL = '<dedicated-postgresql-test-url>'
.\.venv\Scripts\python.exe -B -m pytest tests/integration -q
```

### Backend 결과 확인

```powershell
$env:TEST_DATABASE_URL = '<dedicated-postgresql-test-url>'
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q
```

### Frontend 결과 확인

```powershell
Set-Location frontend
npm run test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
```

### Integration·문서

- 실제 PostgreSQL·Runtime log → FastAPI → React 관리자 E2E
- 실제 HTTPS Source → PostgreSQL → 상세 API → 핵심 조건 UI E2E
- 실제 PostgreSQL → 추천 → 즐겨찾기·알림·`.ics` E2E
- Release 1 golden 검색·상세 회귀

```powershell
python scripts/validate_docs.py
git diff --check
```

PostgreSQL, Browser, API key 또는 Source 접근 환경이 준비되지 않으면 성공으로
처리하지 않고 blocker, 준비 담당과 재실행 조건을 기록한다.

## 위험과 대응

| 위험 | 영향 | 대응 |
| --- | --- | --- |
| 공식 웹 Source 미선정·약관 불명확 | Data 04 구현 시작 불가 | DTL4-1에서 실제 근거로 승인, 대체 Source 선택지 기록 |
| Data 03·04·08의 Schema 동시 수정 | 병합 충돌·계약 분기 | W4-G0에서 소유 브랜치·merge 순서 고정 |
| API·웹 identity 충돌 | 중복·잘못된 덮어쓰기 | source-scoped identity 유지, 자동 병합 금지 |
| 조건 원문의 과도한 구조화 | 잘못된 신청 가능 판단 | evidence 유지, 계산 불가를 unknown으로 표시 |
| 4자리 PIN 반복 대입 | 관리자 기능 우회 | local `0000` 한정, rate limit·cooldown·배포 fail-closed |
| 관리자 DB 화면 범용화 | 민감정보 노출·데이터 훼손 | 승인 Policy projection 읽기 전용, arbitrary SQL 금지 |
| 로그에 PIN·token·Raw·SQL parameter 기록 | 비밀·원문 유출 | event allowlist·redaction·비노출 회귀 |
| 로그 삭제 오용 | 진단 근거 소실·임의 파일 삭제 | archive ID·path containment·rotate·확인·별도 감사 |
| Backend·Frontend 병목 | 필수 기능 미완성 | Mock 선행·매일 소비 대조, 범위 축소 대신 W4-G4 blocked |
| actual 외부 데이터 변화 | 회귀 기대 변동 | 고정 fixture/contract와 최신 actual 관찰 분리 |
| Data 담당과 Gate 주관 겸임 | 자기 결과만으로 승인 | 다른 담당의 명령·결과·소비 증거 독립 대조 |

## 인계사항 발생 조건

다음 실제 차단이 생길 때만 `docs/index.md` 공동 인계 보드에 기록한다.

- 웹 Source 이용 조건·identity·DOM이 승인 계약과 충돌
- 자격요건 Schema·Migration 없이는 Backend·Frontend 소비 불가
- CollectionRun·품질 집계 의미가 Data와 Backend에서 다름
- 관리자 Policy projection이 필요한 Data field를 누락하거나 민감 field를 요구
- 로그 correlation·redaction·삭제 감사 의미가 영역별로 다름
- 추천·날짜·unknown 의미가 실제 Data와 UI에서 다름
- 다른 담당 Forest 변경 없이는 actual E2E가 진행되지 않음

미래 위험, 계획 자체와 5주차 독립 검증 예정은 활성 인계사항으로 등록하지
않는다.

## 완료 체크리스트

- [x] DTL4-0 시작 SHA·환경·브랜치·담당 확인
- [x] DTL4-1 Data inventory와 `W4-G0_APPROVED`
- [x] DTL4-2 Data 03 반복·수정·중복·실패·품질 통계 완료
- [x] DTL4-3 Data 04 공식 Source actual 수집·DB 적재 완료
- [x] DTL4-4 Integration 08 자격요건 evidence Data 구현·소비 검토 완료
- [ ] DTL4-5 Data·OpenAPI·TypeScript·Mock parity와 W4-G1 통과
- [x] Data 05 RYP0 후보 inventory·검증 계약 완료
- [x] Data 05 RYP1 Browser Discovery preflight·Source 승인 완료
- [x] Data 05 RYP2~RYP4 Adapter·지역·중복 제외 Gate 통과
- [ ] Data 06 SOP0~SOP3 후보 정제·중복 감사·승인·Adapter Gate 통과
- [ ] DTL4-6 영역별 단위·통합·actual 준비와 W4-G2 통과
- [x] Data 05 RYP5 대표 Source actual DB·API·Browser 인수 통과
- [x] Data 05 RYP6 13개 승인 Source 전체 pagination·판정·DB 동기화·회귀 완료
- [x] Data 05 RYP7 review 사유·field coverage·승격 계약 감사 완료
- [x] Data 05 RYP8 Source별 지역·청년 대상·신청 상태 추출 보강 완료
- [ ] Data 05 RYP9 전체 재판정·지역 검색 DB·API·Browser 인수와 RYP-G6 통과
- [ ] Data 06 SOP4 우선 Source actual DB·API·Browser 인수 통과
- [ ] Data 06 SOP5 Source군별 최종 상태·전체 회귀 완료
- [ ] DTL4-7 관리자·웹 Source·사용자 세 E2E와 W4-G3 통과
- [ ] Release 1 golden 검색·상세 회귀 통과
- [ ] Data·Backend·Frontend 전체 담당자 회귀 결과 대조
- [ ] Schema·API·DB·운영·README·개발 기록과 실제 구현 일치
- [ ] 비밀·Runtime Raw·HTML·로그·DB 파일 Git 비추적 확인
- [ ] `python scripts/validate_docs.py`와 `git diff --check` 통과
- [ ] W4-G4 midpoint 판정과 5주차 시작 조건 기록
- [ ] 독립 QA·사용성 리뷰·보고서 미수행 상태를 정확히 기록

## 관련 문서

- [4주차 전체 상세 계획](week_04_v0_5_0.md)
- [3주차 Data·Team Leader 실행 계획](week_03_data_team_leader.md)
- [v0.5.0 Contract Baseline](../develop_plan/integration/05_v0_5_0_contract_baseline.md)
- [Data 03 Recurrent Quality Operations](../develop_plan/data/03_recurrent_collection_quality_operations.md)
- [Data 04 Public HTTPS Ingestion](../develop_plan/data/04_public_https_policy_ingestion.md)
- [Data 05 Regional Youth Policy Ingestion](../develop_plan/data/05_regional_youth_policy_ingestion.md)
- [Data 06 Supplemental Official Policy Ingestion](../develop_plan/data/06_supplemental_official_policy_ingestion.md)
- [Integration 08 Eligibility Evidence and Summary](../develop_plan/integration/08_eligibility_evidence_summary.md)
- [Integration 09 Admin Data and Log Console](../develop_plan/integration/09_admin_data_log_console.md)
- [Integration 07 Release 2 Acceptance](../develop_plan/integration/07_release_2_feature_acceptance.md)
- [전체 Forest 로드맵](../develop_plan/forest_roadmap.md)
- [Release와 Milestone 계획](../develop_plan/release_roadmap.md)
- [Data Source 계약](../../data/data_sources.md)
- [수집 정책](../../data/collection_policy.md)
- [데이터 Schema](../../data/data_schema.md)
- [Policy API 계약](../../api/policies.md)
- [공동 확인 및 인계 보드](../../index.md#공동-확인-및-인계-보드)

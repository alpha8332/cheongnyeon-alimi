# ADR 0001: 정책 검색 데이터 기반

- 상태: accepted
- 작성일: 2026-07-31
- 승인일: 2026-08-03
- 결정자: Data·Backend·Frontend 소비 계약 검토, Team Leader Gate
- 관련 Issue/PR: 미정

## 맥락

현재 `NormalizedProgram` 1.0.0은 지역을 원문 `region_text`와 표준 이름
`regions` 배열로 보존하고 PostgreSQL JSONB exact membership으로 조회한다.
이 구조는 합성 Seed와 단일 지역 필터에는 적합하지만 다음 요구를 처리하기
어렵다.

- 천안 검색에서 천안시·충청남도·전국 정책을 함께 판정
- 지역 미상 중앙정부 정책과 명시적 전국 정책 구분
- 지역 포함·제외 규칙
- 행정구역 code의 개편·폐지·분할·별칭
- 온통청년·복지로와 향후 지역 웹사이트의 서로 다른 key 통합
- 사용자 표시 text와 검색 전용 projection 분리

2026-07-31 DT1 실제 표본에서 온통청년 10건은 `zipCd` 원문이 있지만 승인된
code-to-name 표가 없어 정규화 지역이 모두 비었고, 복지로 10건은
지역·연령·신청기간이 모두 없었다. 누락을 전국으로 추정하면 오탐이 되고,
현재 partial 기본 비노출을 유지하면 실제 정책이 검색에서 사라진다.

또한 온통청년 `plcyExplnCn`·`mclsfNm`·`plcyKywdNm`, 복지로
`wlfareInfoOutlCn`·`lifeArray`·`trgterIndvdlArray`는 Raw에 보존되지만 현재
공통 검색 필드에서 충분히 사용되지 않는다.

## 결정

Integration 03 PSF0에서 현재 Data 모델, Backend ORM·Importer·공개 API와
Frontend `PolicyDto`·Mock 소비를 대조하고 다음 구조를 채택한다.

1. Source Adapter가 원본 key를 Source 중립 공통 필드로 변환한다.
2. 정책 지역 적용 범위는 `nationwide`, `regional`, `unknown`으로 구분한다.
3. 행정구역은 이름 배열을 identity로 쓰지 않고 versioned code·parent·alias
   기준정보를 사용한다.
4. 정책과 지역은 include·exclude 관계로 저장하고 Source code와 근거 원문을
   보존한다.
5. 기존 `regions` 배열은 공개 호환용 파생 표현으로 유지한다.
6. Source 설명은 기존 `summary`에 채우고 `keywords`, `life_stages`,
   `target_groups`, `coverage_scope`, `region_rules`를
   `NormalizedProgram` 1.1.0의 필수 필드로 추가한다.
7. Korean text 검색용 projection은 공개 Policy DTO와 별도 저장 책임으로
   둔다.
8. 지역·연령·상태 판정은 `match`, `mismatch`, `unknown` 3값을 사용한다.
9. 기존 row에 근거가 없으면 `coverage_scope=unknown`으로 backfill하고
   전국이나 지역을 추정하지 않는다.
10. Source 간 canonical deduplication과 최종 자연어 검색 가중치는 별도
    Forest에 남긴다.
11. 기존 목록·상세 API의 필드 집합, 숫자 `id`, 품질 opt-in과 provenance
    비노출은 유지한다. 새 검색 내부 필드와 query별 판정 근거는 기존
    `PolicyRead`에 넣지 않고 Backend 06 검색 응답에서만 제공한다.
12. `data_quality_status`는 Source 데이터 완전성이고 검색 적합성 판정이
    아니다. 기존 목록·상세의 partial 기본 비노출은 유지하되 새 검색은
    valid·partial을 후보로 삼고 invalid는 제외한다. 명시적 `mismatch`는
    제외하고 `unknown`은 결과에 남겨 `unverified_conditions`로 전달한다.

### 실행 계약과 버전

`NormalizedProgram` 1.1.0은 현재 31개 필드에 다음 5개 필드를 추가한다.

| 필드 | 타입 | null·빈 값 | 의미 |
| --- | --- | --- | --- |
| `keywords` | string 배열 | `null` 금지, 없으면 `[]` | Source 공식 키워드와 검색용 분류어 |
| `life_stages` | string 배열 | `null` 금지, 없으면 `[]` | Source가 명시한 생애주기 |
| `target_groups` | string 배열 | `null` 금지, 없으면 `[]` | Source가 명시한 대상자 특성 |
| `coverage_scope` | enum | 필수, `unknown` 허용 | `nationwide`, `regional`, `unknown` |
| `region_rules` | object 배열 | `null` 금지, 없으면 `[]` | 포함·제외 지역과 Source 근거·해석 상태 |

`region_rules` 원소는 `relation=include|exclude`,
`resolution_status=matched|unmapped|ambiguous`, nullable
`region_scheme`·`region_code`와 nullable `source_code`·`source_text`를 가진다.
`matched`만 canonical scheme·code를 가져야 하며, `unmapped`와 `ambiguous`는
Source 근거를 버리지 않고 canonical code를 비워 둔다.

- `nationwide`는 `region_rules=[]`이고 Source 계약이나 원문에 명시적 근거가
  있을 때만 사용한다.
- `regional`은 하나 이상의 `matched` include rule이 있어야 한다.
- `unknown`에는 matched rule이 없어야 하지만 unresolved Source evidence는
  보존할 수 있다.
- 같은 canonical region을 include와 exclude에 동시에 둘 수 없다.
- 빈 배열은 “명시 정보 없음”이며 `null`이나 전국을 뜻하지 않는다.
- 세 string 배열의 원소는 공통 text 정규화를 거친 비어 있지 않은 문자열이며
  첫 등장 순서를 유지해 exact 중복을 제거한다. Source에 없는 `청년`, 지역,
  대상자 값을 시스템이 임의로 추가하지 않는다.

기존 1.0.0 입력은 PSF1의 명시적 compatibility adapter에서 새 배열을 `[]`,
`coverage_scope`를 `unknown`으로 보완한다. 기존 `regions` 값이나 문자열
`전국`을 generic adapter가 canonical code 또는 전국으로 추정하지 않는다.
기존 DB row의 `schema_version`도 Migration만으로 1.1.0으로 바꾸지 않고 실제
Raw 재처리나 승인된 1.1.0 입력 때만 갱신한다.

### 저장 모델

최종 테이블 이름과 책임을 다음과 같이 고정한다.

| 저장 대상 | 테이블·컬럼 | 결정 |
| --- | --- | --- |
| 공통 검색 배열·범위 | `policies.keywords`, `life_stages`, `target_groups`, `coverage_scope` | 배열은 JSONB `NOT NULL DEFAULT '[]'`, 범위는 enum `NOT NULL DEFAULT 'unknown'` |
| 행정구역 기준정보 | `administrative_regions` | scheme·code, 이름, level, 공식 parent, 검색용 aggregate parent와 유효기간을 보존 |
| 지역 별칭 | `administrative_region_aliases` | 별칭과 대상 region을 연결하며 모호한 별칭의 다중 후보를 허용 |
| 정책 지역 규칙 | `policy_region_rules` | include·exclude, canonical region, Source code·text와 resolution 상태 보존 |
| 검색 projection | `policy_search_documents` | 정책당 한 행, field별 text와 합성 `search_text`, projection version 보존 |

`administrative_regions`의 identity는 이름이 아니라 `(scheme, code)`다.
PSF2에서 공식 상위지역코드가 비자치구의 집계 시를 표현하지 않는 사례를
확인했다. 원천 parent는 덮어쓰지 않고 같은 공식 광역 parent 아래 현재 유효한
전체 이름의 정확 일치로 검증된 경우에만 nullable `aggregate_parent` 관계를
추가한다. 문자열 prefix나 폐지 code의 후계 지역은 추정하지 않는다.
`policy_region_rules`는 unresolved evidence를 보존하기 위해 canonical region
참조를 nullable로 두되, resolution 상태와 canonical reference 조합은 DB
constraint와 importer 검증을 함께 사용한다. `regional`의 matched include
존재처럼 다른 행을 함께 보는 불변식은 PSF3의 PostgreSQL deferred constraint
trigger로 transaction 최종 상태에서 검증한다.

### 검색과 공개 API 경계

- 기존 `/api/v1/policies` 목록·상세와 `region` exact filter는 호환 경계로
  유지한다. 계층 지역 검색으로 의미를 조용히 바꾸지 않는다.
- 새 내부 검색은 `policy_search_documents`와 관계형 지역 규칙을 사용하며
  Source Raw key를 직접 조회하지 않는다.
- 기존 공개 DTO에는 새 검색 전용 5개 필드나 provenance를 추가하지 않는다.
- 1.0.0과 1.1.0 row가 전환 기간에 함께 존재할 수 있으므로 Frontend의
  `schema_version` literal은 PSF1에서 `'1.0.0' | '1.1.0'`으로 넓힌다.
  Pydantic 공개 DTO는 현재 string이어서 구조 변경이 없다.
- `summary`와 호환용 `regions`는 기존 공개 필드이므로 새 Source mapping과
  승인된 region rule에서 값이 채워질 수 있다.
- 검색의 `matched_conditions`, `unverified_conditions`, 점수와 검색 이유는
  정책 원본이나 기존 `PolicyRead`에 저장하지 않고 query별 응답으로 만든다.
- PSF6 판정 primitive는 `match|mismatch|unknown`과 reason·evidence를 함께
  반환한다. 지역은 exact·ancestor·nationwide·exclude를 구분하고 exclude를
  우선하며, alias 다중 후보와 미매핑·정책 coverage 미상은 unknown 근거로
  보존한다. 자연어 parser와 최종 가중치는 Backend 06에서 이 primitive를
  조합한다.

## 필드 lineage 감사

### 온통청년

| Raw key | 현재 경로와 손실 | 채택 경로 |
| --- | --- | --- |
| `plcyNo`, `plcyNm` | external ID·title → Normalized → DB·API | 기존 경로 유지 |
| `operInstCdNm`, `rgtrInstCdNm` | organization 우선순위 → DB·API | 기존 경로 유지 |
| `plcyExplnCn` | `extra.source_fields`까지만 보존되고 Normalized 이후 유실 | `summary` → `policies.summary` → 기존 API·projection |
| `lclsfNm` | `category_text` → `categories` → JSONB·API | 기존 경로 유지, projection에도 포함 |
| `mclsfNm`, `plcyKywdNm` | `extra.source_fields` 이후 유실 | `keywords` → JSONB·projection, 기존 DTO에는 비노출 |
| `zipCd` | `region_text`까지 전달되나 code-to-name 표가 없어 `regions=[]`·partial | adapter → `region_rules`; 매핑 성공은 canonical relation, 실패는 unresolved evidence와 `unknown` |
| `sprtTrgtMinAge`, `sprtTrgtMaxAge` | `age_text` → `age_min`·`age_max`·원문 → DB·API | 기존 경로 유지, 3값 age 판정 입력 |
| `aplyYmd`, `aplyPrdSeCd` | 신청기간 원문·date·schedule·status → DB·API | 기존 경로 유지, 승인·게시 코드는 신청 가능 상태로 오용하지 않음 |
| `ptcpPrpTrgtCn`, `addAplyQlfcCndCn` | 결합 eligibility → DB·API | 기존 경로 유지, projection eligibility |
| `plcySprtCn`, `plcyAplyMthdCn` | support·method → DB·API | 기존 경로 유지, projection support |

### 복지로

| Raw key | 현재 경로와 손실 | 채택 경로 |
| --- | --- | --- |
| `servId`, `servNm`, `jurMnofNm` | identity·title·organization → DB·API | 기존 경로 유지 |
| `servDgst`, `wlfareInfoOutlCn` | `servDgst`는 support fallback, 개요는 `extra` 이후 유실 | 상세 개요 우선·목록 요약 fallback으로 `summary`; 기존 support fallback은 호환 유지 |
| `intrsThemaArray` | `category_text` → `categories` → DB·API | 기존 category와 `keywords` 양쪽에 Source 근거로 사용 |
| `lifeArray` | `extra.source_fields` 이후 유실 | `life_stages` → JSONB·projection |
| `trgterIndvdlArray` | `extra.source_fields` 이후 유실 | `target_groups` → JSONB·projection |
| `tgtrDtlCn`, `slctCritCn` | 상세가 있으면 eligibility → DB·API | 기존 경로 유지, projection eligibility |
| `alwServCn` | detail/list support → DB·API | 기존 경로 유지, projection support |
| 지역·연령·신청기간 | 현재 API 근거 key 없음 | 값을 만들지 않고 coverage·조건 판정을 `unknown`으로 유지 |

두 Source 모두 Raw byte, `extra.source_fields`와 provenance가 재처리 근거다.
PSF4 adapter는 위 채택 경로를 구현했으며 공통 필드로 명시적으로 승격하지
않은 Source key는 검색에 사용하지 않는다. 온통청년 `zipCd`는 실제 표본의
고유 code 260개가 모두 `kr-bjd-prefix5` exact crosswalk와 일치한 근거만
사용하고, 폐지 code를 후계 지역으로 치환하거나 미매핑 값을 추정하지 않는다.

## 호환성·Migration 영향

| 소비자 | 영향 | PSF 후속 조치 |
| --- | --- | --- |
| Data Schema·모델 | 1.1.0 필수 필드 5개와 legacy adapter 필요 | PSF1 Schema·Fixture·Seed·null/빈 배열/enum 테스트 |
| Extractor·Normalizer | 핵심 key를 `extra`에서 공통 필드로 승격 | PSF4 Source별 mapping·누락 회귀 |
| PostgreSQL | 네 정책 컬럼, 세 지역 테이블, projection 테이블과 index 추가 | PSF3 additive Migration·backfill·downgrade |
| Importer | Policy·region rule·projection의 단일 transaction 필요 | PSF5 rollback·idempotency·projection version 검증 |
| 기존 Policy API | endpoint·field set·partial opt-in 유지, schema version 값과 표시 값은 확장 | PSF1 Frontend version union, PSF7 목록·상세 회귀 |
| Backend 검색 | 기존 exact repository와 분리된 3값 primitive 필요 | PSF6 primitive 완료, Backend 06 query·정렬 구현으로 인계 |
| Frontend 검색 | 기존 `PolicyDto`만으로 검색 이유를 만들 수 없음 | Frontend 04가 별도 검색 응답의 조건·이유·미확인을 표시 |

PSF5는 Importer 조치를 projection version `1.0.0`, 호출자 소유 rebuild service와
단일 transaction 관계 교체로 구현했다. Runtime Normalizer warning도 accepted
program과 함께 전달해 partial 분류 근거를 보존한다.

PSF7은 기존 공개 `PolicyRead` 33개 field와 Frontend version union·Mock 소비를
유지하고 Backend 판정 계층의 Source 패키지 실행 의존을 제거했다. 합성 20,000건
plan에서는 trigram GIN이 강제 사용 가능하지만 기본 planner가 `ILIKE`에
Sequential Scan을 선택했다. 최종 query·실데이터 분포 없이 index나 DB 비용
설정을 바꾸지 않고 Backend 06의 plan 검증 항목으로 인계한다.

Migration은 기존 row에 배열 `[]`, `coverage_scope=unknown`과 빈 projection을
안전하게 준비하되 Source 근거를 생성하지 않는다. projection은 명시적인
backfill/rebuild 절차로 채우고, downgrade는 새 테이블·컬럼을 제거하되 기존
31개 필드와 source identity·provenance를 보존한다.

## 고려한 대안

### 기존 `regions` JSONB 배열 유지

구현은 단순하지만 상위 지역·전국·제외·행정구역 변경을 표현하기 어렵고
문자열 exact match가 이름 변경과 별칭에 취약하다.

### 누락 지역을 모두 전국으로 처리

검색 결과는 늘지만 Source가 제공하지 않은 적용 범위를 생성해 잘못된 신청
가능성을 안내할 위험이 있어 채택하지 않는다.

### 모든 Source 원본 key를 Backend 검색에서 직접 사용

Source 추가마다 Repository와 query가 바뀌고 Raw key가 API·UI까지 누출되므로
채택하지 않는다.

### 모든 지역·검색 정보를 하나의 JSONB에 저장

초기 Migration은 쉽지만 FK·계층·유효기간·참조 무결성과 query plan을
보장하기 어려워 기준정보와 관계는 관계형 저장을 우선한다.

### Source 간 canonical 정책 테이블을 동시에 도입

장기적으로 유용하지만 현재 동일 정책 판정 근거가 없고 제목 기반 병합은
오탐 위험이 크다. source-scoped identity와 provenance를 유지해 향후
canonical layer를 추가할 수 있게만 한다.

## 결과

예상 장점:

- 중앙정부 API와 향후 지역 crawler가 같은 검색 계약 사용
- 천안·충남·전국·미확인·타 지역의 결정적 판정
- Source 누락을 숨기지 않는 검색 이유와 미확인 조건
- 행정구역 변경과 별칭의 추적 가능성
- 사용자 표시 DTO와 검색 index의 책임 분리

비용:

- Normalized Schema·Fixture·Seed 공동 검토
- Alembic Migration, 기준정보 생성과 PostgreSQL 관계 테스트
- Importer transaction과 projection 동기화 복잡도 증가
- Backend·Frontend 소비 계약 재검증

호환성:

- 기존 `(source_id, external_id)`와 provenance를 유지한다.
- 기존 공개 목록·상세는 additive 또는 내부 전용 변경을 우선한다.
- breaking contract가 필요하면 version과 Migration 영향을 명시한다.
- 기존 exact region filter와 새 계층 검색이 한 endpoint에서 서로 다른 의미로
  섞이지 않는다.
- 기존 partial 기본 비노출은 목록·상세에만 적용하며 검색 후보 정책과
  분리한다.

## 검증 방법

- Schema·Python 모델·Fixture·Seed field set과 enum 검증
- 빈 DB·populated DB Migration upgrade·downgrade
- region parent·alias·validity의 고아·중복·순환 검사
- 전국·상위·정확·타 지역·미확인·exclude PostgreSQL 통합 테스트
- DT1 실제 Raw의 오프라인 재처리
- Importer idempotency·rollback과 search projection 동기화
- 기존 Policy API·Frontend 타입 회귀
- 합성 규모 `EXPLAIN (ANALYZE, BUFFERS)` 기록

## 후속 작업

- PSF1에서 1.1.0 실행 계약, legacy adapter와 소비 Fixture 구현
- PSF2에서 권위 있는 행정구역 scheme·version·license 확정
- PSF3~PSF7에서 Migration·mapping·transaction·판정과 회귀 검증
- 구현과 검증이 완료된 Slice에서 데이터 Schema·정규화·DB·API 기준 문서 갱신
- Data 02 DT2에서 검색 노출 의미와 Backend 06 계약 승인
- 별도 지역 Source Forest에서 공식 웹사이트 crawler 구현

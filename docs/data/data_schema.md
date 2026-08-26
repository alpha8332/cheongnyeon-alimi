# 데이터 Schema 기준선

## 문서 상태

- 상태: 논리적 기준선
- 현재 구현 상태: Raw·Extracted·Normalized Python 모델, Raw·Normalized
  JSON Schema, Source 검색 Adapter, 합성 Fixture·canonical JSON Seed와
  versioned 행정구역 기준정보·resolver 구현

이 문서는 `RawPolicyDocument`, `ExtractedPolicy`와
`NormalizedProgram`의 역할과 필드 원칙을 정의한다. 실행 가능한 계약은
`data/schema/*.schema.json`으로 구현하고 이 문서와 함께 관리한다. 현재 Raw
계약은
[`raw_policy_document.schema.json`](../../data/schema/raw_policy_document.schema.json)
Schema version `1.0.0`이다.

## 데이터 단계

```text
External Response
→ RawPolicyDocument
→ ExtractedPolicy
→ NormalizedProgram
→ Validator
```

| 단계 | 목적 | 소스별 구조 인식 | 원문 보존 |
| --- | --- | --- | --- |
| Raw | 응답과 수집 문맥 보존 | 최소 | 필수 |
| Extracted | 소스 필드를 공통 의미 단위로 추출 | 있음 | Raw 참조 |
| Normalized | 서비스가 사용하는 공통 형식으로 변환 | 없음 | 원문 필드 병행 보존 |

## `RawPolicyDocument`

API와 웹 Collector가 같은 envelope를 사용하되 소스별 payload를 이 단계에서
억지로 통일하지 않는다. 현재 구현은 온통청년·복지로 API뿐 아니라 공공 CSV와
지역·보완 공식 Source의 JSON·HTML 응답도 Raw로 보존한다.

| 필드 | 논리 타입 | 기준 |
| --- | --- | --- |
| `schema_version` | string | 현재 Raw 계약 `1.0.0` |
| `document_id` | string | Raw 문서별 32자리 lowercase UUID hex |
| `source_id` | string | 소스의 안정적인 식별자 |
| `source_type` | enum | `api`, `web` |
| `document_role` | enum | `list_response`, `list_item`, `detail_response` |
| `external_id` | string 또는 null | source-scoped 목록·상세 연결 ID |
| `parent_document_id` | string 또는 null | 파생 항목이 참조하는 목록 응답 ID |
| `source_url` | HTTPS URI string | query·fragment·user information이 없는 endpoint |
| `collected_at` | date-time string | timezone을 포함한 수집 시각 |
| `content_type` | string | 응답의 media type |
| `raw_format` | enum | `json`, `xml`, `html`, `csv` |
| `raw_payload_base64` | string | 원본 byte를 Base64로 인코딩한 값 |
| `content_hash` | string | 원본 byte의 `sha256:<64 lowercase hex>` |
| `byte_length` | integer | Base64 디코딩 후 원본 byte 길이 |
| `http_status` | integer | Raw를 만든 성공 응답의 200~299 상태 |
| `collector_version` | string | 수집 로직 버전 |

모든 필드는 required다. 의미상 값이 없는 관계 ID도 필드를 생략하지 않고
`null`을 사용한다. 추가 필드는 허용하지 않는다.

### 문서 역할과 연결

| 역할 | payload 경계 | `external_id` | `parent_document_id` |
| --- | --- | --- | --- |
| `list_response` | 목록 HTTP 응답 전체 byte | `null` | `null` |
| `list_item` | 목록에서 분리한 한 항목 | 필수 | 부모 `list_response.document_id` |
| `detail_response` | 상세 HTTP 응답 전체 byte | 필수 | `null` |

`list_response`와 `detail_response`는 HTTP body의 원본 byte를 권위 있는 원문으로
보존한다. `list_item`은 추출 편의를 위한 파생 Raw이며 반드시 부모 전체 응답을
참조한다. 목록 항목과 상세 응답은 같은 `source_id + external_id`로 연결한다.
external ID의 구체적인 필드와 추출 규칙은 Source Adapter가 소유한다. 예를 들어
온통청년은 `plcyNo`, 복지로는 `servId`를 사용한다.

### 원문과 Hash

- JSON 객체 재직렬화나 XML tree 변환은 공백, 순서와 encoding을 바꿀 수
  있으므로 HTTP body byte를 Base64로 저장한다.
- `content_hash`는 envelope, Base64 문자열이나 메타데이터가 아니라 Base64
  디코딩 후 원본 byte에 SHA-256을 계산한다.
- `byte_length`, Base64 payload와 Hash가 서로 다르면 Python 모델 로드
  단계에서 거부한다.
- 같은 원본 byte는 수집 시각, 문서 역할과 ID가 달라도 같은 Hash를 만든다.
- `source_url`은 HTTPS endpoint만 보존하고 query 전체를 제거한다.
- 요청 자체가 실패하거나 HTTP 상태가 200~299가 아니면 정상 Raw 문서를
  만들지 않고 수집 실행 실패로 분리한다.

### Runtime 저장

기본 운영 Raw root는 Git에서 제외된 `runtime/raw/`다.

```text
runtime/raw/<source_id>/<document_role>/<UTC YYYY>/<MM>/<DD>/<document_id>.json
```

저장기는 root 아래 경로만 허용하고 source ID와 document ID 형식을 검증한다.
완성된 임시 파일을 같은 파일시스템에서 연결해 부분 파일 노출을 막고 같은
`document_id` 파일을 덮어쓰지 않는다. 로드할 때도 symlink를 포함한 실제
경로가 설정 root 밖이면 거부한다.

### 필수 원칙

- 실제 운영 Raw는 Git에 포함하지 않는다.
- Raw byte에 개인정보나 재배포 불가 내용이 있을 수 있으므로 검토 없이
  Fixture로 복사하지 않는다.

## `ExtractedPolicy`

Source Extractor가 소스별 Raw에서 의미 있는 중간 필드를 추출한다.

| 필드 | 논리 타입 |
| --- | --- |
| `source_id` | string |
| `source_name` | string |
| `external_id` | string |
| `title` | string 또는 null |
| `organization` | string 또는 null |
| `summary` | string 또는 null |
| `category_text` | string 또는 null |
| `keywords` | string tuple, 없으면 `()` |
| `life_stages` | string tuple, 없으면 `()` |
| `target_groups` | string tuple, 없으면 `()` |
| `application_period_text` | string 또는 null |
| `region_text` | string 또는 null |
| `coverage_scope_hint` | `nationwide`, `regional`, `unknown` |
| `region_evidence` | Source code·text와 include·exclude tuple |
| `age_text` | string 또는 null |
| `eligibility_text` | string 또는 null |
| `support_content` | string 또는 null |
| `application_method` | string 또는 null |
| `source_url` | HTTP(S) URI string |
| `collected_at` | timezone 포함 date-time |
| `provenance` | 기여 Raw 문서 배열 |
| `extra` | object |

현재 등록된 Source의 목록 항목에는 source-scoped 외부 ID가 있으므로
`ExtractedPolicy.external_id`는 필수 string이다. 선택 공통 필드의 원문이
없거나 빈 문자열이면 해당 공통 필드는 null로 전달한다. 다만 누락과 빈
문자열을 구분할 수 있도록 `extra.source_fields`에는 실제 필드 존재 여부와
값을 그대로 보존한다.

`extra.source_fields.list_item`에는 목록 항목의 모든 source 필드를 넣는다.
복지로 상세가 결합되면 `detail_response`에도 모든 상세 leaf 값을 넣고 상세가
없으면 null을 사용한다. XML에서 같은 이름의 leaf가 한 번이면 string, 반복되면
원문 순서의 string 배열이다. 따라서 공통 필드로 매핑한 값, 코드, 미매핑
필드와 빈 문자열을 Raw 재로드 없이도 확인할 수 있고 정확한 byte와 계층은
provenance가 가리키는 Raw에서 재현한다.

검색 필드는 Source Adapter가 명시적인 Source key만 승격한다. 온통청년은
`plcyExplnCn`, `mclsfNm`, `plcyKywdNm`, `zipCd`를 사용하고 복지로는
`wlfareInfoOutlCn`·`servDgst`, `intrsThemaArray`, `lifeArray`,
`trgterIndvdlArray`를 사용한다. HTML Source도 `SourceRegionEvidence`에
include·exclude, 외부 code scheme과 원문 code·text를 명시하며 공통
Normalizer가 Source별 JSON key나 HTML selector를 직접 해석하지 않게 한다.

### Extracted provenance

`provenance`의 각 항목은 다음 필드를 가진다.

| 필드 | 논리 타입 | 기준 |
| --- | --- | --- |
| `raw_document_id` | string | 기여한 Raw의 `document_id` |
| `document_role` | Raw role enum | 목록 전체·항목·상세 구분 |
| `content_hash` | string | 기여 Raw의 SHA-256 |
| `collected_at` | date-time | 기여 Raw의 timezone 포함 수집 시각 |
| `source_url` | HTTP(S) URI | 기여 Raw의 query 없는 안전한 endpoint |

온통청년 정책은 부모 `list_response`와 `list_item`, 복지로 정책은 두 문서에
선택적인 `detail_response`를 더한다. 정책의 `collected_at`은 기여 Raw 중 가장
최근 시각이다. `source_url`은 source가 제공한 공개 정책 URL이 안전하고
유효하면 사용하고, 그렇지 않으면 해당 Raw의 안전한 API endpoint로
fallback한다.

`ExtractedPolicy`는 XML 태그와 JSON 필드명을 공통 Normalizer로 노출하지 않기
위한 내부 경계다. 이 모델을 바꿀 때는 Normalized Schema, Fixture와 Seed의
재생성 영향을 확인한다. Extracted 자체를 서비스 소비자 계약으로 승격하려면
필수·null·배열 규칙을 Backend·Frontend와 별도로 공동 검토해야 한다.

## `NormalizedProgram`

현재 실행 가능한 계약은
[`normalized_program.schema.json`](../../data/schema/normalized_program.schema.json)
Schema version `1.2.0`이다. 객체의 필드는 모두 required로 고정하고 의미상
선택 단일 값은 null, 복수 값은 빈 배열로 표현한다. 이 방식으로 필드 생략과
값 없음이 섞이지 않게 한다.

| 필드 | 논리 타입 | 기준 |
| --- | --- | --- |
| `schema_version` | string | 현재 계약 `1.2.0` |
| `source_id` | string | 안정적인 내부 source ID |
| `source_name` | string | 사용자에게 표시할 소스 이름 |
| `external_id` | string 또는 null | source-scoped 외부 ID |
| `title` | string | 필수, 정규화 후 빈 값 금지 |
| `organization` | string 또는 null | 담당·운영 기관 |
| `summary` | string 또는 null | 현재 두 Extractor에는 공통 입력 없음 |
| `category_text` | string 또는 null | 분류 원문 text |
| `categories` | category enum 배열 | 다중 분류, 없으면 `[]` |
| `keywords` | string 배열 | Source 공식 키워드·검색 분류어, 없으면 `[]` |
| `life_stages` | string 배열 | Source가 명시한 생애주기, 없으면 `[]` |
| `target_groups` | string 배열 | Source가 명시한 대상자 특성, 없으면 `[]` |
| `application_period_text` | string 또는 null | 신청기간 원문 text |
| `application_start` | date 또는 null | `YYYY-MM-DD` |
| `application_end` | date 또는 null | `YYYY-MM-DD` |
| `application_schedule` | enum 또는 null | 일정 유형 |
| `application_status` | enum 또는 null | 수집 기준 시점 상태 |
| `region_text` | string 또는 null | 지역 원문 text·코드 |
| `regions` | string 배열 | 표준화된 지역 이름 |
| `coverage_scope` | coverage enum | `nationwide`, `regional`, `unknown` |
| `region_rules` | region rule object 배열 | 포함·제외 canonical 지역과 Source 근거 |
| `age_min` | integer 또는 null | 0~150 |
| `age_max` | integer 또는 null | 0~150 |
| `age_condition_text` | string 또는 null | 연령 원문 text |
| `eligibility_text` | string 또는 null | 자격 원문 |
| `eligibility_summary` | Eligibility Summary object | 구조화 조건·서류·시설 문의처와 공개 evidence |
| `support_content` | string 또는 null | 지원 내용 |
| `application_method` | string 또는 null | 신청 방법 |
| `education_statuses` | string 배열 | 없으면 `[]` |
| `employment_statuses` | string 배열 | 없으면 `[]` |
| `required_conditions` | string 배열 | 없으면 `[]` |
| `preferred_conditions` | string 배열 | 없으면 `[]` |
| `excluded_conditions` | string 배열 | 없으면 `[]` |
| `source_url` | HTTP(S) URI | user information 금지 |
| `collected_at` | date-time | timezone 필수 |
| `provenance` | Raw provenance 배열 | 최소 1개, 중복 금지 |
| `data_quality_status` | 품질 enum | `valid`, `partial`, `invalid` |

`source_id`와 provenance를 Normalized에도 보존해 같은 external ID의 다른
소스를 구분하고 Raw까지 재추적한다. provenance 항목은 Extracted 계약과 같은
Raw document ID·역할·hash·수집 시각·안전 endpoint 구조를 사용한다.

### 검색 배열과 지역 규칙

`keywords`, `life_stages`, `target_groups`는 `null`이 될 수 없다. 각 원소는
공통 text 정규화를 거친 비어 있지 않은 문자열이며 첫 등장 순서를 유지해
exact 중복을 제거한다. Source에 없는 청년·지역·대상 값을 시스템이 임의로
추가하지 않는다.

`region_rules`의 모든 원소는 다음 6개 key를 가진다.

| 필드 | 타입 | 기준 |
| --- | --- | --- |
| `relation` | enum | `include`, `exclude` |
| `resolution_status` | enum | `matched`, `unmapped`, `ambiguous` |
| `region_scheme` | string 또는 null | matched canonical code scheme |
| `region_code` | string 또는 null | scheme 안의 canonical code |
| `source_code` | string 또는 null | Source가 제공한 원본 code |
| `source_text` | string 또는 null | Source가 제공한 지역 근거 text |

- `matched`는 `region_scheme`·`region_code`가 모두 필요하다.
- `unmapped`·`ambiguous`는 canonical 두 필드가 `null`이고 source code 또는
  text 중 하나 이상의 근거가 필요하다.
- `nationwide`는 명시적 Source 근거가 있을 때만 사용하며 `region_rules=[]`다.
- `regional`은 matched include가 하나 이상 필요하다.
- `unknown`에는 matched rule이 없지만 unresolved Source evidence는 남길 수
  있다.
- 같은 canonical 지역을 중복하거나 include·exclude에 동시에 둘 수 없다.

기존 `regions`는 표시·exact filter 호환용 이름 배열이며 canonical identity가
아니다. 1.0.0 입력은 compatibility adapter가 검색 배열 `[]`,
`coverage_scope=unknown`, `region_rules=[]`를 추가하고, 1.0.0·1.1.0 입력 모두에
빈 unknown `eligibility_summary`를 추가해 1.2.0 객체로 변환한다. 기존
`regions`나 문자열 `전국`, 자격 원문을 generic adapter가 구조화 조건으로
추정하지 않는다.

### 날짜와 시간

- 날짜는 `YYYY-MM-DD` 문자열 또는 null이다.
- 수집 시각은 timezone을 포함한 ISO 8601 date-time 문자열이다.
- 종료일을 알 수 없으면 임의 날짜를 생성하지 않고 null을 사용한다.
- 시작일은 종료일보다 늦을 수 없다.
- `application_status`의 기간 비교 기준일은 `collected_at`을
  Asia/Seoul 날짜로 변환한 값이다.

### enum 기준

category는 실제 복지로의 다중 관심주제를 보존하기 위해 단일 `category`가
아닌 `categories` 배열이다.

```text
housing
finance
welfare
employment
startup
education
other
```

신청 일정 유형:

```text
fixed_period
always
until_budget_exhausted
```

신청 상태:

```text
open
closed
scheduled
```

지역 적용 범위:

```text
nationwide
regional
unknown
```

`always`는 일정 유형이고 `open`은 수집 기준일의 상태이므로 같은 enum에 넣지
않는다. 판단 근거가 없으면 `"unknown"` enum 대신 null을 사용한다.

## null과 빈 배열

| 값 종류 | 누락 표현 | 금지 예 |
| --- | --- | --- |
| 선택 단일 값 | `null` | 빈 문자열, 임의 날짜, 의미 없는 `"unknown"` |
| 복수 값 | `[]` | `null`, 빈 문자열, 단일 string |
| 지역 적용 범위 | 필수 enum `unknown` | `null`, 지역·전국 추정 |
| 필수 값 | invalid 처리 | 누락을 null로 정상 통과 |

원문 표현은 별도 text 필드나 Raw/Extracted 단계에 보존한다. 구조화에
실패했다는 이유로 원문까지 삭제하지 않는다.

## 품질 분류

- `valid`: Schema를 통과하고 category·지역·연령·신청기간 검색 정보가 있음
- `partial`: Schema를 통과하지만 해당 검색 정보가 일부 누락되거나 선택 필드
  파싱 경고가 있음
- `invalid`: 제목·출처·provenance 등 핵심 필드가 없거나 Schema, 날짜·연령
  범위 관계를 위반하거나 선언한 품질 상태가 실제 판정과 다름

invalid 데이터는 정상 Fixture, Seed 또는 PostgreSQL 입력과 분리하고 실패
이유를 기록한다. Validator issue는 JSON path, 코드, 메시지와
`warning`·`error` severity를 가진다. partial은 Schema-valid
`NormalizedProgram`을 유지하지만 invalid는 `program=null`인 rejected
결과로 분리한다.

### Backend·Frontend 저장과 소비 경계

Normalized 1.0.0은 최초 실행 계약, 1.1.0은 검색용 배열과 지역 coverage를
추가한 호환 minor version, 1.2.0은 Source 근거 기반 `eligibility_summary`를
추가한 현재 version이다. 합성 Raw → Extracted → Normalized Fixture와 canonical
Seed로 이 변환을 검증한다.

Backend Policy ORM은 배열·조건·provenance를 PostgreSQL `JSONB`, 수집 시각을
timezone-aware timestamp, 일정·상태·품질을 DB enum으로 저장한다.
`region_rules`는 관계형 지역 모델과 연결하고 검색 projection은 Policy upsert와
같은 transaction에서 동기화한다. SQLite 기반 단위 테스트는 빠른 대체 경계일
뿐 PostgreSQL Migration·constraint 검증을 대신하지 않는다.

Importer는 DB 접근 전에 `NormalizedProgramValidator`로 전체 입력을 검증한다.
valid·partial만 허용하고 invalid·Schema 위반·identity admission 거부·DB write
실패가 있으면 같은 canonical batch 전체를 rollback한다. identity는
`(source_id, external_id)`이며 현재 등록 Source는 비어 있지 않은 external ID를
요구한다. 동일 입력은 `unchanged`로 분류해 `updated_at`을 바꾸지 않는다.

Frontend 공개 `PolicyDto`는 provenance 같은 내부 감사 필드를 노출하지 않는다.
`eligibility_summary`는 상세 DTO에서만 제공하고 목록·검색 DTO에는 포함하지
않는다. Frontend type은 지원되는 1.0.0·1.1.0·1.2.0 응답을 읽을 수 있다.

현재 1.2.0의 37개 필드와 PostgreSQL 컬럼·관계 매핑은
[Policy 데이터베이스 매핑](../architecture/policy_database_mapping.md)을
따른다.

[Fixture와 Seed 계약](fixture_seed_contract.md)은 1.2.0의 Backend 저장 후보,
Frontend 비노출 경계와 현재 승인 상태를 기록한다.

## JSON Schema 동기화 규칙

### Eligibility Summary 1.0.0 nested 계약

정책 상세 자격요건 확장은
[Eligibility Summary 공통 계약](eligibility_summary_contract.md)과
`data/schema/eligibility_summary.schema.json`을 실행 기준으로 사용한다.
`coverage`, 조건·제외·우대·서류·unknown·공개 시설 연락처와 각 항목의 공개
evidence를 별도 객체로 고정하며 배열은 required이고 값이 없으면 `[]`다.

독립 nested Schema로 먼저 검증한 뒤 `NormalizedProgram 1.2.0`의 required
`$defs.eligibilitySummary`로 삽입했다.
Fixture·Seed·ORM·Importer는 37개 exact field parity를 사용한다. 1.0.0·1.1.0
compatibility adapter는 근거 없는 조건을 만들지 않고 unknown 빈 객체만 추가한다.

구현된 계층은 `data/schema/*.schema.json`이 기계 검증의 기준이고 이 문서는
사람을 위한 설명이다. 둘은 같은 변경에서 함께 수정한다.

Schema 변경 PR은 다음을 포함한다.

1. 영향받는 JSON Schema
2. 이 문서와 [정규화 규칙](normalization_rules.md)
3. 유효·경계·실패 사례 테스트
4. Fixture와 Seed
5. Backend 응답 Schema와 Frontend 타입 영향 검토
6. 호환성이 깨지면 `CHANGELOG.md`와 전환 방법

합성 valid·partial·invalid 단위 Fixture와 두 소스 형태의 합성 Raw에서
재생성한 Normalized Fixture·Seed로 계약을 검증한다. 현재 runtime Raw는
소비자 공동 검토나 이용 조건과 관계없이 배포 데이터로 복사하지 않는다.

Raw Schema는 Semantic Versioning 문자열을 사용한다. required·타입·역할
관계처럼 기존 문서를 무효화하는 변경은 major, 기존 문서를 계속 허용하는
추가는 minor, 설명과 제약의 호환 가능한 수정은 patch를 올린다. 저장된
문서의 `schema_version`과 Schema `$id`를 함께 변경한다.

Raw Schema는 Collector 재처리와 provenance를 위한 내부 계약이다.
Normalized Schema는 Backend importer, PostgreSQL, 공개 API와 Frontend 소비의
현재 기준이다. 변경 요청이 생기면 Python 모델, Schema, Fixture, Seed, DB·API와
Frontend 타입을 같은 변경에서 동기화한다.

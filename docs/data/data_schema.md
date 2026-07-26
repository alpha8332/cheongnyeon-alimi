# 데이터 Schema 기준선

## 문서 상태

- 상태: 논리적 기준선
- 현재 구현 상태: Raw Python 모델·JSON Schema·runtime 저장 구현,
  Extracted·Normalized Schema 미구현

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

API와 향후 HTML Collector가 같은 envelope를 사용할 수 있게 하되 소스별
payload를 이 단계에서 억지로 통일하지 않는다. 현재 구현은 온통청년·복지로
API의 JSON·XML Raw만 생성 대상으로 삼는다.

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
| `raw_format` | enum | `json`, `xml`, `html` |
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
현재 external ID는 온통청년 `plcyNo`, 복지로 `servId`다.

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
| `external_id` | string 또는 null |
| `title` | string 또는 null |
| `organization` | string 또는 null |
| `category_text` | string 또는 null |
| `application_period_text` | string 또는 null |
| `region_text` | string 또는 null |
| `age_text` | string 또는 null |
| `eligibility_text` | string 또는 null |
| `support_content` | string 또는 null |
| `application_method` | string 또는 null |
| `source_url` | URI string |
| `extra` | object |

소스별 추가 필드는 `extra`에 보존한다. `ExtractedPolicy`는 XML 태그나 CSS
Selector를 공통 Normalizer로 노출하지 않기 위한 내부 경계다.

## `NormalizedProgram`

### 필수 필드

- `title`
- `source_name`
- `source_url`
- `collected_at`
- `data_quality_status`

필수 필드가 없으면 단순 null로 정상 데이터처럼 통과시키지 않고 Validator가
invalid로 분류한다.

### 선택 단일 필드

계획에서 확인된 선택 필드는 다음과 같다.

- `external_id`
- `organization`
- `summary`
- `category`
- `application_start`
- `application_end`
- `application_status`
- `age_min`
- `age_max`
- `age_condition_text`
- `eligibility_text`
- `support_content`
- `application_method`

값이 없는 선택 단일 필드는 `null`을 사용한다. 빈 문자열, `"unknown"`과
임의의 기본값으로 누락을 숨기지 않는다.

### 배열 필드

다음 필드는 값이 하나이거나 없어도 항상 배열이다.

- `regions`
- `education_statuses`
- `employment_statuses`
- `required_conditions`
- `preferred_conditions`
- `excluded_conditions`

값이 없으면 `[]`을 사용한다. 배열 필드를 `null`이나 단일 string으로
바꾸지 않는다.

### 날짜와 시간

- 날짜는 `YYYY-MM-DD` 문자열 또는 null이다.
- 수집 시각은 timezone을 포함한 ISO 8601 date-time 문자열이다.
- 종료일을 알 수 없으면 임의 날짜를 생성하지 않고 null을 사용한다.

### enum 기준

현재 확정된 category 매핑:

```text
housing
finance
welfare
employment
startup
education
other
```

현재 확정된 품질 상태:

```text
valid
partial
invalid
```

`application_status`는 계획 예시에서 `always`와 `open`이 혼용되어 최종 enum이
확정되지 않았다. JSON Schema 구현 전에 상시 신청과 현재 신청 가능 상태를
하나의 필드로 표현할지 별도 필드로 나눌지 공동 검토한다.

## null과 빈 배열

| 값 종류 | 누락 표현 | 금지 예 |
| --- | --- | --- |
| 선택 단일 값 | `null` | 빈 문자열, 임의 날짜, 의미 없는 `"unknown"` |
| 복수 값 | `[]` | `null`, 빈 문자열, 단일 string |
| 필수 값 | invalid 처리 | 누락을 null로 정상 통과 |

원문 표현은 별도 text 필드나 Raw/Extracted 단계에 보존한다. 구조화에
실패했다는 이유로 원문까지 삭제하지 않는다.

## 품질 분류

- `valid`: 필수 필드와 주요 검색 필드가 정상
- `partial`: 필수 필드는 있으나 날짜, 지역, 연령 등 일부 값이 누락
- `invalid`: 제목이나 출처 URL 등 핵심 필드가 없거나 Schema를 위반

invalid 데이터는 정상 Fixture, Seed 또는 PostgreSQL 입력과 분리하고 실패
이유를 기록한다.

## JSON Schema 동기화 규칙

구현된 계층은 `data/schema/*.schema.json`이 기계 검증의 기준이고 이 문서는
사람을 위한 설명이다. 둘은 같은 변경에서 함께 수정한다.

Schema 변경 PR은 다음을 포함한다.

1. 영향받는 JSON Schema
2. 이 문서와 [정규화 규칙](normalization_rules.md)
3. 유효·경계·실패 사례 테스트
4. Fixture와 Seed
5. Backend 응답 Schema와 Frontend 타입 영향 검토
6. 호환성이 깨지면 `CHANGELOG.md`와 전환 방법

Raw Schema는 Semantic Versioning 문자열을 사용한다. required·타입·역할
관계처럼 기존 문서를 무효화하는 변경은 major, 기존 문서를 계속 허용하는
추가는 minor, 설명과 제약의 호환 가능한 수정은 patch를 올린다. 저장된
문서의 `schema_version`과 Schema `$id`를 함께 변경한다.

Raw Schema는 Collector 재처리와 provenance를 위한 내부 계약이다. 이번
`1.0.0` 확정은 `NormalizedProgram`, Backend API 응답과 Frontend 타입을
변경하지 않는다. 향후 Backend가 Raw를 직접 적재하거나 Frontend 관리자
화면에 노출하면 해당 소비자 계약을 공동 검토한다.

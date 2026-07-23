# 데이터 Schema 기준선

## 문서 상태

- 상태: 논리적 기준선
- 현재 구현 상태: JSON Schema 미구현

이 문서는 `RawPolicyDocument`, `ExtractedPolicy`와
`NormalizedProgram`의 역할과 필드 원칙을 정의한다. 실행 가능한 최종 계약은
향후 `data/schema/*.schema.json`으로 구현하고 이 문서와 함께 관리한다.

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

API와 HTML을 같은 envelope로 저장한다. 소스별 payload를 이 단계에서 억지로
통일하지 않는다.

| 필드 | 논리 타입 | 기준 |
| --- | --- | --- |
| `source_id` | string | 소스의 안정적인 식별자 |
| `source_type` | string | API 또는 Web 유형 |
| `external_id` | string 또는 null | 소스가 제공하거나 규칙으로 만든 외부 식별자 |
| `source_url` | URI string | 원문 또는 원문을 확인할 수 있는 출처 URL |
| `collected_at` | date-time string | timezone을 포함한 수집 시각 |
| `content_type` | string | 응답의 media type |
| `raw_format` | string | `json`, `xml`, `html` 등 원문 형식 |
| `raw_payload` | object, array 또는 string | 손실 없이 보존한 원문 |
| `content_hash` | string | 원문 내용으로 계산한 SHA-256 |
| `http_status` | integer | 문서를 생성한 응답의 HTTP 상태 |
| `collector_version` | string | 수집 로직 버전 |

### 필수 원칙

- `source_url`과 `collected_at`은 반드시 존재한다.
- 원문 형식을 보존할 수 있도록 `raw_payload` 타입을 제한하지 않는다.
- `external_id`가 없으면 null을 허용하되 다음 우선순위로 안정적인 ID를
  검토한다.
  1. 사이트가 제공하는 게시물 ID
  2. 상세 URL의 식별자
  3. `source_id`와 정규화된 `source_url` 기반 Hash
- `content_hash`는 원문 변경과 동일 내용 재수집을 확인하기 위한 기반이다.
- 요청 자체가 실패해 Raw 문서를 만들 수 없는 경우는 수집 실행 실패 기록으로
  분리한다.

필드별 최종 required 목록, pattern과 허용 enum은 Raw JSON Schema 구현
Slice에서 샘플 응답과 함께 확정한다.

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

JSON Schema가 구현된 뒤에는 `data/schema/*.schema.json`이 기계 검증의
기준이고 이 문서는 사람을 위한 설명이다. 둘은 같은 변경에서 함께
수정한다.

Schema 변경 PR은 다음을 포함한다.

1. 영향받는 JSON Schema
2. 이 문서와 [정규화 규칙](normalization_rules.md)
3. 유효·경계·실패 사례 테스트
4. Fixture와 Seed
5. Backend 응답 Schema와 Frontend 타입 영향 검토
6. 호환성이 깨지면 `CHANGELOG.md`와 전환 방법

Schema 버전 관리 방식과 호환성 정책은 실제 첫 Schema 구현 시 확정한다.

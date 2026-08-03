# Policy 데이터베이스 매핑

## 문서 상태

- 상태: 현재 구현 기준
- 입력 계약: `NormalizedProgram` 1.0.0 또는 기본 검색값만 가진 1.1.0
- 저장 모델: Backend `Policy`
- Migration: `20260728_0001`

이 문서는 Data의 canonical JSON, Backend importer, PostgreSQL `policies`
테이블과 공개 Policy API 사이의 현재 필드 매핑을 정의한다. 논리 필드의 의미와
검증 규칙은 [데이터 Schema 기준선](../data/data_schema.md), 공개 응답은
[Policy API 계약](../api/policies.md)이 권위 있다.

## 매핑 원칙

- 현재 저장되는 기존 Normalized 31개 필드는 이름을 바꾸지 않고 같은 이름의
  DB 컬럼에 저장한다.
- 선택 단일 값은 nullable 컬럼에 `NULL`, 복수 값은 non-null JSONB에 JSON
  배열로 저장한다.
- 날짜는 PostgreSQL `date`, 수집 시각은 timezone-aware `timestamptz`로
  변환한다.
- 원문 text와 구조화 필드는 서로 대체하지 않고 모두 보존한다.
- `provenance`는 DB에는 보존하지만 일반 사용자 Policy API에는 노출하지
  않는다.
- 저장 계층이 생성하는 `id`, `created_at`, `updated_at`은 Normalized 입력
  계약에는 없고 공개 Policy DTO에 추가된다.

## 31개 필드 매핑

`직접`은 JSON 값과 DB 조회 값이 같은 의미와 값을 유지한다는 뜻이다. 날짜와
시각만 Python·PostgreSQL 타입으로 변환한 뒤 아래 비교 기준을 적용한다.

| Normalized 필드 | JSON 타입 | PostgreSQL 컬럼 타입 | DB null | Importer 변환 | 공개 API |
| --- | --- | --- | --- | --- | --- |
| `schema_version` | string `1.0.0` 또는 `1.1.0` | `varchar(32)` | 아니요 | 직접 | 노출 |
| `source_id` | string | `text` | 아니요 | 비어 있지 않은 string | 노출 |
| `source_name` | string | `varchar(255)` | 아니요 | 직접 | 노출 |
| `external_id` | string 또는 null | `varchar(512)` | 예 | 현재 admission 후 string | 노출 |
| `title` | string | `varchar(1000)` | 아니요 | 직접 | 노출 |
| `organization` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `summary` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `category_text` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `categories` | category string 배열 | `jsonb` | 아니요 | 배열 그대로 | 노출 |
| `application_period_text` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `application_start` | date string 또는 null | `date` | 예 | Python `date` | ISO date 노출 |
| `application_end` | date string 또는 null | `date` | 예 | Python `date` | ISO date 노출 |
| `application_schedule` | enum 또는 null | `policy_application_schedule` | 예 | 직접 | 노출 |
| `application_status` | enum 또는 null | `policy_application_status` | 예 | 직접 | 노출 |
| `region_text` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `regions` | string 배열 | `jsonb` | 아니요 | 배열 그대로 | 노출 |
| `age_min` | integer 또는 null | `integer` | 예 | 직접 | 노출 |
| `age_max` | integer 또는 null | `integer` | 예 | 직접 | 노출 |
| `age_condition_text` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `eligibility_text` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `support_content` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `application_method` | string 또는 null | `text` | 예 | 직접 | 노출 |
| `education_statuses` | string 배열 | `jsonb` | 아니요 | 배열 그대로 | 노출 |
| `employment_statuses` | string 배열 | `jsonb` | 아니요 | 배열 그대로 | 노출 |
| `required_conditions` | string 배열 | `jsonb` | 아니요 | 배열 그대로 | 노출 |
| `preferred_conditions` | string 배열 | `jsonb` | 아니요 | 배열 그대로 | 노출 |
| `excluded_conditions` | string 배열 | `jsonb` | 아니요 | 배열 그대로 | 노출 |
| `source_url` | URI string | `text` | 아니요 | 직접 | 노출 |
| `collected_at` | timezone date-time string | `timestamptz` | 아니요 | aware `datetime` | aware date-time 노출 |
| `provenance` | object 배열 | `jsonb` | 아니요 | 배열 그대로 | 비노출 |
| `data_quality_status` | quality enum | `policy_data_quality_status` | 아니요 | 직접 | valid·partial만 노출 |

### JSONB 배열

다음 8개 필드는 PostgreSQL JSONB에 원소 순서와 값을 그대로 저장한다.

```text
categories
regions
education_statuses
employment_statuses
required_conditions
preferred_conditions
excluded_conditions
provenance
```

`category_text`·`categories`와 `region_text`·`regions`는 원문과 정규화 결과를
동시에 보존한다. 배열이 비어 있으면 `[]`이며 `NULL`, 빈 문자열 또는 단일
string으로 바꾸지 않는다. `categories`와 `regions`에는 GIN index가 있고
Repository는 배열 원소의 exact membership으로 검색한다.

### 일정·상태와 기간

- `application_period_text`는 원문 기간 표현을 보존한다.
- `application_start`와 `application_end`는 검색 가능한 날짜다.
- `application_schedule`은 신청 방식, `application_status`는 수집 시점의
  상태이므로 서로 대체하지 않는다.
- 날짜가 없으면 `NULL`이며 원문 text가 있더라도 임의 날짜를 만들지 않는다.

### provenance와 공개 API

`provenance`는 Raw 문서 ID·역할·hash·수집 시각·안전한 source URL의 object
배열로 DB에 보존한다. 일반 사용자 `PolicyRead`에는 포함하지 않는다. 나머지
Normalized 30개 필드는 공개 DTO에 있고 저장 계층이 생성한 다음 필드가
추가된다.

| 저장 계층 생성 필드 | PostgreSQL 타입 | 현재 생성 경계 | 공개 API |
| --- | --- | --- | --- |
| `id` | auto-increment integer | DB identity | 노출 |
| `created_at` | `timestamptz` | Importer write instant, ORM·DB default fallback | 노출 |
| `updated_at` | `timestamptz` | Importer write instant, ORM·DB default fallback | 노출 |

Importer는 최초 insert에 하나의 UTC aware write instant를 생성해 두 필드에
같이 전달한다. ORM과 Migration의 `ck_policies_timestamp_order`는
`updated_at >= created_at`을 강제한다. Migration은 이 constraint를 추가하기
전에 기존 역전 행의 `updated_at`을 `created_at`으로 보정한다. Importer 밖의
insert에서는 ORM Python default와 DB `CURRENT_TIMESTAMP` server default가
방어적 fallback이며, Policy를 변경하는 writer는 `updated_at`을 명시해야
한다. 상세 결정과 검증은
[Backend Policy Runtime Safety 계획](../development/develop_plan/backend/03_policy_runtime_safety.md)과
[개발 기록](../development/development_notes/backend/policy_runtime_safety.md)에
기록한다.

invalid는 DB enum에는 존재하지만 importer admission에서 거부되므로 정상
Policy API에 도달하지 않는다. partial은 저장하며
`include_partial=true`일 때만 공개한다.

## Normalized 1.1.0 전환 경계

PSF1에서 논리 Schema는 기존 31개 필드에 `keywords`, `life_stages`,
`target_groups`, `coverage_scope`, `region_rules`를 더한 36개 필드가 됐다.
현재 Migration `20260728_0001`과 Policy ORM은 기존 31개만 저장한다.

- 세 검색 배열이 `[]`, coverage가 `unknown`, rules가 `[]`인 1.1.0 입력은
  기존 저장 계약으로 호환된다.
- 이 기본값 중 하나라도 의미 있는 값이면 importer가
  `search_storage_not_ready`로 거부한다.
- 따라서 PSF3 전에는 새 검색 값을 조용히 버린 채 적재하지 않는다.
- 1.0.0 입력은 Normalized compatibility adapter에서만 1.1.0 안전 기본값으로
  확장하며 지역·전국 여부를 추정하지 않는다.
- 새 5개 필드의 PostgreSQL 컬럼·관계 저장과 전체 36개 왕복 검증은 PSF3
  Migration에서 이 문서를 갱신한 뒤 활성화한다.

PSF2의 파일 기준정보는 `kr-bjd-20260803` scheme과 10자리 code를 identity로
사용한다. PostgreSQL에는 아직 적재하지 않았으며 PSF3의
`administrative_regions`는 공식 `parent_code`와 별도로 nullable
`aggregate_parent_code`를 저장해야 한다. 비자치구의 원천 parent를 집계 시로
덮어쓰지 않으며 alias 다중 후보, active·retired와 유효기간을 보존한다.
구체적인 생성·해석 계약은
[행정구역 기준정보](../data/administrative_regions.md)를 따른다.

## 식별자와 upsert

- DB identity는 `(source_id, external_id)` unique constraint다.
- 현재 `youthcenter-api`와 `bokjiro-central-welfare-api`는 비어 있지 않은
  `external_id`가 필수다.
- 두 Source의 null ID는 `missing_external_id`, 그 밖의 아직 합의되지 않은
  Source의 null ID는 `unsupported_null_external_id`로 적재하지 않는다.
- DB 컬럼과 논리 Schema의 nullable은 향후 Source 계약 확장 경계를 보존하기
  위한 것이며 현재 importer가 null identity를 허용한다는 뜻이 아니다.
- 같은 identity의 같은 값은 `unchanged`이고 `updated_at`을 바꾸지 않는다.
- 같은 identity의 변경 값은 identity를 제외한 Normalized 필드를 원자적으로
  update한다. `updated_at`은 기존 시각과 새 write instant 중 늦은 값이므로
  시스템 시각이 역행해도 감소하지 않는다.
- 향후 Source의 대체 ID 생성 규칙은 이 매핑에서 일반화하지 않는다.

## Seed와 DB 조회 비교 기준

canonical Seed와 DB 조회 결과는 `(source_id, external_id)`로 짝지어 다음처럼
비교한다.

1. Seed 객체와 `NormalizedProgram.FIELD_NAMES`는 36개로 같고, PSF3 전
   importer write key와 ORM의 system field 제외 컬럼 집합은 검색 5개 필드를
   제외한 기존 31개로 같다.
2. string, integer, enum, null과 JSONB 배열·object는 값과 배열 순서를 exact
   equality로 비교한다.
3. `application_start`·`application_end`는 DB `date.isoformat()`과 Seed의
   `YYYY-MM-DD`를 비교한다.
4. `collected_at`은 문자열 offset이 아니라 UTC absolute instant를 비교한다.
5. 빈 배열은 DB에서도 `[]`, null은 DB에서도 `NULL`이어야 한다.
6. 다중 category와 provenance object의 누락·병합·축약이 없어야 한다.
7. 기존 공개 API 필드 집합은 기존 저장 31개에서 `provenance`만 제외하고
   `id`·`created_at`·`updated_at`을 더한 집합이다. 검색 5개 필드는 기존
   목록·상세 DTO에 노출하지 않는다.

구조적 집합과 변환은
`backend/tests/test_policy_mapping_contract.py`, 실제 PostgreSQL 왕복은
`backend/tests/test_postgresql_end_to_end.py`가 검증한다. Integration 소유의
canonical Seed 전체 흐름과 거부·재실행·rollback·Repository 조회는
`tests/integration/test_seed_to_database.py`가 검증한다.

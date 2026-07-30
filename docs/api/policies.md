# Policy API 계약

## 계약 정보

- Base path: `/api/v1/policies`
- 인증: 현재 없음
- 응답 형식: JSON
- 정렬: `id` 오름차순
- 데이터 기준: `NormalizedProgram` 1.0.0

일반 사용자 Policy API는 Raw provenance를 반환하지 않는다. 목록과 상세는
기본적으로 `valid` 정책만 노출하며 `include_partial=true`일 때
`valid`·`partial`을 함께 허용한다. `invalid` 정책은 어떤 경우에도 공개하지
않는다.

## 정책 목록

```http
GET /api/v1/policies
```

### Query

| 이름 | 타입 | 기본값 | 규칙 |
| --- | --- | --- | --- |
| `page` | integer | `1` | 1 이상 |
| `limit` | integer | `10` | 1~100 |
| `category` | enum | 없음 | `categories`의 정확한 원소 |
| `region` | string | 없음 | `regions`의 정확한 원소, 1~100자 |
| `status` | enum | 없음 | `open`, `closed`, `scheduled` |
| `include_partial` | boolean | `false` | `true`면 partial 포함 |

`category`는 `housing`, `finance`, `welfare`, `employment`, `startup`,
`education`, `other` 중 하나다. category와 region은 배열 원소의 완전 일치
필터다. 예를 들어 `finance`는 일치하지만 `fin`은 일치하지 않고,
`서울특별시`는 일치하지만 `서울`은 일치하지 않는다. 원문
`category_text`·`region_text`의 부분 문자열 검색은 이 endpoint의 기본 필터가
아니다.

### 응답

```json
{
  "total": 2,
  "page": 1,
  "limit": 10,
  "items": [
    {
      "schema_version": "1.0.0",
      "source_id": "youthcenter-api",
      "source_name": "온통청년 청년정책 API",
      "external_id": "SYN-YOUTH-001",
      "title": "합성 청년 주거 지원",
      "organization": "합성 주거기관",
      "summary": null,
      "category_text": "주거",
      "categories": ["housing"],
      "application_period_text": "2026. 1. 1. ~ 2026. 6. 30.",
      "application_start": "2026-01-01",
      "application_end": "2026-06-30",
      "application_schedule": "fixed_period",
      "application_status": "closed",
      "region_text": "서울시",
      "regions": ["서울특별시"],
      "age_min": 19,
      "age_max": 34,
      "age_condition_text": "19세 ~ 34세",
      "eligibility_text": "합성 청년 대상",
      "support_content": "합성 월 지원",
      "application_method": "온라인 신청",
      "education_statuses": [],
      "employment_statuses": [],
      "required_conditions": [],
      "preferred_conditions": [],
      "excluded_conditions": [],
      "source_url": "https://fixture.invalid/youth/001",
      "collected_at": "2026-07-26T06:00:00Z",
      "data_quality_status": "valid",
      "id": 1,
      "created_at": "2026-07-29T00:00:00Z",
      "updated_at": "2026-07-29T00:00:00Z"
    }
  ]
}
```

`total`은 pagination 적용 전 필터 결과 수다. 요청 page가 결과 범위를
벗어나면 `total`은 유지되고 `items`는 빈 배열이다.

`collected_at`, `created_at`, `updated_at`은 timezone-aware date-time이다.
PostgreSQL Session timezone에 따라 같은 절대 시각이 `+00:00` 또는 `+09:00`
등 다른 offset으로 표현될 수 있으므로 소비자는 offset 문자열이 아니라
절대 시각으로 해석한다.

## 정책 상세

```http
GET /api/v1/policies/{policy_id}
```

| 이름 | 위치 | 타입 | 기본값 | 규칙 |
| --- | --- | --- | --- | --- |
| `policy_id` | path | integer | 없음 | 조회할 DB ID |
| `include_partial` | query | boolean | `false` | partial 상세 허용 |

응답 DTO는 목록의 `items` 원소와 같다. partial 정책 ID를 기본 요청으로
조회하면 404이며, `include_partial=true`일 때만 조회할 수 있다.

## 오류

| 상태 | 조건 | 응답 기준 |
| --- | --- | --- |
| `404` | ID가 없거나 요청 품질 범위에서 숨겨짐 | `{"detail":"Policy not found"}` |
| `422` | page·limit 범위, category·status enum 또는 query 타입 위반 | FastAPI validation 오류 |
| `500` | 처리되지 않은 서버 오류 | 내부 상세를 제외한 공통 오류 응답 |

404는 실제 ID 부재와 품질 정책에 따른 비노출을 구분하지 않는다.

## 저장·검색 경계

- Normalized 31개 필드의 DB 저장과 공개 DTO 노출 관계는
  [Policy 데이터베이스 매핑](../architecture/policy_database_mapping.md)을
  따른다.
- PostgreSQL category·region 필터는 JSONB `@>` 연산자를 사용해 배열 원소를
  정확히 검색하고 기존 GIN index와 호환된다.
- SQLite는 운영 대체 DB가 아니라 단위 테스트 경계이며 `json_each`로 같은
  원소 일치 의미를 검증한다.
- 자유 키워드, 원문 부분 문자열, 정렬 선택과 추천은 이 계약 범위가 아니다.
- `provenance`는 DB에 보존하지만 목록·상세 공개 DTO에서 제외한다.

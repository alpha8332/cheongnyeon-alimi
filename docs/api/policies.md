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
422는 query뿐 아니라 `policy_id` path 타입 위반에도 같은 FastAPI validation
오류 형식을 사용하며 최상위 `detail`은 오류 object의 배열이다.

처리되지 않은 서버 오류의 공개 응답은 다음과 같다. 예외 메시지, DB 정보와
내부 stack trace는 응답에 포함하지 않는다.

```json
{
  "error": {
    "message": "Internal Server Error",
    "details": {}
  }
}
```

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

## Frontend D6 인계

### TypeScript 기준

Frontend의 사용자 정책 화면은 canonical Seed의 `NormalizedProgram`이 아니라
아래 공개 API DTO를 기준으로 타입을 정의한다. 모든 key는 응답에 존재하며
선택 단일 값만 `null`일 수 있다. 배열은 값이 없어도 `[]`다.

```typescript
export type PolicyCategory =
  | 'housing'
  | 'finance'
  | 'welfare'
  | 'employment'
  | 'startup'
  | 'education'
  | 'other';

export type ApplicationSchedule =
  | 'fixed_period'
  | 'always'
  | 'until_budget_exhausted';

export type ApplicationStatus = 'open' | 'closed' | 'scheduled';
export type PublicDataQualityStatus = 'valid' | 'partial';

export interface PolicyDto {
  schema_version: '1.0.0';
  source_id: string;
  source_name: string;
  external_id: string | null;
  title: string;
  organization: string | null;
  summary: string | null;
  category_text: string | null;
  categories: PolicyCategory[];
  application_period_text: string | null;
  application_start: string | null;
  application_end: string | null;
  application_schedule: ApplicationSchedule | null;
  application_status: ApplicationStatus | null;
  region_text: string | null;
  regions: string[];
  age_min: number | null;
  age_max: number | null;
  age_condition_text: string | null;
  eligibility_text: string | null;
  support_content: string | null;
  application_method: string | null;
  education_statuses: string[];
  employment_statuses: string[];
  required_conditions: string[];
  preferred_conditions: string[];
  excluded_conditions: string[];
  source_url: string;
  collected_at: string;
  data_quality_status: PublicDataQualityStatus;
  id: number;
  created_at: string;
  updated_at: string;
}

export interface PolicyListResponse {
  total: number;
  page: number;
  limit: number;
  items: PolicyDto[];
}
```

`PolicyDto`에는 `provenance`와 `invalid` 품질 상태가 없다. 상세 route와
React key는 nullable `external_id`나 source 조합이 아니라 API가 반환한 숫자
`id`를 사용한다.

### API Client 전환 기준

```typescript
const list = await apiClient.get<PolicyListResponse>(
  '/api/v1/policies',
  {
    params: {
      page: 1,
      limit: 10,
      include_partial: false,
    },
  },
);

const detail = await apiClient.get<PolicyDto>(
  `/api/v1/policies/${policyId}`,
  {
    params: {
      include_partial: false,
    },
  },
);
```

- 목록 응답은 배열이 아니라 `total`, `page`, `limit`, `items` envelope다.
- 상세 endpoint는 `/api/v1/policies/{policy_id}`이며 `policy_id`는 DB 숫자
  ID다.
- `/api/v1/programs`와 source/external ID 조합 상세 endpoint는 구현돼 있지
  않다.
- `include_partial`의 기본값은 `false`다. partial 화면을 제공할 때 목록과
  상세 요청에 같은 값을 전달한다.
- 현재 API에는 자유 키워드·연령 query가 없다. Mock 전용 로컬 검색을 실제
  API 필터처럼 간주하지 않는다.

### Mock → API 전환

canonical Seed 4건을 Mock 사례로 사용할 수 있지만 다음 변환이 필요하다.

1. 일반 사용자 DTO에 없는 `provenance`를 제거한다.
2. 각 객체에 안정적인 양의 `id`와 timezone-aware `created_at`,
   `updated_at`을 추가한다.
3. 기본 목록은 `data_quality_status === "valid"`인 2건만 반환한다.
4. `include_partial=true`에서만 valid·partial 4건을 반환한다.
5. 목록은 `PolicyListResponse` envelope로 감싼다.
6. 상세는 숫자 `id`로 찾고 partial 기본 요청은 404와 같은 비노출 상태로
   처리한다.

Frontend 소비 테스트는 최소한 다음 상태를 확인한다.

- loading, 빈 `items`, 404, 422와 500
- nullable 값의 명시적인 fallback과 빈 배열 렌더링
- `application_schedule`과 `application_status`의 구분
- partial 표시와 목록·상세 opt-in 일관성
- timezone offset 문자열이 달라도 같은 instant로 해석
- 공개 응답과 화면 상태에 provenance가 포함되지 않음

### 현재 Frontend branch 검토 결과

2026-07-30 `feature/frontend/policy-discovery`의 FE 2A는 공개 `PolicyDto`,
`/api/v1/policies`, pagination envelope, 숫자 `id`와 partial opt-in을
타입·Mock·API Client·화면에 반영했다.

- 사용자 DTO에서 `provenance`와 `invalid` 제거
- canonical Seed를 공개 DTO로 변환하면서 양의 `id`와 DB 시각 추가
- 기본 valid 2건, `include_partial=true`에서 valid·partial 4건 반환
- 목록·상세가 같은 partial opt-in을 사용하도록 상세 링크 query 유지
- TypeScript 컴파일러와 Node 내장 테스트 러너 기반 소비 계약 테스트 추가

현재 PC에는 Node·npm이 없어 추가한 테스트·lint·build는 아직 실행하지
못했다. 실행 증거가 생길 때까지 D0·D6 Frontend 상태는
`review-pending`으로 유지한다.

## 통합 검증

`tests/integration/test_seed_to_policy_api.py`는 canonical Seed 4건을 실제
PostgreSQL에 적재하고 목록·상세 API를 호출해 다음 계약을 검증한다.

- 기본 valid 2건과 `include_partial=true`의 4건
- pagination과 category·region·status의 exact filter
- 공개 30개 Normalized 필드의 Seed 값 보존과 provenance 비노출
- partial 상세 opt-in, 404, query·path 422와 내부 상세가 없는 500 응답

테스트는 저장소의 합성 Seed와 로컬 테스트 DB만 사용하며 외부 API를 호출하지
않는다.
